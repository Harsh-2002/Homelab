#!/usr/bin/env python3
"""Enable the real Chrome DevTools MCP after its Docker browser is available."""
import json
from pathlib import Path
import yaml

flags = ['-y', 'chrome-devtools-mcp@1.12.0', '--no-usage-statistics']
path = Path('/home/dev/.config/opencode/opencode.json')
data = json.loads(path.read_text())
data['mcp']['servers']['chrome-devtools'] = {
    'type': 'local', 'command': ['sg', 'docker', '-c',
        'exec docker exec -i playwright npx ' + ' '.join(flags) +
        ' --browserUrl=http://127.0.0.1:9222'],
    'disabled': False, 'timeout': {'startup': 90000, 'catalog': 60000}}
path.write_text(json.dumps(data, indent=2) + '\n')
path.chmod(0o600)
path = Path('/data/apps/hermes/home/config.yaml')
data = yaml.safe_load(path.read_text())
data['mcp_servers']['chrome-devtools'] = {
    'command': 'python3',
    'args': ['/workspace/Homelab/infrastructure/l3b/chrome-devtools-client.py'],
    'enabled': True}
path.write_text(yaml.safe_dump(data, sort_keys=False))
path.chmod(0o600)
print('Host OpenCode and Hermes DevTools attach to the same shared Docker browser.')
