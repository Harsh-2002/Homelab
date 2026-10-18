#!/usr/bin/env python3
"""Sync only production Studio's backend header into protected Caddy env."""
import base64
import json
from pathlib import Path
import subprocess

op=Path(__file__).resolve().parents[2]/'scripts/op-sa'
item=json.loads(subprocess.check_output([str(op),'item','get','Supabase','--vault','HomeLab','--format','json']))
values=json.loads(next(f['value'] for f in item['fields'] if f.get('label')=='deployment-secrets'))
header='Basic '+base64.b64encode((values['username']+':'+values['dashboardPassword']).encode()).decode()
program='''import pathlib,sys,os
p=pathlib.Path('/etc/caddy/cloudflare.env')
value=sys.stdin.read().strip()
old=p.read_text().splitlines()
key='SUPABASE_STUDIO_AUTH'
new=[line for line in old if not line.startswith(key+'=')]
new.append(key+'="'+value+'"')
p.write_text('\\n'.join(new)+'\\n')
os.chmod(p,0o640)
'''
import shlex
command='python3 -c '+shlex.quote(program)
subprocess.run(['ssh','proxy',command],input=header,text=True,check=True)
print('Production Studio backend credential synchronized; no secret output')
