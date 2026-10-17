#!/usr/bin/env python3
"""Read-only application acceptance; never prints login or private content."""
import http.cookiejar
import json
from pathlib import Path
import subprocess
import urllib.request
import urllib.error

base='https://notes.l3b.cc.cd'
op=Path(__file__).resolve().parents[2]/'scripts/op-sa'
item=json.loads(subprocess.check_output([str(op),'item','get','Nivra','--vault','HomeLab','--format','json']))
fields={f['id']:f.get('value','') for f in item['fields']}
jar=http.cookiejar.CookieJar()
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def request(path, data=None, expected=200):
    req=urllib.request.Request(base+path,None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json','Origin':base})
    try:
        with client.open(req,timeout=30) as response:
            assert response.status==expected
            body=response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        if error.code!=expected:
            raise SystemExit('Application check failed: '+path+' HTTP '+str(error.code)+'; private response withheld')
request('/health')
request('/api/v1/notes',expected=401)
login=request('/api/auth/sign-in/email',{'email':fields['username'],'password':fields['password']})
if login.get('twoFactorRedirect'):
    raise SystemExit('Native login requires owner MFA; no bypass attempted')
request('/api/v1/notes')
system=request('/api/v1/system')
print('PASS: HTTPS health, unauthenticated data denial, native owner login and authenticated notes/system reads')
print('System top-level keys (no values):', ', '.join(system.keys()))
