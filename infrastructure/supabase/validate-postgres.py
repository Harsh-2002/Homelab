#!/usr/bin/env python3
"""Run from dev; test the Caddy PG TLS boundary without printing DB secrets."""
import subprocess

program = r'''
import os, shlex, subprocess
from pathlib import Path
values = {}
for line in Path('/srv/supabase/.env').read_text().splitlines():
    if line and not line.startswith('#') and '=' in line:
        k,v = line.split('=',1)
        values[k] = shlex.split(v)[0] if v else ''
env = dict(os.environ, PGPASSWORD=values['POSTGRES_PASSWORD'])
dsn = 'host=sb.l3b.cc.cd port=5432 dbname=postgres user=postgres sslmode=verify-full sslrootcert=/etc/ssl/certs/ca-certificates.crt connect_timeout=10'
result = subprocess.run(['docker','exec','-e','PGPASSWORD','supabase-db','psql',dsn,'-v','ON_ERROR_STOP=1','-Atc','select current_database(), current_user, 1'],env=env,capture_output=True,text=True)
if result.returncode:
    raise SystemExit('PostgreSQL TLS/auth test failed: '+ result.stderr.replace(values['POSTGRES_PASSWORD'], '[REDACTED]'))
assert result.stdout.strip() == 'postgres|postgres|1', result.stdout
print('PASS: authenticated SQL through sb:5432 with certificate and hostname verification')
env['PGPASSWORD'] = 'intentional-invalid-validation-password'
result = subprocess.run(['docker','exec','-e','PGPASSWORD','supabase-db','psql',dsn,'-Atc','select 1'],env=env,capture_output=True,text=True)
assert result.returncode != 0 and ('password' in result.stderr.lower() or 'authentication' in result.stderr.lower())
print('PASS: invalid PostgreSQL password rejected')
'''
subprocess.run(['ssh', 'supabase', 'sudo python3 -'], input=program, text=True, check=True)
