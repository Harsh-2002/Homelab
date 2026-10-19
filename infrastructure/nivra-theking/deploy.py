#!/usr/bin/env python3
"""Create only the friend's isolated Portainer stack; never onboard its owner."""
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
NAME = 'nivra-theking'
BASE = 'https://portainer.l3b.cc.cd/api'
item = json.loads(subprocess.check_output([str(ROOT/'scripts/op-sa'),
    'item', 'get', 'Portainer', '--vault', 'HomeLab', '--format', 'json']))
key = next(f['value'] for f in item['fields'] if f.get('label') == 'access-token')


def api(path, method='GET', data=None):
    request = urllib.request.Request(BASE+path,
        None if data is None else json.dumps(data).encode(),
        {'X-API-Key': key, 'Content-Type': 'application/json'}, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


assert not any(s['Name'] == NAME for s in api('/stacks')), 'Stack exists: do not recreate or overwrite it'
baseline = api('/endpoints/2/docker/containers/nivra/json')
assert baseline['State']['Health']['Status'] == 'healthy'
compose = (ROOT/'infrastructure/nivra-theking/docker-compose.yaml').read_text()
assert '/data/apps/nivra:/data' not in compose
assert '/data/apps/nivra-theking:/data' in compose
preflight = '''
set -eu
test ! -e /data/apps/nivra-theking
test -z "$(sudo docker ps -a --filter name='^/nivra-theking$' --format '{{.Names}}')"
sudo docker image inspect ghcr.io/harsh-2002/nivra:latest >/dev/null
sudo install -d -m 750 -o 1000 -g 1000 /data/apps/nivra-theking
'''
subprocess.run(['ssh', '-o', 'BatchMode=yes', 'ctr', preflight], check=True)
subprocess.run(['ssh', '-o', 'BatchMode=yes', 'ctr',
    'sudo install -m 640 -o root -g 1000 /dev/stdin /data/apps/nivra-theking/docker-compose.yaml'],
    input=compose, text=True, check=True)
stack = api('/stacks/create/standalone/string?endpointId=2', 'POST',
    {'Name': NAME, 'StackFileContent': compose, 'Env': []})
print('Created Portainer stack', stack['Id'], NAME, flush=True)
deadline = time.monotonic()+120
while time.monotonic() < deadline:
    try:
        info = api('/endpoints/2/docker/containers/nivra-theking/json')
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        time.sleep(3)
        continue
    if info['State'].get('Health', {}).get('Status') == 'healthy':
        break
    time.sleep(3)
else:
    raise SystemExit('New instance not healthy; preserve its data and inspect before publishing')
assert any(m['Source'] == '/data/apps/nivra-theking' and m['Destination'] == '/data' for m in info['Mounts'])
assert not any(m['Source'] == '/data/apps/nivra' for m in info['Mounts'])
current = api('/endpoints/2/docker/containers/nivra/json')
assert current['Id'] == baseline['Id'] and current['State']['Health']['Status'] == 'healthy'
print('Healthy Portainer stack', stack['Id'], NAME, 'endpoint2; original Nivra unchanged')
print('No owner account, password, API key, agent integration or Homepage entry created')
