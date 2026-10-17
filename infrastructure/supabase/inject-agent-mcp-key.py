#!/usr/bin/env python3
"""Mechanically inject/rotate the vault MCP key in three protected client files.

Public server entries are added with apply_patch first. Only the uniquely
located existing Authorization value is replaced; other configuration is kept.
No key in command arguments, stdout or Git. Run on dev as dev.
"""
import datetime
import json
import pathlib
import shutil
import subprocess
import tomllib
import yaml

repo = pathlib.Path(__file__).resolve().parents[2]
result = subprocess.run([str(repo / 'scripts/op-sa'), 'item', 'get', 'Supabase', '--vault', 'HomeLab', '--format', 'json'], capture_output=True, text=True, check=True)
fields = json.loads(result.stdout)['fields']
key = next(field['value'] for field in fields if field.get('id') == 'mcp-api-key' or field.get('label') == 'mcp-api-key')
assert key.startswith('sb_mcp_') and len(key) >= 45
auth = 'Bearer ' + key
paths = [pathlib.Path('/home/dev/.codex/config.toml'), pathlib.Path('/home/dev/.claude.json'), pathlib.Path('/home/dev/.hermes/config.yaml')]
updates = []
for path in paths:
    old = path.read_text()
    doc = tomllib.loads(old) if path.suffix == '.toml' else json.loads(old) if path.suffix == '.json' else yaml.safe_load(old)
    server = doc.get('mcp_servers', doc.get('mcpServers'))['supabase']
    assert server['url'] == 'https://sb.l3b.cc.cd/mcp'
    current = server.get('headers', server.get('http_headers'))['Authorization']
    if current == auth:
        continue
    assert current == '__SUPABASE_MCP_AUTH__' or current.startswith('Bearer sb_mcp_')
    assert old.count(current) == 1, 'Refusing ambiguous credential replacement'
    updates.append((path, old, old.replace(current, auth)))
if updates:
    root = pathlib.Path('/home/dev/.local/state/supabase-mcp-config-backups')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = root / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup.mkdir(mode=0o700)
    for index, (path, old, new) in enumerate(updates):
        assert path.read_text() == old, 'Configuration changed concurrently; retry safely'
        saved = backup / (str(index) + '-' + path.name)
        shutil.copy2(path, saved)
        saved.chmod(0o600)
        path.chmod(0o600)
        path.write_text(new)
        path.chmod(0o600)
    print('Updated', len(updates), 'protected client Authorization values; backup:', backup)
else:
    print('All three client keys already match the canonical vault key')
