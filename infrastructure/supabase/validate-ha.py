#!/usr/bin/env python3
"""Controlled scoped HA drills. No node drain/shutdown, force deletion or PVC changes."""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
import uuid

import psycopg

p=argparse.ArgumentParser()
p.add_argument('operation',choices=['storage-restart','switchover'])
p.add_argument('--execute',action='store_true')
p.add_argument('--allow-active-logical-slots',action='store_true',
    help='Explicitly acknowledge the known Realtime graceful-shutdown blocker')
args=p.parse_args()
if not args.execute: p.error('An explicitly authorized controlled drill requires --execute')
# Serialize drills so a DB interruption cannot contaminate a Storage measurement.
lock_dir=Path.home()/'.local/state/homelab'
lock_dir.mkdir(parents=True,exist_ok=True)
lock=(lock_dir/'supabase-ha-drill.lock').open('a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('Another Supabase recovery drill is running; do not overlap tests')
root=Path(__file__).resolve().parents[2]
K=['kubectl','--context','k8s','-n','supabase-prod']
def kubectl(*args):
    return subprocess.check_output(K+list(args),text=True).strip()
def obj(*args):return json.loads(kubectl(*args,'-o','json'))
cluster=obj('get','cluster','supabase-db')
assert cluster['status'].get('readyInstances')==3, 'All3 database instances must be ready'
assert cluster['spec']['postgresql']['synchronous'].get('failoverQuorum') is True
for deployment in obj('get','deployments')['items']:
    assert deployment.get('status',{}).get('readyReplicas',0)==deployment['spec'].get('replicas',1), 'Restore all service replicas before a drill'
item=json.loads(subprocess.check_output([str(root/'scripts/op-sa'),'item','get','Supabase','--vault','HomeLab','--format','json']))
values=json.loads(next(f['value'] for f in item['fields'] if f.get('label')=='deployment-secrets'))
def connect():
    return psycopg.connect(host='sb.l3b.cc.cd',port=5432,dbname='postgres',
        user='postgres.homelab-production',password=values['password'],sslmode='verify-full',
        sslrootcert='/etc/ssl/certs/ca-certificates.crt',connect_timeout=3,
        options='-c statement_timeout=3000',autocommit=True)
def api(path):
    request=urllib.request.Request('https://sb.l3b.cc.cd'+path,headers={'apikey':values['secretKey']})
    with urllib.request.urlopen(request,timeout=3) as response:return response.read()

if args.operation=='storage-restart':
    # Fixtures must have been explicitly created by validate.py --keep.
    assert (Path.home()/'.local/state/homelab/supabase-prod-acceptance.json').exists()
    expected=b'Supabase persistent acceptance fixture\n'
    path='/storage/v1/object/acceptance-private/fixture.txt'
    assert api(path)==expected
    pods=obj('get','pods','-l','app.kubernetes.io/name=supabase-storage')['items']
    assert len(pods)==1 and pods[0]['status']['phase']=='Running'
    old=pods[0]['metadata']['name']
    start=time.monotonic()
    kubectl('delete','pod',old,'--wait=false')
    errors=0;first_error=None;last_error=None;rest_errors=0
    deadline=start+240
    while time.monotonic()<deadline:
        try:
            assert api(path)==expected
            healthy=True
        except (urllib.error.URLError,TimeoutError):
            errors+=1;first_error=first_error or time.monotonic();last_error=time.monotonic();healthy=False
        try:api('/rest/v1/homelab_acceptance?select=id')
        except (urllib.error.URLError,TimeoutError):rest_errors+=1
        new_pods=obj('get','pods','-l','app.kubernetes.io/name=supabase-storage')['items']
        ready=[pod for pod in new_pods if pod['metadata']['name']!=old and
            any(c['type']=='Ready' and c['status']=='True' for c in pod['status'].get('conditions',[]))]
        if ready and healthy:break
        time.sleep(1)
    else:raise SystemExit('Storage did not recover; fixtures preserved for investigation')
    print(json.dumps({'operation':'storage-pod-restart','old':old,'new':ready[0]['metadata']['name'],
        'old_node':pods[0]['spec']['nodeName'],'new_node':ready[0]['spec']['nodeName'],
        'recovery_seconds':round(time.monotonic()-start,2),'failed_storage_probes':errors,
        'observed_failure_span_seconds':round(last_error-first_error,2) if first_error else 0,
        'failed_rest_probes':rest_errors,'file_sha256_preserved':hashlib.sha256(api(path)).hexdigest()},indent=2))
else:
    old=cluster['status']['currentPrimary']
    target=next(n for n in cluster['status']['instancesStatus']['healthy'] if n!=old)
    marker=str(uuid.uuid4())
    table='ha_probe_'+uuid.uuid4().hex[:12]
    with connect() as conn:
        replicas=conn.execute("SELECT count(*) FROM pg_stat_replication WHERE state='streaming' AND sync_state='quorum'").fetchone()[0]
        assert replicas==2
        logical=conn.execute("SELECT count(*) FROM pg_replication_slots WHERE slot_type='logical' AND active").fetchone()[0]
        assert logical==0 or args.allow_active_logical_slots, 'Active logical consumers can block graceful shutdown; resolve or explicitly acknowledge before another drill'
        conn.execute('CREATE TABLE homelab_bootstrap.'+table+'(marker uuid PRIMARY KEY)')
        conn.execute('INSERT INTO homelab_bootstrap.'+table+' VALUES(%s)',(marker,))
    start=time.monotonic()
    # Same status operation as the upstream v1.30.1 cnpg promote plugin.
    latest=obj('get','cluster','supabase-db')
    assert latest['status']['currentPrimary']==old and latest['status'].get('readyInstances')==3
    patch={'metadata':{'resourceVersion':latest['metadata']['resourceVersion']},'status':{
        'targetPrimary':target,'targetPrimaryTimestamp':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'phase':'Switchover in progress','phaseReason':'Controlled homelab HA validation'}}
    kubectl('patch','cluster','supabase-db','--subresource=status','--type=merge','-p',json.dumps(patch))
    errors=0;last_error=None;first_error=None;deadline=start+300
    while time.monotonic()<deadline:
        current=obj('get','cluster','supabase-db')['status']['currentPrimary']
        try:
            with connect() as conn:
                assert conn.execute('SELECT count(*) FROM homelab_bootstrap.'+table+' WHERE marker=%s',(marker,)).fetchone()[0]==1
                is_primary=conn.execute('SELECT NOT pg_is_in_recovery()').fetchone()[0]
            if current==target and is_primary:break
        except psycopg.Error:
            errors+=1;first_error=first_error or time.monotonic();last_error=time.monotonic()
        time.sleep(1)
    else:raise SystemExit('Switchover did not recover; acknowledged marker preserved for investigation')
    with connect() as conn:conn.execute('DROP TABLE homelab_bootstrap.'+table)
    print(json.dumps({'operation':'planned-primary-switchover','old':old,'new':current,
        'recovery_seconds':round(time.monotonic()-start,2),'failed_sql_probes':errors,
        'observed_failure_span_seconds':round(last_error-first_error,2) if first_error else 0,
        'acknowledged_marker_retained':True,'fixture_removed':True},indent=2))
