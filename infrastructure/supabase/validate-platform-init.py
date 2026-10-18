#!/usr/bin/env python3
"""Verify official init contract and real async webhook delivery; remove own fixtures."""
import json
import subprocess
import time
import uuid

K = ['kubectl', '--context', 'k8s', '-n', 'supabase-prod']
primary = subprocess.check_output(K+['get','cluster','supabase-db','-o','jsonpath={.status.currentPrimary}'], text=True)

def sql(query):
    result = subprocess.run(K+['exec','-i',primary,'-c','postgres','--','psql',
        '-U','postgres','-d','postgres','-v','ON_ERROR_STOP=1','-At'],
        input=query, text=True, capture_output=True, check=True)
    return result.stdout.strip()

assert sql("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='pg_net') AND to_regprocedure('supabase_functions.http_request()') IS NOT NULL AND current_setting('app.settings.jwt_secret',true) IS NOT NULL AND current_setting('app.settings.jwt_exp',true)='3600';") == 't'
print('PASS: webhooks, pg_net and database JWT settings initialized')
required = ['plpgsql','uuid-ossp','pgcrypto','supabase_vault','pg_net','pg_cron','pg_stat_statements']
installed = sql('SELECT extname FROM pg_extension ORDER BY extname;').splitlines()
assert set(required) <= set(installed), 'Required platform extensions missing: '+str(set(required)-set(installed))
db_pods = json.loads(subprocess.check_output(K+['get','pods','-l','cnpg.io/cluster=supabase-db','-o','json'],text=True))
for db_pod in db_pods['items']:
    probe = subprocess.run(K+['exec',db_pod['metadata']['name'],'-c','postgres','--',
        'psql','-U','postgres','-d','postgres','-v','ON_ERROR_STOP=1','-Atc',
        'SELECT count(*) >= 0 FROM extensions.pg_stat_statements;'],capture_output=True,text=True,check=True)
    assert probe.stdout.strip() == 't'
print('PASS: required platform extension inventory and callable query statistics on all database instances')
pods = json.loads(subprocess.check_output(K+['get','pods','-l','app.kubernetes.io/name=supabase-studio','-o','json'],text=True))
pod = next(p for p in pods['items'] if any(c.get('type')=='Ready' and c.get('status')=='True' for c in p['status'].get('conditions',[])))
name, ip = pod['metadata']['name'], pod['status']['podIP']
extension_test = r'''
async function main() {
  const base='http://127.0.0.1:3000/api/platform/pg-meta/default';
  const listing=await fetch(base+'/extensions');
  if(!listing.ok) throw new Error('Extension listing HTTP '+listing.status);
  const extensions=await listing.json();
  const available=extensions.find(e=>e.name==='hstore');
  if(!available || available.installed_version) throw new Error('Disposable extension test requires hstore available and disabled');
  const query="BEGIN; CREATE EXTENSION hstore WITH SCHEMA extensions; SELECT extname FROM pg_extension WHERE extname='hstore'; DROP EXTENSION hstore; ROLLBACK;";
  const response=await fetch(base+'/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query})});
  if(!response.ok || !(await response.text()).includes('hstore')) throw new Error('Extension lifecycle failed');
  console.log('PASS: Studio extension listing and transactional enable/disable; no extension left installed');
} main().catch(e=>{console.error(e.message);process.exit(1)});
'''
subprocess.run(K+['exec',name,'--','node','-e',extension_test],check=True)
observability_test = r'''
async function main() {
  const base='http://127.0.0.1:3000/api/platform/pg-meta/default';
  const queries=[
    "SET search_path TO public,extensions; SELECT count(*) AS statements, coalesce(sum(calls),0) AS calls FROM pg_stat_statements WHERE dbid=(SELECT oid FROM pg_database WHERE datname=current_database())",
    "SET search_path TO public,extensions; SELECT auth.rolname,statements.calls,statements.total_exec_time+statements.total_plan_time AS total_time,statements.mean_exec_time+statements.mean_plan_time AS mean_time FROM pg_stat_statements AS statements JOIN pg_authid AS auth ON statements.userid=auth.oid WHERE statements.calls>0 ORDER BY total_time DESC LIMIT 20",
    "SET search_path TO public,extensions; SELECT COALESCE(ROUND(AVG(rows::numeric/NULLIF(calls,0)),1),0) AS avg_rows_per_call,COUNT(*) FILTER(WHERE total_exec_time+total_plan_time>1000) AS slow_queries,COALESCE(ROUND(SUM(shared_blks_hit)*100.0/NULLIF(SUM(shared_blks_hit+shared_blks_read),0),2),0) AS cache_hit_rate FROM pg_stat_statements WHERE calls>0",
    "SELECT 'index hit rate' AS name,sum(idx_blks_hit)/nullif(sum(idx_blks_hit+idx_blks_read),0) AS ratio FROM pg_statio_user_indexes UNION ALL SELECT 'table hit rate',sum(heap_blks_hit)/nullif(sum(heap_blks_hit)+sum(heap_blks_read),0) FROM pg_statio_user_tables"
  ];
  for (const query of queries) {
    const response=await fetch(base+'/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query})});
    if(!response.ok || !Array.isArray(await response.json())) throw new Error('Studio observability SQL failed HTTP '+response.status);
  }
  console.log('PASS: Studio query-statistics, role join, metrics and cache-hit-rate SQL routes return data');
} main().catch(e=>{console.error(e.message);process.exit(1)});
'''
subprocess.run(K+['exec',name,'--','node','-e',observability_test],check=True)
table = 'webhook_probe_'+uuid.uuid4().hex[:12]
receiver = r'''
const http=require('http');
const timer=setTimeout(()=>process.exit(2),45000);
const server=http.createServer((req,res)=>{let body='';req.on('data',c=>body+=c);req.on('end',()=>{
  res.writeHead(200,{'content-type':'application/json'});
  res.end(JSON.stringify({received:JSON.parse(body)}));
  console.log('DELIVERED');server.close();clearTimeout(timer);
});});server.listen(19339,'0.0.0.0',()=>console.log('READY'));
'''
process = subprocess.Popen(K+['exec',name,'--','node','-e',receiver],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
oid = request_id = None
try:
    assert process.stdout.readline().strip() == 'READY', 'Temporary webhook receiver failed to start'
    sql(f'''CREATE TABLE homelab_bootstrap.{table}(id int PRIMARY KEY, message text);
CREATE TRIGGER delivery AFTER INSERT ON homelab_bootstrap.{table} FOR EACH ROW
EXECUTE FUNCTION supabase_functions.http_request('http://{ip}:19339/probe','POST','{{"Content-Type":"application/json"}}','{{}}','5000');
INSERT INTO homelab_bootstrap.{table} VALUES(1,'homelab-webhook-probe');''')
    oid = sql(f"SELECT 'homelab_bootstrap.{table}'::regclass::oid;")
    request_id = sql(f'SELECT request_id FROM supabase_functions.hooks WHERE hook_table_id={int(oid)};')
    assert request_id.isdigit()
    deadline = time.monotonic()+25
    while time.monotonic()<deadline:
        result = sql(f"SELECT json_build_object('status',status_code,'error',error_msg,'content',content)::text FROM net._http_response WHERE id={int(request_id)};")
        if result:
            response = json.loads(result)
            assert response['status']==200 and response['error'] is None, response
            payload = json.loads(response['content'])['received']
            assert payload['type']=='INSERT' and payload['table']==table
            assert payload['record']=={'id':1,'message':'homelab-webhook-probe'}
            print('PASS: INSERT trigger -> pg_net queue -> actual HTTP POST -> correct record payload -> HTTP 200')
            break
        time.sleep(1)
    else:
        raise RuntimeError('Webhook delivery did not complete before deadline')
finally:
    sql(f'DROP TABLE IF EXISTS homelab_bootstrap.{table};')
    if oid:
        sql(f'DELETE FROM supabase_functions.hooks WHERE hook_table_id={int(oid)};')
    if request_id and request_id.isdigit():
        sql(f'DELETE FROM net._http_response WHERE id={int(request_id)};')
    process.terminate()
    process.communicate(timeout=50)
print('PASS: disposable table, trigger, audit row and response removed; no application data changed')
