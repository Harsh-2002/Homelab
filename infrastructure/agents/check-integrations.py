#!/usr/bin/env python3
"""Read-only global MCP parity check. Never print credentials or full configs."""
import json
from pathlib import Path
import sys
import tomllib

import yaml


def load():
    home = Path.home()
    codex = tomllib.loads((home / '.codex/config.toml').read_text())
    claude = json.loads((home / '.claude.json').read_text())
    hermes = yaml.safe_load((home / '.hermes/config.yaml').read_text())
    opencode = json.loads((home / '.config/opencode/opencode.json').read_text())
    return {
        'Codex': codex.get('mcp_servers', {}),
        'Claude Code': claude.get('mcpServers', {}),
        'Hermes': hermes.get('mcp_servers', {}),
        'OpenCode': opencode.get('mcp', {}).get('servers', {}),
    }, opencode


def normalized(entry, client):
    if entry.get('disabled') or entry.get('enabled') is False:
        return ('disabled',)
    if 'url' in entry:
        return ('remote', entry['url'], entry.get('headers', entry.get('http_headers', {})))
    command = entry.get('command', [])
    argv = list(command) if isinstance(command, list) else [command, *entry.get('args', [])]
    # Hermes intentionally resolves this credential through its own protected env.
    # Compare command structure without rendering or equating opaque credentials.
    if '--api-key' in argv:
        pos = argv.index('--api-key') + 1
        if pos < len(argv):
            argv[pos] = '<credential>'
    return ('local', argv)


def main():
    clients, opencode = load()
    required = {'playwright', 'chrome-devtools', 'context7', 'shadcn',
                'orva', 'supabase', 'nivra', 'rea', 'olx'}
    # Any newly added standalone integration must propagate to all four clients.
    names = required | set().union(*(set(items) for items in clients.values()))
    names.discard('openviking')  # Native plugins/provider, not duplicate MCP entries.
    failures = []
    for name in sorted(names):
        missing = [client for client, servers in clients.items() if name not in servers]
        if missing:
            failures.append(f'{name}: missing in {", ".join(missing)}')
            continue
        baseline = normalized(clients['Codex'][name], 'Codex')
        mismatches = [client for client, servers in clients.items()
                      if normalized(servers[name], client) != baseline]
        if mismatches:
            failures.append(f'{name}: configuration drift in {", ".join(mismatches)}')
        else:
            print(f'{name}: aligned across four agents')
    packages = opencode.get('plugins', [])
    if not any('@openviking/opencode-plugin' in
               (p if isinstance(p, str) else p.get('package', '')) for p in packages):
        failures.append('OpenCode: official OpenViking plugin missing')
    if clients['OpenCode'].get('olx', {}).get('protocol') != '2026-07-28':
        failures.append('OpenCode: OLX protocol revision missing')
    config = Path.home() / '.config/opencode/opencode.json'
    if config.stat().st_mode & 0o077:
        failures.append('OpenCode: credential-bearing config is not private')
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('PASS: shared MCP parity and OpenCode memory registration; no secrets displayed')
    print('This checks configuration, not live connectivity or automatic memory capture.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError):
        print('FAIL: unable to validate an agent configuration; inspect locally without printing secrets', file=sys.stderr)
        sys.exit(1)
