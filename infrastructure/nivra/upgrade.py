#!/usr/bin/env python3
"""Upgrade existing Nivra through Portainer, with stopped-writer backup first.

Run on dev after reviewing the release and pre-pulling latest on CTR.
Never emits vault credentials, stack env, account data or note contents.
"""
import datetime
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://portainer.l3b.cc.cd/api'
item = json.loads(subprocess.check_output([str(ROOT/'scripts/op-sa'), 'item', 'get', 'Portainer', '--vault', 'HomeLab', '--format', 'json']))
key = next(f['value'] for f in item['fields'] if f.get('label') == 'access-token')
def api(path, method='GET', data=None):
    request = urllib.request.Request(BASE+path, None if data is None else json.dumps(data).encode(),
        {'X-API-Key':key, 'Content-Type':'application/json'}, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        body = response.read()
        return json.loads(body) if body else None
stacks = [s for s in api('/stacks') if s['Name']=='nivra']
assert len(stacks)==1 and stacks[0]['EndpointId']==2
sid = stacks[0]['Id']
stack = api(f'/stacks/{sid}')
old = api(f'/stacks/{sid}/file')['StackFileContent']
new = (ROOT/'infrastructure/nivra/compose.yaml').read_text()
image = next(line.strip().split('image:',1)[1].strip() for line in new.splitlines() if line.strip().startswith('image:'))
assert '/data/apps/nivra:/data' in old and '/data/apps/nivra:/data' in new
subprocess.run(['ssh','ctr','docker image inspect '+image+' --format "{{.Id}}"'],check=True,capture_output=True)
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup = '/data/nivra-upgrade-backups/'+stamp
subprocess.run(['ssh','ctr',f"sudo sh -c 'install -d -m 700 /data/nivra-upgrade-backups {backup} && umask 077 && install -m 600 /dev/stdin {backup}/stack-before.json'"],input=json.dumps({'stack':stack,'compose':old}),text=True,check=True)
api('/endpoints/2/docker/containers/nivra/stop?t=30','POST')
updated = False
try:
    script = r'''
import hashlib,json,sqlite3,tarfile,subprocess
from pathlib import Path
root=Path('/data/apps/nivra')
backup=Path(__BACKUP__)
db=sqlite3.connect('file:'+str(root/'nivra.sqlite')+'?mode=ro',uri=True)
assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
tables=['user','notes','attachments','tasks','bookmarks','artifacts','forms','form_responses','writing_templates','apikey','oauth_client']
manifest={}
for table in tables:
 rows=db.execute('select * from '+table+' order by rowid').fetchall()
 manifest[table]={'count':len(rows),'sha256':hashlib.sha256(repr(rows).encode()).hexdigest()}
(backup/'content-before.json').write_text(json.dumps(manifest))
subprocess.run(['tar','-C','/data/apps','-czf',str(backup/'data.tar.gz'),'nivra'],check=True)
with tarfile.open(backup/'data.tar.gz','r:gz') as archive:
 for member in archive:
  if member.isfile():
   f=archive.extractfile(member)
   while f.read(1024*1024):pass
subprocess.run(['chmod','600',str(backup/'data.tar.gz'),str(backup/'content-before.json')],check=True)
print('Consistent stopped-writer backup validated; SQLite integrity ok')
'''.replace('__BACKUP__',repr(backup))
    subprocess.run(['ssh','ctr','sudo python3 -'],input=script,text=True,check=True)
    updated = True
    api(f'/stacks/{sid}?endpointId=2','PUT',{'StackFileContent':new,'Env':stack.get('Env',[]),'Prune':False,'PullImage':False})
finally:
    if not updated:
        api('/endpoints/2/docker/containers/nivra/start','POST')
deadline = time.monotonic()+120
while time.monotonic()<deadline:
    info=api('/endpoints/2/docker/containers/nivra/json')
    if info['State'].get('Health',{}).get('Status')=='healthy':
        assert info['Config']['Image']==image
        break
    time.sleep(3)
else:
    raise SystemExit('New container unhealthy; preserve backup and inspect before rollback')
print('Portainer stack',sid,'healthy; rollback backup:',backup)
print('Image:',image)
print('Backup includes plaintext private data: keep root-only; do not upload to Git')
