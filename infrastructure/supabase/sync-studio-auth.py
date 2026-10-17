#!/usr/bin/env python3
"""Operator helper: sync backend Studio credential to Caddy, never display it.

Run on dev with trusted supabase/proxy SSH aliases. Caddy expands this variable
at config-adaptation time; source the protected file when validating/reloading.
"""
import base64
import shlex
import subprocess

raw = subprocess.check_output(['ssh', 'supabase', 'sudo cat /srv/supabase/.env'], text=True)
env = {}
for line in raw.splitlines():
    if line and not line.startswith('#') and '=' in line:
        key, value = line.split('=', 1)
        if key in ('DASHBOARD_USERNAME', 'DASHBOARD_PASSWORD'):
            env[key] = shlex.split(value)[0] if value else ''
assert all(env.get(key) for key in ('DASHBOARD_USERNAME', 'DASHBOARD_PASSWORD'))
credential = 'Basic ' + base64.b64encode((env['DASHBOARD_USERNAME'] + ':' + env['DASHBOARD_PASSWORD']).encode()).decode()
remote = '''import pathlib, re, sys
path = pathlib.Path('/etc/caddy/cloudflare.env')
text = path.read_text()
value = sys.stdin.read().strip()
assert value.startswith('Basic ') and "'" not in value and '\\n' not in value
line = "SUPABASE_STUDIO_AUTH='" + value + "'"
pattern = r'^SUPABASE_STUDIO_AUTH=.*$'
text = re.sub(pattern, lambda _: line, text, flags=re.M) if re.search(pattern, text, re.M) else text.rstrip() + '\\n' + line + '\\n'
path.write_text(text)
path.chmod(0o600)
'''
subprocess.run(['ssh', 'proxy', 'python3 -c ' + shlex.quote(remote)], input=credential, text=True, check=True)
print('Synced protected Studio backend credential to Caddy; no secret displayed')
