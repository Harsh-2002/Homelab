#!/usr/bin/env python3
"""Owner-authorized exact-target Anchor retirement. Never emit credentials."""
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
VOLUME = '7e046962cf1dc044453e241b3ecafbde74e3e5b90d001128acb477a4aae218c4'
IMAGE = 'ghcr.io/zhfahim/anchor:0.17.2@sha256:e6e791ab834794516bc05d8967607c4db4ea1565a658548930421382c4e48a0a'

def ssh(command):
    return subprocess.check_output(['ssh', 'ctr', command], text=True).strip()

item = json.loads(subprocess.check_output([
    str(ROOT/'scripts/op-sa'), 'item', 'get', 'Portainer',
    '--vault', 'HomeLab', '--format', 'json']))
key = next(f['value'] for f in item['fields'] if f.get('label') == 'access-token')

def api(path, method='GET'):
    request = urllib.request.Request('https://portainer.l3b.cc.cd/api'+path,
        headers={'X-API-Key': key}, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        body = response.read()
        return json.loads(body) if body else None

stacks = [s for s in api('/stacks') if s['Name'] == 'anchor']
assert len(stacks) == 1 and stacks[0]['Id'] == 154 and stacks[0]['EndpointId'] == 2
container = api('/endpoints/2/docker/containers/anchor/json')
assert container['Name'] == '/anchor' and container['Config']['Image'] == IMAGE
assert any(m['Source'] == '/data/apps/anchor' and m['Destination'] == '/data'
           for m in container['Mounts'])
assert any(m.get('Name') == VOLUME and m['Destination'] == '/var/lib/postgresql'
           for m in container['Mounts'])
assert ssh(f"sudo docker ps -a --filter volume={VOLUME} --format '{{{{.Names}}}}'") == 'anchor'
assert ssh("sudo realpath /data/apps/anchor") == '/data/apps/anchor'
nivra_id = ssh("sudo docker inspect nivra --format '{{.Id}}'")
assert nivra_id and ssh("sudo docker inspect nivra --format '{{.State.Health.Status}}'") == 'healthy'
api('/stacks/154?endpointId=2', 'DELETE')
assert not [s for s in api('/stacks') if s['Name'] == 'anchor']
assert not ssh("sudo docker ps -a --filter name='^/anchor$' --format '{{.Names}}'")
assert not ssh(f"sudo docker ps -a --filter volume={VOLUME} --format '{{{{.Names}}}}'")
volumes = ssh(f"sudo docker volume ls --filter name='^{VOLUME}$' --format '{{{{.Name}}}}'")
if volumes:
    assert volumes == VOLUME
    ssh('sudo docker volume rm '+VOLUME)
ssh('sudo rm -rf -- /data/apps/anchor')
assert ssh('test ! -e /data/apps/anchor && echo removed') == 'removed'
if not ssh(f"sudo docker ps -a --filter ancestor={IMAGE} --format '{{{{.Names}}}}'"):
    ssh('sudo docker image rm '+IMAGE)
assert not ssh("sudo docker network ls --filter name='^anchor_default$' --format '{{.Name}}'")
assert ssh("sudo docker inspect nivra --format '{{.Id}}'") == nivra_id
assert ssh("sudo docker inspect nivra --format '{{.State.Health.Status}}'") == 'healthy'
print('Anchor stack, container, owned volume, bind data, network and unused image removed. Nivra unchanged and healthy.')
