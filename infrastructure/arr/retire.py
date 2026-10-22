#!/usr/bin/env python3
"""Owner-authorized ARR retirement. Preserve downloads/media and retained apps.

No backups. Move qBittorrent's stopped configuration intact to its own stack.
Never prints credentials, torrent names, application configuration or Stack Env.
"""
import hashlib
import http.cookiejar
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if sys.argv[1:] != ['--execute']:
    raise SystemExit('Explicit owner-authorized deletion only: retire.py --execute')
ROOT = Path(__file__).resolve().parents[2]
OP = str(ROOT/'scripts/op-sa')
REMOVED = {'sonarr','radarr','prowlarr','bazarr','seerr','lidarr','readarr',
    'cleanuparr','unpackerr','soularr','slskd'}
VAULT_TITLES = {'Sonarr','Radarr','Prowlarr','Bazarr','Lidarr','Readarr','Cleanuparr','Soulseek'}


def op(*args):
    return subprocess.check_output([OP,*args], text=True)


def item(name):
    return json.loads(op('item','get',name,'--vault','HomeLab','--format','json'))


def field(record, label):
    return next(f['value'] for f in record['fields'] if f.get('label') == label)


key = field(item('Portainer'), 'access-token')


def api(path, method='GET', data=None):
    req = urllib.request.Request('https://portainer.l3b.cc.cd/api'+path,
        None if data is None else json.dumps(data).encode(),
        {'X-API-Key':key, 'Content-Type':'application/json'}, method=method)
    with urllib.request.urlopen(req, timeout=240) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def ssh(script, data=None):
    return subprocess.check_output(['ssh','-o','BatchMode=yes','ctr',script],input=data,text=True).strip()


qbit = item('qBittorrent')


def torrent_hashes():
    jar = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    base = 'http://10.1.1.4:8081'
    body = urllib.parse.urlencode({'username':field(qbit,'username'),'password':field(qbit,'password')}).encode()
    with client.open(urllib.request.Request(base+'/api/v2/auth/login',body,
            headers={'Referer':base}),timeout=10) as response:
        result = response.read()
        assert (response.status==200 and result==b'Ok.') or (response.status==204 and not result)
    with client.open(base+'/api/v2/torrents/info',timeout=15) as response:
        result = {t['hash'] for t in json.load(response)}
    client.open(urllib.request.Request(base+'/api/v2/auth/logout',b''),timeout=10).close()
    return result


stacks = [s for s in api('/stacks') if s['Name']=='arr']
assert len(stacks)==1 and stacks[0]['Id']==153 and stacks[0]['EndpointId']==2
assert not any(s['Name']=='qbittorrent' for s in api('/stacks'))
containers = api('/endpoints/2/docker/containers/json?all=1')
owned = [c for c in containers if c['Labels'].get('com.docker.compose.project')=='arr']
assert {c['Names'][0].lstrip('/') for c in owned} == REMOVED|{'qbittorrent'}
baseline = {n:api('/endpoints/2/docker/containers/'+n+'/json') for n in ['qbittorrent','jellyfin','motrix-server']}
assert any(m['Source']=='/data/apps/arr/qbittorrent' and m['Destination']=='/config' for m in baseline['qbittorrent']['Mounts'])
assert api('/endpoints/2/docker/images/lscr.io/linuxserver/qbittorrent:latest/json')['Id'] == baseline['qbittorrent']['Image'], 'Do not upgrade qBittorrent during retirement'
assert ssh("test ! -e /data/apps/qbittorrent && test -d /data/apps/arr/qbittorrent && mountpoint -q /mnt/AV && echo safe")=='safe'
actual = set(ssh('sudo find /data/apps/arr -mindepth 1 -maxdepth 1 -printf "%f\\n"').splitlines())
assert actual == REMOVED|{'qbittorrent'}, 'Unexpected data under ARR: inspect before deleting'
before = torrent_hashes()
print('Preflight passed:',len(REMOVED),'retired services;',len(before),'torrent entries to preserve',flush=True)
api('/endpoints/2/docker/containers/qbittorrent/stop?t=120','POST')
manifest_script = '''
import hashlib,json,pathlib
root=pathlib.Path('/data/apps/arr/qbittorrent')
print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}))
'''
manifest = json.loads(ssh('sudo python3 -',manifest_script))
api('/stacks/153?endpointId=2','DELETE')
assert not any(s['Name']=='arr' for s in api('/stacks'))
assert not [c for c in api('/endpoints/2/docker/containers/json?all=1') if c['Labels'].get('com.docker.compose.project')=='arr']
ssh('sudo mv -- /data/apps/arr/qbittorrent /data/apps/qbittorrent')
after_move = json.loads(ssh('sudo python3 -',manifest_script.replace('/data/apps/arr/qbittorrent','/data/apps/qbittorrent')))
assert manifest == after_move, 'Stopped qBittorrent config changed during move'
compose = (ROOT/'infrastructure/qbittorrent/docker-compose.yaml').read_text()
stack = api('/stacks/create/standalone/string?endpointId=2','POST',
    {'Name':'qbittorrent','StackFileContent':compose,'Env':[]})
print('Created standalone qBittorrent stack',stack['Id'],'with unchanged configuration',flush=True)
deadline=time.monotonic()+180
while time.monotonic()<deadline:
    try:
        current=api('/endpoints/2/docker/containers/qbittorrent/json')
        if current['State'].get('Health',{}).get('Status')=='healthy':
            assert current['Image']==baseline['qbittorrent']['Image']
            assert torrent_hashes()==before
            break
    except urllib.error.HTTPError as error:
        if error.code!=404: raise
    time.sleep(3)
else:raise SystemExit('qBittorrent needs recovery; data retained, no retired folders deleted yet')
print('qBittorrent healthy; identical torrent hash set, config moved byte-for-byte, same image',flush=True)
for name in ['jellyfin','motrix-server']:
    current=api('/endpoints/2/docker/containers/'+name+'/json')
    assert current['Id']==baseline[name]['Id'] and current['State']['Running']

# Exact stopped-app directories only. Never touch /mnt/AV or any media/downloads.
cleanup = '''
import json,os,pathlib,shutil
root=pathlib.Path('/data/apps/arr')
names=__NAMES__
assert root.resolve()==root and not root.is_symlink()
assert set(p.name for p in root.iterdir())==set(names)
for name in names:
 p=root/name
 assert p.resolve()==p and p.is_dir() and not p.is_symlink() and not os.path.ismount(p)
 for base,dirs,files in os.walk(p,followlinks=False):
  assert not os.path.ismount(base)
 shutil.rmtree(p)
 print('Deleted retired app data:',name,flush=True)
root.rmdir()
'''.replace('__NAMES__',repr(sorted(REMOVED)))
print(ssh('sudo python3 -',cleanup),flush=True)
assert not [c for c in api('/endpoints/2/docker/containers/json?all=1') if c['Names'][0].lstrip('/') in REMOVED]
remaining_images={c['ImageID'] for c in api('/endpoints/2/docker/containers/json?all=1')}
for image in sorted({c['ImageID'] for c in owned if c['Names'][0].lstrip('/') in REMOVED}):
    if image not in remaining_images:
        api('/endpoints/2/docker/images/'+image+'?force=false','DELETE')
print('Unused retired-service images removed; retained images untouched',flush=True)
vault=json.loads(op('item','list','--vault','HomeLab','--format','json'))
targets=[i for i in vault if i['title'] in VAULT_TITLES]
assert {i['title'] for i in targets}==VAULT_TITLES
for entry in targets:
    record=item(entry['id'])
    assert record['title'] in VAULT_TITLES
    op('item','delete',entry['id'],'--vault','HomeLab')
    print('Deleted retired-service vault item:',entry['title'],flush=True)
print('ARR retired. No backup created. qBittorrent, Motrix, Jellyfin and media/downloads retained.',flush=True)
