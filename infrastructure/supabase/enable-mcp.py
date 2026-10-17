#!/usr/bin/env python3
"""Enable native MCP for the trusted Caddy peer only; preserve /api/mcp deny.

Run on the VM as root. Generates a dedicated proxy key once, never prints it.
Gateway restart is a separate explicit step. Refuses unknown upstream changes.
"""
import pathlib
import secrets
import shutil
import sys

root = pathlib.Path(sys.argv[1])
env = root / '.env'
text = env.read_text()
if '\nSUPABASE_MCP_API_KEY=' not in '\n' + text:
    text = text.rstrip() + '\nSUPABASE_MCP_API_KEY=sb_mcp_' + secrets.token_urlsafe(32) + '\n'
    env.write_text(text)
    env.chmod(0o600)
source = root / 'volumes/api/envoy/lds.template.yaml'
template = source.read_text()
start = template.index('                      - match:\n                          prefix: /mcp\n')
end = template.index('\n                      - match:\n                          prefix: /\n', start)
route = template[start:end]
marker = '                            # Homelab: only Caddy may call native MCP.\n'
if marker not in route:
    expected = root / '.upstream/docker/volumes/api/envoy/lds.template.yaml'
    baseline = expected.read_text()
    if template != baseline:
        raise SystemExit('Gateway template differs from pinned upstream; review instead of broad patch')
    deny = route.index('                            # Block access to /mcp by default\n')
    policy = marker + '''                            rbac:
                              rules:
                                action: ALLOW
                                policies:
                                  caddy_only:
                                    permissions:
                                      - any: true
                                    principals:
                                      - direct_remote_ip:
                                          address_prefix: 10.1.1.3
                                          prefix_len: 32
'''
    backup = source.with_name('lds.template.yaml.before-mcp')
    if not backup.exists():
        shutil.copy2(source, backup)
    source.write_text(template[:start] + route[:deny] + policy + template[end:])
    source.chmod(0o644)
print('Dedicated MCP key present; native /mcp restricted to Caddy10.1.1.3; /api/mcp unchanged')
