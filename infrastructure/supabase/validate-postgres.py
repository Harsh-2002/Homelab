#!/usr/bin/env python3
"""Validate TLS PostgreSQL access and optionally fail over the new database only."""
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid
import psycopg

root=Path(__file__).resolve().parents[2]
item=json.loads(subprocess.check_output([str(root/'scripts/op-sa'),'item','get','Supabase','--vault','HomeLab','--format','json']))
values=json.loads(next(f['value'] for f in item['fields'] if f.get('label')=='deployment-secrets'))
def connection():
    return psycopg.connect(host='sb.l3b.cc.cd',port=5432,dbname='postgres',user='postgres.homelab-production',password=values['password'],sslmode='verify-full',sslrootcert='/etc/ssl/certs/ca-certificates.crt',connect_timeout=8,autocommit=True)
def kubectl(*args):
    return subprocess.check_output(['kubectl','--context','k8s','-n','supabase-prod',*args],text=True).strip()
with connection() as conn:
    assert conn.pgconn.ssl_in_use
    assert conn.execute('SELECT NOT pg_is_in_recovery()').fetchone()[0]
    conn.execute('CREATE TEMPORARY TABLE homelab_sql_probe(value integer)')
    conn.execute('INSERT INTO homelab_sql_probe VALUES (1)')
    assert conn.execute('SELECT value FROM homelab_sql_probe').fetchone()[0]==1
print('PASS: sb.l3b.cc.cd:5432 verified TLS, Supavisor authentication and real SQL writes')
if '--failover' in sys.argv:
    old=kubectl('get','cluster','supabase-db','-o','jsonpath={.status.currentPrimary}')
    marker=str(uuid.uuid4())
    with connection() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS homelab_bootstrap.ha_probe(marker uuid PRIMARY KEY)')
        conn.execute('INSERT INTO homelab_bootstrap.ha_probe VALUES (%s)',(marker,))
    start=time.monotonic()
    kubectl('delete','pod',old,'--wait=false')
    print('Testing normal primary-pod deletion:',old,flush=True)
    deadline=start+300
    while time.monotonic()<deadline:
        new=kubectl('get','cluster','supabase-db','-o','jsonpath={.status.currentPrimary}')
        try:
            if new!=old:
                with connection() as conn:
                    assert conn.execute('SELECT count(*) FROM homelab_bootstrap.ha_probe WHERE marker=%s',(marker,)).fetchone()[0]==1
                    conn.execute('DROP TABLE homelab_bootstrap.ha_probe')
                break
        except psycopg.Error:
            pass
        time.sleep(3)
    else:raise SystemExit('FAIL: failover did not recover verified SQL within 300 seconds')
    print(f'PASS: primary changed {old} -> {new}; acknowledged marker retained; SQL recovered after {time.monotonic()-start:.1f}s')
    print('Scope: primary pod termination, not a complete node/network-partition fencing drill')
