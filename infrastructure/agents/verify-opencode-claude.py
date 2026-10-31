#!/usr/bin/env python3
"""Read-only Claude SDK integration checks; never print expanded configs or credentials."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', help='Optional known smoke-test session ID to verify recorded tool output')
    args = parser.parse_args()
    config = json.loads((Path.home() / '.config/opencode/opencode.json').read_text())
    packages = [p if isinstance(p, str) else p.get('package', '') for p in config.get('plugins', [])]
    if not any(p.startswith('@openchamber/opencode-claude') for p in packages):
        print('Legacy plugin retired from startup configuration. Native Claude Agent migration pending OpenCode >=2.2.3.')
        print('No live model discovery, location initialization or MCP startup performed.')
        return
    service = json.loads((Path.home() / '.config/opencode/service.json').read_text())
    base = 'http://127.0.0.1:' + str(service['port'])
    authorization = 'Basic ' + base64.b64encode(('opencode:' + service['password']).encode()).decode()

    def api(path):
        request = urllib.request.Request(base + path, headers={'Authorization': authorization})
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response).get('data')

    # Initializing a location loads plugins. Model listing makes no completion request.
    warmup = subprocess.run(['opencode', 'models'], capture_output=True, text=True, timeout=45)
    if warmup.returncode:
        raise SystemExit('FAIL: native OpenCode model discovery')
    providers = api('/api/provider')
    provider = next(p for p in providers if p.get('id') == 'claude-code')
    proxy = provider['settings']['baseURL']
    assert urllib.parse.urlparse(proxy).hostname == '127.0.0.1', 'proxy must remain loopback-only'
    with urllib.request.urlopen(proxy.removesuffix('/v1') + '/health', timeout=10) as response:
        assert response.status == 200
    try:
        urllib.request.urlopen(urllib.request.Request(proxy + '/models', headers={'Origin': 'https://example.invalid'}), timeout=10)
    except urllib.error.HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError('browser-origin request unexpectedly accepted')
    model = 'claude-opus-5-5[1m]'
    entry = next(m for m in api('/api/model') if m.get('providerID') == 'claude-code' and m.get('id') == model)
    assert any(v.get('id') == 'xhigh' for v in entry.get('variants', []))
    assert entry['limit']['context'] == 1000000
    agents = api('/api/agent')
    assert {'build', 'plan'} <= {a.get('id') for a in agents}
    for agent in agents:
        if agent.get('id') in {'build', 'plan'}:
            selection = agent.get('model', {})
            assert (selection.get('providerID'), selection.get('id'), selection.get('variant')) == ('claude-code', model, 'xhigh')
    connections = api('/api/mcp')
    assert isinstance(connections, list)
    for connection in connections:
        state = connection.get('status', {})
        state = state.get('status') if isinstance(state, dict) else state
        assert state == 'connected', 'MCP connection unavailable: ' + connection.get('name', 'unknown')
    assert any(c.get('name') == 'openviking' for c in connections)
    print('PASS: Claude provider/model/xhigh agents, loopback health, browser-origin rejection and existing MCP connections')
    if args.session:
        messages = api('/api/session/' + urllib.parse.quote(args.session, safe='') + '/message')
        tools = [part for message in messages for part in message.get('content', [])
                 if isinstance(part, dict) and part.get('type') == 'tool']
        assert any(t.get('state', {}).get('status') == 'completed' and
                   any('CLAUDE_SDK_TOOL_OK' in part.get('text', '')
                       for part in t.get('state', {}).get('content', []) if isinstance(part, dict))
                   for t in tools)
        print('PASS: recorded smoke-test tool completed with expected actual output')
    print('No credentials or expanded configuration displayed. This check sends no model prompt.')


if __name__ == '__main__':
    main()
