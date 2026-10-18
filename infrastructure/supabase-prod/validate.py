#!/usr/bin/env python3
"""Disposable end-to-end acceptance test. Run on dev with the k8s kubectl context and vault access.

Reads credentials only from the canonical 1Password item. Never prints tokens.
Use --keep to retain fixtures for the restart persistence test; --cleanup removes
only these explicitly named acceptance fixtures.
"""
import base64
import json
import pathlib
import secrets
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
import websocket

ROOT = pathlib.Path(__file__).resolve().parents[2]
item = json.loads(subprocess.check_output([str(ROOT / 'scripts/op-sa'), 'item', 'get', 'Supabase Production', '--vault', 'HomeLab', '--format', 'json']))
values = json.loads(next(field['value'] for field in item['fields'] if field.get('label') == 'deployment-secrets'))
ENV = {
    'SUPABASE_SECRET_KEY': values['secretKey'],
    'SUPABASE_PUBLISHABLE_KEY': values['publishableKey'],
    'DASHBOARD_USERNAME': values['username'],
    'DASHBOARD_PASSWORD': values['dashboardPassword'],
}
BASE = 'https://sb-prod.l3b.cc.cd'
STUDIO = 'https://supabase-prod.l3b.cc.cd'
STATE = pathlib.Path.home() / '.local/state/homelab/supabase-prod-acceptance.json'
STATE.parent.mkdir(parents=True, exist_ok=True)

def request(path, method='GET', data=None, user=None, admin=False, anonymous=False, raw=False, headers=None, expected=(200, 201, 204)):
    head = {} if anonymous else {'apikey': ENV['SUPABASE_SECRET_KEY'] if admin else ENV['SUPABASE_PUBLISHABLE_KEY']}
    if user:
        head['Authorization'] = 'Bearer ' + user
    if headers:
        head.update(headers)
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode()
        head['Content-Type'] = 'application/json'
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, data, head, method=method), timeout=35) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, body = error.code, error.read()
    assert status in expected, f'{method} {path.split("?")[0]}: unexpected HTTP {status}, error category {json.loads(body).get("code", "unknown") if body[:1] == b"{" else "non-JSON"}'
    if raw:
        return status, body
    if not body:
        return None
    return json.loads(body) if body[:1] in (b'{', b'[') else body

def sql(query):
    pod = subprocess.check_output(['kubectl', '--context', 'k8s', '-n', 'supabase-prod', 'get', 'pods', '-l', 'cnpg.io/cluster=supabase-db,role=primary', '-o', 'jsonpath={.items[0].metadata.name}'], text=True)
    result = subprocess.run(['kubectl', '--context', 'k8s', '-n', 'supabase-prod', 'exec', '-i', pod, '-c', 'postgres', '--', 'psql', '-v', 'ON_ERROR_STOP=1', '-U', 'postgres', '-d', 'postgres', '-At'], input=query, text=True, capture_output=True)
    assert result.returncode == 0, 'Acceptance SQL failed; inspect protected database logs'
    return result.stdout.strip()

def cleanup():
    # Remove fixture foreign keys before deleting the disposable Auth users.
    sql('DROP TABLE IF EXISTS public.homelab_acceptance;')
    if STATE.exists():
        state = json.loads(STATE.read_text())
        bucket_status, _ = request('/storage/v1/bucket/acceptance-private', admin=True, raw=True, expected=(200, 400, 404))
        if bucket_status == 200:
            request('/storage/v1/object/acceptance-private', 'DELETE', {'prefixes': ['fixture.txt']}, admin=True)
            request('/storage/v1/bucket/acceptance-private', 'DELETE', admin=True)
        for user in state['users']:
            request('/auth/v1/admin/users/' + user['id'], 'DELETE', admin=True, expected=(200, 204, 404))
        STATE.unlink()
    print('PASS: disposable acceptance fixtures removed')

if '--cleanup' in sys.argv:
    cleanup()
    sys.exit()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def check_studio_sso(extra_headers=None):
    headers = {'Accept': 'text/html'}
    headers.update(extra_headers or {})
    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(urllib.request.Request(STUDIO + '/', headers=headers), timeout=15)
        raise AssertionError('Studio accessible without SSO')
    except urllib.error.HTTPError as response:
        assert response.code in (302, 303, 307, 401)
        target = response.headers.get('Location') or response.headers.get('X-Tinyauth-Location', '')
        assert target.startswith('https://login.l3b.cc.cd/')
        assert not response.headers.get('WWW-Authenticate'), 'Browser Basic-auth challenge remains'

check_studio_sso()
request('/rest/v1/homelab_acceptance', anonymous=True, expected=(401,))
basic = base64.b64encode((ENV['DASHBOARD_USERNAME'] + ':' + ENV['DASHBOARD_PASSWORD']).encode()).decode()
check_studio_sso({'Authorization': 'Basic ' + basic})
check_studio_sso({'Remote-User': 'admin', 'Remote-Email': 'iam.anuragvishwakarma@gmail.com', 'Remote-Groups': 'infrastructure-admins'})
request('/auth/v1/health')
jwks = request('/auth/v1/.well-known/jwks.json')
assert jwks['keys'] and all(key.get('kty') == 'EC' and 'd' not in key and 'k' not in key for key in jwks['keys']), 'Public JWKS contains secret key material'
request('/functions/v1/hello', anonymous=True, expected=(401,))
print('PASS: HTTPS, Studio SSO redirect/no Basic popup, spoof/Basic bypass denial and API authentication')

if STATE.exists():
    state = json.loads(STATE.read_text())
    assert len(request('/rest/v1/homelab_acceptance?select=*', admin=True)) == 2
    _, body = request('/storage/v1/object/acceptance-private/fixture.txt', admin=True, raw=True)
    assert body == b'Supabase persistent acceptance fixture\n'
    print('PASS: database rows and private Storage object persisted')
else:
    sql('''CREATE TABLE public.homelab_acceptance (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), owner uuid NOT NULL REFERENCES auth.users(id), message text NOT NULL);
ALTER TABLE public.homelab_acceptance ENABLE ROW LEVEL SECURITY;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.homelab_acceptance TO authenticated;
CREATE POLICY owner_only ON public.homelab_acceptance FOR ALL TO authenticated USING (owner = auth.uid()) WITH CHECK (owner = auth.uid());
ALTER PUBLICATION supabase_realtime ADD TABLE public.homelab_acceptance;
''')
    state = {'users': []}
    for number in range(2):
        email = f'acceptance-{secrets.token_hex(6)}@example.invalid'
        password = secrets.token_urlsafe(28)
        user = request('/auth/v1/admin/users', 'POST', {'email': email, 'password': password, 'email_confirm': True}, admin=True)
        state['users'].append({'id': user['id'], 'email': email, 'password': password})
    STATE.write_text(json.dumps(state))
    STATE.chmod(0o600)
    request('/storage/v1/bucket', 'POST', {'id': 'acceptance-private', 'name': 'acceptance-private', 'public': False}, admin=True)
    request('/storage/v1/object/acceptance-private/fixture.txt', 'POST', b'Supabase persistent acceptance fixture\n', admin=True, headers={'Content-Type': 'text/plain'})

tokens = []
for index, user in enumerate(state['users']):
    session = request('/auth/v1/token?grant_type=password', 'POST', {'email': user['email'], 'password': user['password']})
    token = session['access_token']
    assert json.loads(base64.urlsafe_b64decode(token.split('.')[0] + '=='))['alg'] == 'ES256'
    refreshed = request('/auth/v1/token?grant_type=refresh_token', 'POST', {'refresh_token': session['refresh_token']})
    token = refreshed['access_token']
    tokens.append(token)
    existing = request('/rest/v1/homelab_acceptance?select=*', user=token)
    if not existing:
        request('/rest/v1/homelab_acceptance', 'POST', {'owner': user['id'], 'message': f'acceptance-{index}'}, user=token)
    rows = request('/rest/v1/homelab_acceptance?select=*', user=token)
    assert len(rows) == 1 and rows[0]['owner'] == user['id']
    request('/rest/v1/homelab_acceptance?owner=eq.' + user['id'], 'PATCH', {'message': f'validated-{index}'}, user=token)
extra = request('/rest/v1/homelab_acceptance', 'POST', {'owner': state['users'][0]['id'], 'message': 'delete-probe'}, user=tokens[0], headers={'Prefer': 'return=representation'})
request('/rest/v1/homelab_acceptance?id=eq.' + extra[0]['id'], 'DELETE', user=tokens[0])
assert len(request('/rest/v1/homelab_acceptance?select=*', user=tokens[0])) == 1
assert request('/rest/v1/homelab_acceptance?select=*') == []
request('/rest/v1/homelab_acceptance', 'POST', {'owner': state['users'][1]['id'], 'message': 'deny cross-user write'}, user=tokens[0], expected=(403,))
print('PASS: ES256 Auth, token refresh, REST CRUD and two-user RLS isolation')

request('/storage/v1/object/acceptance-private/fixture.txt', anonymous=True, expected=(400, 401, 403))
request('/storage/v1/object/acceptance-private/fixture.txt', expected=(400, 401, 403))
_, body = request('/storage/v1/object/acceptance-private/fixture.txt', admin=True, raw=True)
assert body == b'Supabase persistent acceptance fixture\n'
signed = request('/storage/v1/object/sign/acceptance-private/fixture.txt', 'POST', {'expiresIn': 2}, admin=True)
url = signed.get('signedURL') or signed['signedUrl']
request('/storage/v1' + url, anonymous=True, raw=True)
time.sleep(4)
request('/storage/v1' + url, anonymous=True, expected=(400, 401, 403))
print('PASS: private Storage upload/read, access denial and signed URL expiry')

request('/functions/v1/hello', user=tokens[0], raw=True)
request('/functions/v1/hello', headers={'Authorization': 'Bearer invalid'}, expected=(401,))
print('PASS: authenticated Edge Function executes; invalid JWT rejected')

ws_url = BASE.replace('https://', 'wss://') + '/realtime/v1/websocket?apikey=' + ENV['SUPABASE_PUBLISHABLE_KEY'] + '&vsn=1.0.0'
def subscribe(token):
    ws = websocket.create_connection(ws_url, timeout=15)
    ws.send(json.dumps({'topic': 'realtime:acceptance', 'event': 'phx_join', 'ref': '1', 'payload': {
        'access_token': token,
        'config': {'broadcast': {'self': False}, 'presence': {'key': ''}, 'postgres_changes': [{'event': '*', 'schema': 'public', 'table': 'homelab_acceptance'}], 'private': False}}}))
    return ws

ws = subscribe(tokens[0])
deadline = time.monotonic() + 35
ready = False
while time.monotonic() < deadline:
    event = json.loads(ws.recv())
    if event.get('event') == 'system':
        assert event['payload']['status'] == 'ok', 'Realtime subscription rejected'
        ready = True
        break
assert ready, 'Realtime database subscription was not ready'
request('/rest/v1/homelab_acceptance?owner=eq.' + state['users'][0]['id'], 'PATCH', {'message': 'realtime-verified'}, user=tokens[0])
received = False
while time.monotonic() < deadline:
    event = json.loads(ws.recv())
    if event.get('event') == 'postgres_changes':
        assert event['payload']['data']['record']['message'] == 'realtime-verified'
        received = True
        break
assert received, 'Realtime database update was not received'
request('/rest/v1/homelab_acceptance?owner=eq.' + state['users'][1]['id'], 'PATCH', {'message': 'must-not-leak'}, user=tokens[1])
ws.settimeout(4)
try:
    while True:
        event = json.loads(ws.recv())
        assert event.get('event') != 'postgres_changes', 'Realtime cross-user data leak'
except websocket.WebSocketTimeoutException:
    pass
ws.close()
bad = subscribe('invalid')
event = json.loads(bad.recv())
assert event.get('payload', {}).get('status') == 'error', 'Realtime accepted invalid JWT'
bad.close()
print('PASS: Realtime WebSocket database update, RLS isolation and invalid JWT denial')

if '--keep' not in sys.argv:
    cleanup()
else:
    print('Fixtures retained securely for restart verification')
