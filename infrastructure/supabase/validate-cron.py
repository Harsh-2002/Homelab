#!/usr/bin/env python3
"""Exercise real pg_cron execution, not just catalog access; clean owned fixtures."""
import json
from pathlib import Path
import subprocess
import time
import uuid

K = ['kubectl', '--context', 'k8s', '--request-timeout=15s', '-n', 'supabase-prod']


def kubectl(*args):
    return subprocess.check_output(K + list(args), text=True, timeout=30).strip()


primary = kubectl('get', 'cluster', 'supabase-db', '-o', 'jsonpath={.status.currentPrimary}')


def sql(query, database='postgres', pod=primary):
    response = subprocess.run(K + ['exec', '-i', pod, '-c', 'postgres', '--',
        'psql', '-X', '-U', 'postgres', '-d', database, '-v', 'ON_ERROR_STOP=1', '-At'],
        input="SET statement_timeout='10s';\n" + query, text=True,
        capture_output=True, timeout=25, check=True)
    return '\n'.join(line for line in response.stdout.strip().splitlines() if line != 'SET')


pods = json.loads(kubectl('get', 'pods', '-l', 'cnpg.io/cluster=supabase-db', '-o', 'json'))
assert len(pods['items']) == 3
for pod in pods['items']:
    name = pod['metadata']['name']
    assert sql("SELECT current_setting('cron.use_background_workers')='on' "
        "AND current_setting('cron.max_running_jobs')='4' "
        "AND NOT EXISTS(SELECT 1 FROM pg_settings WHERE pending_restart);", pod=name) == 't', name
print('PASS: background-worker mode active on all3 DB instances; no pending restart', flush=True)

schema = 'homelab_cron_probe_' + uuid.uuid4().hex[:12]
databases = []
jobs = []
try:
    for database in ('postgres', '_supabase'):
        sql(f'CREATE SCHEMA {schema}; CREATE TABLE {schema}.probe('
            'ran_at timestamptz DEFAULT clock_timestamp(), actor name, db name);', database)
        databases.append(database)
        command = f'INSERT INTO {schema}.probe(actor,db) VALUES(current_user,current_database())'
        jobname = schema + '_' + database
        result = sql(f"SELECT cron.schedule_in_database('{jobname}','5 seconds',"
            f"'{command}','{database}','postgres');")
        assert result.isdigit(), result
        jobs.append(int(result))
    # Studio SQL requests execute as supabase_admin, not postgres.
    result = sql(f"SET ROLE supabase_admin; SELECT cron.schedule('{schema}_studio',"
        f"'5 seconds','INSERT INTO {schema}.probe(actor,db) VALUES(current_user,current_database())');")
    assert result.isdigit(), result
    jobs.append(int(result))
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        postgres = json.loads(sql(f"SELECT json_build_object('postgres',count(*) FILTER(WHERE actor='postgres'),"
            f"'supabase_admin',count(*) FILTER(WHERE actor='supabase_admin')) FROM {schema}.probe WHERE db='postgres';"))
        analytics = int(sql(f"SELECT count(*) FROM {schema}.probe WHERE actor='postgres' AND db='_supabase';", '_supabase'))
        success = int(sql('SELECT count(DISTINCT jobid) FROM cron.job_run_details WHERE status=\'succeeded\' AND jobid IN (' + ','.join(map(str, jobs)) + ');'))
        if min(postgres.values()) >= 2 and analytics >= 2 and success == 3:
            print('PASS: repeated scheduled writes in postgres and _supabase; postgres and Studio supabase_admin roles', flush=True)
            print('PASS: all3 owned jobs have succeeded execution records', flush=True)
            break
        time.sleep(2)
    else:
        raise RuntimeError('Cron execution probe timed out: ' + sql(
            'SELECT json_agg(t) FROM (SELECT jobid,status,return_message FROM cron.job_run_details WHERE jobid IN (' +
            ','.join(map(str, jobs)) + ') ORDER BY runid DESC LIMIT 6)t;'))
finally:
    for job in jobs:
        sql(f'SELECT cron.unschedule({job});')
    # Unschedule first, then wait until the owned workers have finished.
    for database in databases:
        sql(f'DROP TABLE {schema}.probe; DROP SCHEMA {schema};', database)
    if jobs:
        sql('DELETE FROM cron.job_run_details WHERE jobid IN (' + ','.join(map(str, jobs)) + ');')
    print('Owned cron jobs, test schemas/tables and execution records removed; existing jobs untouched', flush=True)
