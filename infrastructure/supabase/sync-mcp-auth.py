#!/usr/bin/env python3
"""Copy only the dedicated MCP key to Caddy over SSH stdin, never argv/logs."""
import shlex
import subprocess

raw = subprocess.check_output(['ssh', 'supabase', 'sudo cat /srv/supabase/.env'], text=True)
matches = [line.split('=', 1)[1] for line in raw.splitlines() if line.startswith('SUPABASE_MCP_API_KEY=')]
assert len(matches) == 1
key = shlex.split(matches[0])[0]
assert key.startswith('sb_mcp_') and len(key) >= 45
remote = '''import pathlib, re, sys
path = pathlib.Path('/etc/caddy/cloudflare.env')
text = path.read_text()
value = sys.stdin.read().strip()
assert re.fullmatch(r'sb_mcp_[A-Za-z0-9_-]{43,}', value)
line = "SUPABASE_MCP_API_KEY='" + value + "'"
pattern = r'^SUPABASE_MCP_API_KEY=.*$'
text = re.sub(pattern, lambda _: line, text, flags=re.M) if re.search(pattern, text, re.M) else text.rstrip() + '\\n' + line + '\\n'
path.write_text(text)
path.chmod(0o600)
'''
subprocess.run(['ssh', 'proxy', 'python3 -c ' + shlex.quote(remote)], input=key, text=True, check=True)
print('Synced protected MCP key to Caddy; no secret displayed')
