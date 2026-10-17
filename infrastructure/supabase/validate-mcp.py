#!/usr/bin/env python3
"""From dev: validate native MCP through the private bearer-key Caddy boundary."""
import json
import shlex
import subprocess
import urllib.error
import urllib.request

URL = 'https://supabase.l3b.cc.cd/mcp'
raw = subprocess.check_output(['ssh', 'supabase', 'sudo cat /srv/supabase/.env'], text=True)
key = next(shlex.split(line.split('=', 1)[1])[0] for line in raw.splitlines() if line.startswith('SUPABASE_MCP_API_KEY='))

def call(method, params=None, token=key, endpoint=URL):
    body = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        body['params'] = params
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    if token is not None:
        headers['Authorization'] = 'Bearer ' + token
    try:
        with urllib.request.urlopen(urllib.request.Request(endpoint, json.dumps(body).encode(), headers), timeout=30) as response:
            return response.status, json.load(response), response.headers
    except urllib.error.HTTPError as error:
        return error.code, None, error.headers

for token in (None, 'wrong-key'):
    status, _, headers = call('tools/list', token=token)
    assert status == 401 and not headers.get('Location') and headers.get('WWW-Authenticate', '').startswith('Bearer')
print('PASS: missing/invalid MCP keys rejected without browser SSO or Basic-auth redirect')
status, init, _ = call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'homelab-validation', 'version': '1.0'}})
assert status == 200 and 'result' in init, f'MCP initialization failed HTTP {status}'
print('PASS: MCP initialize, protocol', init['result']['protocolVersion'])
status, listing, _ = call('tools/list')
assert status == 200 and listing.get('result', {}).get('tools')
tools = listing['result']['tools']
print('PASS: tools/list returned', len(tools), 'tools:', ', '.join(tool['name'] for tool in tools))
status, result, _ = call('tools/call', {'name': 'execute_sql', 'arguments': {'query': 'select current_database() as database, 1 as mcp_health'}})
assert status == 200 and 'result' in result and not result['result'].get('isError'), 'Read-only SQL tool invocation failed'
assert 'mcp_health' in json.dumps(result['result'])
print('PASS: execute_sql ran a read-only health query against the real database')
status, result, _ = call('tools/call', {'name': 'execute_sql', 'arguments': {'query': 'create temporary table homelab_mcp_validation (value integer) on commit drop; insert into homelab_mcp_validation values (1); select value from homelab_mcp_validation;'}})
assert status == 200 and 'result' in result and not result['result'].get('isError'), 'Temporary SQL write test failed'
print('PASS: agent SQL writes work using a temporary table; no application data changed')
status, _, _ = call('tools/list', endpoint='https://supabase.l3b.cc.cd/api/mcp')
assert status in (401, 403), 'Direct /api/mcp alias not denied'
print('PASS: alternate /api/mcp route remains protected/blocked')
