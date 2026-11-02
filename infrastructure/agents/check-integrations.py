#!/usr/bin/env python3
"""Read-only global MCP and shared-skill check. Never print credentials or full configs."""
import json
import hashlib
from pathlib import Path
import shutil
import sys
import tomllib
import subprocess

import yaml


def single_node():
    """Owner-scoped l3b check; never create excluded Codex/Claude configs."""
    home = Path.home()
    op_path = home / '.config/opencode/opencode.json'
    hermes_path = home / '.hermes/config.yaml'
    opencode = json.loads(op_path.read_text())
    hermes = yaml.safe_load(hermes_path.read_text())
    clients = {'OpenCode': opencode['mcp']['servers'], 'Hermes': hermes['mcp_servers']}
    expected = {'context7', 'shadcn', 'rea', 'nivra', 'orva', 'olx'}
    browser_mcps = {'playwright', 'chrome-devtools'}
    failures = []
    names = set().union(*(set(servers) for servers in clients.values()))
    for name in sorted(names):
        for client, servers in clients.items():
            entry = servers.get(name)
            if entry is None:
                if name not in browser_mcps:
                    failures.append(f'{client}: missing {name}')
                continue
            enabled = not entry.get('disabled', False) and entry.get('enabled', True)
            if name in browser_mcps:
                if enabled:
                    failures.append(f'{client}: browser MCP {name} must be removed or disabled')
                continue
            if enabled != (name in expected):
                failures.append(f'{client}: unexpected enabled state for {name}')
        print(f'{name}: scoped presence/enabled-state checked')
    if not shutil.which('playwright-cli'):
        failures.append('Playwright CLI is not installed')
    if not (home / '.agents/skills/playwright-cli/SKILL.md').is_file():
        failures.append('Playwright CLI official skill missing')
    print('Playwright CLI: installed and official skill present; browser MCPs forbidden')
    for path in [op_path, hermes_path]:
        if path.stat().st_mode & 0o077:
            failures.append('Credential-bearing agent config is not private')
    if hermes.get('memory', {}).get('provider') != 'openviking':
        failures.append('Hermes: OpenViking memory provider is not active')
    memory_plugins = [item for item in opencode.get('plugins', [])
                      if 'openviking' in (item if isinstance(item, str) else item.get('package', ''))]
    if '--memory' in sys.argv and len(memory_plugins) != 1:
        failures.append('OpenCode: expected exactly one official OpenViking plugin')
    if memory_plugins:
        memory_path = home / '.openviking/ovcli.conf'
        memory_config = json.loads(memory_path.read_text())
        if memory_path.stat().st_mode & 0o077:
            failures.append('OpenViking client config is not private')
        if memory_config.get('url') != 'https://memory.l3b.cc.cd' or not memory_config.get('api_key'):
            failures.append('OpenViking client endpoint/account key is not configured')
        if 'openviking' in clients['OpenCode']:
            failures.append('OpenCode: duplicate configured OpenViking MCP; use the plugin-owned server')
        skill_root = home / '.local/share/openviking-plugin/node_modules/@openviking/opencode-plugin/skills'
        for name in ['openviking-memory', 'openviking-skills', 'ov-experience-memory']:
            if not (skill_root / name / 'SKILL.md').is_file():
                failures.append('OpenCode: bundled memory skill missing: ' + name)
        if str(skill_root) not in opencode.get('skills', []):
            failures.append('OpenCode: bundled memory skills directory not configured')
        print('OpenViking: official plugin, private account config and three bundled skills checked')
    claude_path = home / '.claude.json'
    if claude_path.is_file():
        claude = json.loads(claude_path.read_text()).get('mcpServers', {})
        ov = claude.get('openviking', {})
        if ov.get('url') != 'https://memory.l3b.cc.cd/mcp' or not (ov.get('headers') or {}).get('Authorization'):
            failures.append('Claude Code: OpenViking MCP missing or incomplete')
        ox = claude.get('olx', {})
        if '--network' not in ox.get('args', []) or 'ghcr.io/harsh-2002/olx-mcp:latest' not in ox.get('args', []):
            failures.append('Claude Code: OLX MCP missing or not on the l3b network')
        print('Claude Code: OpenViking and OLX MCP entries checked')
    if not (home / '.agents/skills/herdr-control/SKILL.md').is_file():
        failures.append('OpenCode: shared Herdr control skill missing')
    if not (home / '.hermes/memories').is_dir():
        failures.append('Hermes: local memories missing')
    for failure in failures:
        print('FAIL: ' + failure, file=sys.stderr)
    if failures:
        return 1
    print('PASS: l3b OpenCode/Hermes restore scope; excluded clients untouched.')
    print('This checks configuration, not live connectivity, auth or model execution.')
    return 0


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
    required = {'context7', 'shadcn', 'orva', 'nivra', 'rea', 'olx'}
    # Browser automation is Playwright CLI + its official skill only; no browser MCPs.
    names = required | set().union(*(set(items) for items in clients.values()))
    names.discard('openviking')
    names.discard('playwright')
    names.discard('chrome-devtools')
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
    if not shutil.which('playwright-cli'):
        failures.append('Playwright CLI is not installed')
    if not (Path.home() / '.agents/skills/playwright-cli/SKILL.md').is_file():
        failures.append('Playwright CLI official skill missing')
    packages = opencode.get('plugins', [])
    if not any('@openviking/opencode-plugin' in
               (p if isinstance(p, str) else p.get('package', '')) for p in packages):
        failures.append('OpenCode: official OpenViking plugin missing')
    if clients['OpenCode'].get('olx', {}).get('protocol') != '2026-07-28':
        failures.append('OpenCode: OLX protocol revision missing')
    config = Path.home() / '.config/opencode/opencode.json'
    if config.stat().st_mode & 0o077:
        failures.append('OpenCode: credential-bearing config is not private')
    skill = Path.home() / '.agents/skills/herdr-control/SKILL.md'
    try:
        expected = skill.read_bytes()
        for client, root in [('Codex', '.codex/skills'), ('Claude Code', '.claude/skills'),
                             ('Hermes', '.hermes/skills')]:
            if (Path.home() / root / 'herdr-control/SKILL.md').read_bytes() != expected:
                failures.append(f'{client}: Herdr control skill drift')
        roots = opencode.get('skills', [])
        if str(Path.home() / '.agents/skills') not in roots:
            failures.append('OpenCode: shared Herdr skill root absent')
        result = subprocess.run(['herdr', 'integration', 'status'], capture_output=True,
                                text=True, timeout=10, check=False)
        if result.returncode or any(not any(line.startswith(client + ': current ')
            for line in result.stdout.splitlines()) for client in ('codex', 'claude', 'hermes', 'opencode')):
            failures.append('Herdr: one or more native agent integrations absent or outdated')
        else:
            print('herdr: native integrations current; shared control skill aligned across four agents')
    except (OSError, subprocess.TimeoutExpired):
        failures.append('Herdr: unable to validate local integrations/control skill')
    try:
        reference = (Path.home() / '.agents/skills/excalidraw-local/SKILL.md').read_bytes()
        for root in ('.codex/skills', '.claude/skills', '.hermes/skills'):
            if (Path.home() / root / 'excalidraw-local/SKILL.md').read_bytes() != reference:
                failures.append('Excalidraw: shared local skill drift')
        result = subprocess.run(['excalidraw', '--version'], capture_output=True,
                                text=True, timeout=10, check=False)
        if result.returncode:
            failures.append('Excalidraw: CLI version check failed')
        else:
            print('excalidraw: official CLI available; shared skill aligned across four agents')
    except (OSError, subprocess.TimeoutExpired):
        failures.append('Excalidraw: CLI or shared skill unavailable')
    try:
        manifest = json.loads((Path(__file__).with_name('beautiful-rust.lock.json')).read_text())
        expected_names = {'rust-best-practices', 'rust-review', 'rust-port'}
        if set(manifest['skills']) != expected_names:
            failures.append('BeautifulRust: incomplete skill manifest')
        for name, files in manifest['skills'].items():
            for root in ('.agents/skills', '.codex/skills', '.claude/skills', '.hermes/skills'):
                directory = Path.home() / root / name
                actual = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in directory.rglob('*') if p.is_file()}
                if actual != files:
                    failures.append(f'BeautifulRust: content drift in {root}/{name}')
        assets = Path.home() / '.local/share/beautiful-rust' / manifest['revision']
        for name, digest in manifest['lintFiles'].items():
            if hashlib.sha256((assets / name).read_bytes()).hexdigest() != digest:
                failures.append(f'BeautifulRust: reference asset drift in {name}')
        if str(Path.home() / '.agents/skills') not in opencode.get('skills', []):
            failures.append('BeautifulRust: OpenCode shared skill root absent')
        print('beautiful-rust: three complete skills and reference assets checked across four agents')
    except (OSError, ValueError, KeyError):
        failures.append('BeautifulRust: missing skill, reference asset or install manifest')
    try:
        packages = [p if isinstance(p, str) else p.get('package', '')
                    for p in opencode.get('plugins', [])]
        if any(p.startswith('@openchamber/opencode-claude') for p in packages):
            failures.append('OpenCode Claude: retired external plugin is configured')
        selections = [opencode.get('model', '')] + [
            a.get('model', '') for a in opencode.get('agents', {}).values()]
        if any(isinstance(m, str) and m.startswith('claude-code/') for m in selections):
            failures.append('OpenCode Claude: stale external-provider model default')
        dropin = Path.home() / '.config/systemd/user/opencode.service.d/claude-sdk.conf'
        if dropin.exists():
            failures.append('OpenCode Claude: retired SDK environment drop-in remains')
        print('opencode-claude: legacy startup/defaults absent; native Claude Agent verified separately')
    except (OSError, ValueError, KeyError):
        failures.append('OpenCode Claude: unable to validate retirement state')
    for failure in failures:
        print(f'FAIL: {failure}', file=sys.stderr)
    if failures:
        return 1
    print('PASS: shared MCP parity and OpenCode memory registration; no secrets displayed')
    print('This checks configuration, not live connectivity or automatic memory capture.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(single_node() if '--single-node' in sys.argv else main())
    except (OSError, ValueError, KeyError, TypeError):
        print('FAIL: unable to validate an agent configuration; inspect locally without printing secrets', file=sys.stderr)
        sys.exit(1)
