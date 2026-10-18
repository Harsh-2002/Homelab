#!/usr/bin/env python3
"""Deploy Omni through Portainer. Never accepts EULA or imports nodes.

Secrets are read/written through the existing HomeLab vault service account.
No secret is emitted or placed in Compose/Portainer stack environment.
"""
import json
import subprocess
import tempfile
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OP = str(ROOT / 'scripts/op-sa')


def op(*args, payload=None):
    return subprocess.check_output([OP, *args], input=payload, text=True)


def request(base, path, headers, method='GET', body=None):
    req = urllib.request.Request(base + path,
        None if body is None else json.dumps(body).encode(),
        {**headers, 'Content-Type': 'application/json'}, method=method)
    with urllib.request.urlopen(req, timeout=180) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def field(item, label):
    return next(f['value'] for f in item['fields'] if f.get('label') == label)


def put_file(path, content):
    assert path.startswith('/data/apps/omni/')
    subprocess.run(['ssh', '-o', 'BatchMode=yes', 'ctr',
        f'sudo install -m 600 /dev/stdin {path}'],
        input=content, text=True, check=True, capture_output=True)


items = json.loads(op('item', 'list', '--vault', 'HomeLab', '--format', 'json'))
found = [i for i in items if i['title'] == 'Omni']
if found:
    assert len(found) == 1
    secrets = json.loads(field(json.loads(op('item', 'get', found[0]['id'],
        '--vault', 'HomeLab', '--format', 'json')), 'deployment-secrets'))
else:
    key = op('read', 'op://HomeLab/Pocket ID Automation API/credential').strip()
    def pocket(path, method='GET', body=None):
        return request('https://auth.l3b.cc.cd/api', path, {'X-API-KEY': key}, method, body)
    users = pocket('/users')['data']
    owner = next(u for u in users if u.get('isAdmin') and not u.get('disabled'))
    group = next(g for g in pocket('/user-groups')['data'] if g['name'] == 'infrastructure-admins')
    clients = pocket('/oidc/clients')['data']
    assert not any(c['id'] == 'omni' for c in clients), 'Existing Omni client: reconcile manually; do not rotate'
    pocket('/oidc/clients', 'POST', {
        'id': 'omni', 'name': 'Omni', 'description': 'Homelab Talos management',
        'callbackURLs': ['https://omni.l3b.cc.cd/oidc/consume'],
        'logoutCallbackURLs': ['https://omni.l3b.cc.cd'],
        'isPublic': False, 'pkceEnabled': False,
        'requiresReauthentication': False, 'requiresPushedAuthorizationRequests': False,
        'skipConsent': True, 'credentials': {}, 'launchURL': 'https://omni.l3b.cc.cd',
        'isGroupRestricted': True, 'accessTokenDurationMinutes': 15,
        'refreshTokenDurationMinutes': 10080})
    pocket('/oidc/clients/omni/allowed-user-groups', 'PUT', {'userGroupIds': [group['id']]})
    client_secret = pocket('/oidc/clients/omni/secrets', 'POST', {})
    assert isinstance(client_secret.get('secret'), str), 'Unexpected secret response: inspect schema without values'
    with tempfile.TemporaryDirectory(prefix='homelab-omni-gpg-') as home:
        def gpg(*args):
            return subprocess.check_output(['gpg', '--homedir', home, '--batch',
                '--pinentry-mode', 'loopback', '--passphrase', '', *args], stderr=subprocess.DEVNULL)
        identity = 'Omni (Homelab etcd encryption) <omni@l3b.cc.cd>'
        gpg('--quick-generate-key', identity, 'rsa4096', 'cert', 'never')
        listing = gpg('--with-colons', '--list-keys', identity).decode()
        fingerprint = next(line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:'))
        gpg('--quick-add-key', fingerprint, 'rsa4096', 'encr', 'never')
        private_key = gpg('--armor', '--export-secret-keys', identity).decode()
    secrets = {'accountId': str(uuid.uuid4()), 'adminEmail': owner['email'],
        'oidcClientSecret': client_secret['secret'], 'encryptionKey': private_key}
    record = {'title': 'Omni', 'category': 'API_CREDENTIAL',
        'urls': [{'href': 'https://omni.l3b.cc.cd', 'primary': True}],
        'fields': [{'id': 'deployment-secrets', 'label': 'deployment-secrets',
            'type': 'CONCEALED', 'value': json.dumps(secrets)}]}
    op('item', 'create', '--vault', 'HomeLab', '--format', 'json', '-', payload=json.dumps(record))
    print('Omni recovery material saved in HomeLab vault; Pocket ID client restricted to infrastructure-admins')

subprocess.run(['ssh', '-o', 'BatchMode=yes', 'ctr',
    'sudo install -d -m 700 /data/apps/omni /data/apps/omni/state /data/apps/omni/state/sqlite'], check=True)
config = {'account': {'id': secrets['accountId'], 'name': 'Homelab'},
    'auth': {'auth0': {'enabled': False},
        'initialUsers': [secrets['adminEmail']],
        'oidc': {'enabled': True, 'providerURL': 'https://auth.l3b.cc.cd',
            'clientID': 'omni', 'clientSecret': secrets['oidcClientSecret'],
            'scopes': ['openid', 'profile', 'email'], 'allowUnverifiedEmail': False}}}
put_file('/data/apps/omni/config.yaml', json.dumps(config))
put_file('/data/apps/omni/omni.asc', secrets['encryptionKey'])
compose = (ROOT / 'infrastructure/omni/docker-compose.yaml').read_text()
put_file('/data/apps/omni/docker-compose.yaml', compose)
portainer = json.loads(op('item', 'get', 'Portainer', '--vault', 'HomeLab', '--format', 'json'))
def api(path, method='GET', body=None):
    return request('https://portainer.l3b.cc.cd/api', path,
        {'X-API-Key': field(portainer, 'access-token')}, method, body)
stacks = [s for s in api('/stacks') if s['Name'] == 'omni']
if stacks:
    assert len(stacks) == 1 and stacks[0]['EndpointId'] == 2
    stack = api(f"/stacks/{stacks[0]['Id']}")
    api(f"/stacks/{stack['Id']}?endpointId=2", 'PUT', {
        'StackFileContent': compose, 'Env': stack.get('Env', []),
        'Prune': False, 'PullImage': False})
else:
    stack = api('/stacks/create/standalone/string?endpointId=2', 'POST', {
        'Name': 'omni', 'StackFileContent': compose, 'Env': []})
print('Portainer stack omni:', stack['Id'], '; EULA acceptance and node import are separate')
