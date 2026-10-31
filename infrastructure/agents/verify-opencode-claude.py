#!/usr/bin/env python3
"""Check native Claude Agent in an already-initialized OpenCode location.

A fresh location starts its MCP processes; avoid extra locations under memory
pressure. No model prompt, config mutation or expanded credentials displayed.
"""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, help='An already-initialized live location')
    parser.add_argument('--session', help='Optional known native smoke-test session')
    args = parser.parse_args()
    config = json.loads((Path.home() / '.config/opencode/opencode.json').read_text())
    packages = [p if isinstance(p, str) else p.get('package', '') for p in config.get('plugins', [])]
    assert not any(p.startswith('@openchamber/opencode-claude') for p in packages)
    service = json.loads((Path.home() / '.config/opencode/service.json').read_text())
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(('opencode:' + service['password']).encode()).decode(),
        'x-opencode-directory': urllib.parse.quote(str(Path(args.directory).resolve()), safe=''),
    }
    base = 'http://127.0.0.1:' + str(service['port'])

    def api(path):
        with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers), timeout=30) as r:
            return json.load(r)['data']

    pid = subprocess.check_output(['systemctl', '--user', 'show', 'opencode.service',
                                   '-p', 'MainPID', '--value'], text=True).strip()
    version = subprocess.check_output(['/proc/' + pid + '/exe', '--version'], text=True).strip()
    numbers = tuple(int(p) for p in version.removeprefix('opencode v').split('.')[:3])
    assert numbers >= (2, 2, 3), 'server lacks built-in Claude Agent'
    providers = api('/api/provider')
    assert any(p.get('id') == 'claude-agent' for p in providers)
    assert not any(p.get('id') == 'claude-code' for p in providers), 'legacy provider still loaded'
    models = [m for m in api('/api/model') if m.get('providerID') == 'claude-agent']
    assert models and any(m.get('id') == 'opus' for m in models)
    assert any(v.get('id') == 'xhigh' for m in models for v in m.get('variants', []))
    connections = api('/api/mcp')
    assert any(c.get('name') == 'openviking' for c in connections)
    for c in connections:
        state = c.get('status', {})
        state = state.get('status') if isinstance(state, dict) else state
        assert state == 'connected', 'MCP unavailable: ' + c.get('name', 'unknown')
    print('PASS:', version, 'native Claude Agent/model variants and', len(connections), 'live MCP connections')
    if args.session:
        messages = api('/api/session/' + urllib.parse.quote(args.session, safe='') + '/message')
        parts = [p for m in messages for p in m.get('content', []) if isinstance(p, dict)]
        assert any(p.get('type') == 'tool' and p.get('state', {}).get('status') == 'completed'
                   and any(c.get('text') == 'NATIVE_CLAUDE_TOOL_OK' for c in p.get('state', {}).get('content', []) if isinstance(c, dict)) for p in parts)
        assert any('NATIVE_CLAUDE_TOOL_OK' in p.get('text', '') for p in parts if p.get('type') == 'text')
        print('PASS: recorded native tool result and resumed response')
    print('No model prompt sent; no credentials or expanded configuration displayed.')


if __name__ == '__main__':
    main()
