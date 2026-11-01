#!/usr/bin/env python3
"""Read-only core acceptance checks. No fixtures, credential output or service changes."""
import argparse
import json
import socket
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path)
    parser.add_argument('--browser', action='store_true', help='Verify the actual authenticated browser session without reading credentials')
    args = parser.parse_args()
    result = {'checkedOn': '2026-11-02', 'node': 'l3b', 'checks': {}}
    checks = result['checks']

    def run(*command):
        return subprocess.run(command, capture_output=True, text=True,
                              check=True, timeout=30).stdout.strip()

    names = run('docker', 'ps', '--format', '{{.Names}}').splitlines()
    containers = json.loads(run('docker', 'inspect', *names))
    published = {item['Name'].lstrip('/'): sorted((item['HostConfig'].get('PortBindings') or {}))
                 for item in containers if item['HostConfig'].get('PortBindings')}
    assert published == {'adguard': ['53/udp'], 'caddy': ['443/tcp', '443/udp']}, 'Unexpected Docker host ports'
    checks['dockerPublishedPortsExact'] = published
    by_name = {item['Name'].lstrip('/'): item for item in containers}
    for name in ['portainer', 'adguard', 'unbound', 'caddy', 'pocket-id', 'tinyauth', 'homepage']:
        assert name in by_name and by_name[name]['State']['Running'], name + ' is not running'
    for name in ['unbound', 'pocket-id', 'tinyauth', 'homepage']:
        assert by_name[name]['State'].get('Health', {}).get('Status') == 'healthy', name + ' is not healthy'
    for name in ['adguard', 'unbound', 'caddy', 'pocket-id', 'tinyauth']:
        assert by_name[name]['HostConfig']['ReadonlyRootfs'], name + ' root filesystem is not read-only'
    assert 'opencode' not in by_name and 'opencode-host-proxy' not in by_name, 'Unwanted agent duplicate/proxy'
    assert 'hermes' not in by_name, 'Hermes must remain stopped until core acceptance'
    checks['coreContainersRunningAndHardened'] = True
    checks['duplicateAgentAndProxyAbsent'] = True
    checks['hermesDeferred'] = True
    assert not any('tailscale' in name.lower() for name in by_name)
    assert subprocess.run(['systemctl', 'is-active', '--quiet', 'tailscaled'],
                          capture_output=True, timeout=10).returncode != 0
    checks['tailscaleNotRunning'] = True

    data_uuid = run('findmnt', '-n', '-o', 'UUID', '-M', '/data')
    backup_uuid = run('findmnt', '-n', '-o', 'UUID', '-M', '/mnt/HOMELAB_BACKUP')
    assert data_uuid == 'f3c5b7ac-b0c8-463f-a91a-45e880ebae21'
    assert backup_uuid == 'c05e9f2d-a64e-4012-9407-a3dc94475dbb'
    assert run('findmnt', '-n', '-o', 'UUID', '-T', '/var/lib/docker') == run('findmnt', '-n', '-o', 'UUID', '-M', '/')
    assert run('findmnt', '-n', '-o', 'UUID', '-T', '/var/lib/containerd') == run('findmnt', '-n', '-o', 'UUID', '-M', '/')
    checks['storagePlacementAndMountedBackupIdentity'] = True

    answer = run('dig', '@10.1.1.10', 'portainer.l3b.cc.cd', '+notcp', '+short')
    assert answer.splitlines()[-1] == '10.1.1.10', 'Wrong private DNS answer'
    valid = run('dig', '@10.1.1.10', 'cloudflare.com', '+notcp', '+dnssec', '+noall', '+comments')
    invalid = run('dig', '@10.1.1.10', 'dnssec-failed.org', '+notcp', '+dnssec', '+noall', '+comments')
    assert 'status: NOERROR' in valid and ' ad;' in valid, 'Validated DNSSEC answer missing'
    assert 'status: SERVFAIL' in invalid, 'Broken DNSSEC domain was accepted'
    checks['udpDnsPrivateAnswerAndDnssec'] = True
    for port in [53, 80, 9000, 8931, 4098]:
        with socket.socket() as sock:
            sock.settimeout(2)
            assert sock.connect_ex(('10.1.1.10', port)) != 0, f'Unexpected host TCP listener: {port}'
    checks['noDnsTcpHttpOrManagementHostPorts'] = True

    def get(url, headers=None):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=15) as response:
                return response.status, response.read(), response.headers
        except urllib.error.HTTPError as error:
            return error.code, b'', error.headers

    status, data, headers = get('https://portainer.l3b.cc.cd/api/status')
    assert status == 200 and json.loads(data)['Version'] == '2.45.3'
    status, data, _ = get('https://auth.l3b.cc.cd/.well-known/openid-configuration')
    assert status == 200
    discovery = json.loads(data)
    assert discovery['issuer'] == 'https://auth.l3b.cc.cd'
    assert discovery['jwks_uri'].startswith('https://auth.l3b.cc.cd/')
    status, data, _ = get(discovery['jwks_uri'])
    assert status == 200 and json.loads(data)['keys']
    assert get('https://login.l3b.cc.cd/')[0] == 200
    for spoofed in [False, True]:
        headers = {'Accept': 'application/json'}
        if spoofed:
            headers.update({'Remote-User': 'admin', 'Remote-Groups': 'infrastructure-admins',
                            'X-Forwarded-For': '10.1.2.3'})
        assert get('https://dns.l3b.cc.cd/', headers)[0] == 401, 'DNS dashboard auth bypass'
    checks['httpsPortainerAndOidcDiscovery'] = True
    checks['dnsDashboardForwardAuthAndSpoofRejection'] = True
    context = ssl.create_default_context()
    context.set_alpn_protocols(['h2', 'http/1.1'])
    with socket.create_connection(('10.1.1.10', 443), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname='portainer.l3b.cc.cd') as tls:
            assert tls.selected_alpn_protocol() == 'h2'
    checks['trustedTlsAndHttp2'] = True
    if args.browser:
        code = r'''const {chromium}=require('/app/node_modules/playwright-core');
(async()=>{const b=await chromium.connectOverCDP('http://127.0.0.1:9222');const c=b.contexts()[0];const r=await c.request.get('https://portainer.l3b.cc.cd/api/users/me');if(r.status()!==200)throw Error('Not signed in');const u=await r.json();if(u.Role!==1)throw Error('Not administrator');const s=(await c.cookies('https://portainer.l3b.cc.cd')).find(x=>x.name==='portainer_api_key');if(!s||!s.secure||!s.httpOnly||s.sameSite!=='Strict')throw Error('Cookie policy');console.log('PASS');process.exit(0)})().catch(()=>{console.error('Authenticated browser acceptance failed');process.exit(1)});'''
        assert run('docker', 'exec', 'playwright-mcp', 'node', '-e', code) == 'PASS'
        checks['actualPortainerBrowserAdminSessionAndSecureCookie'] = True
    checks['wireguardHostServicePreserved'] = run('systemctl', 'is-active', 'wg-quick@wg0') == 'active'
    assert checks['wireguardHostServicePreserved']
    result['limits'] = [
        'UDP-only client DNS intentionally has no TCP fallback for truncated replies',
        'Published UDP443/listener is checked; independent end-to-end HTTP3 test not performed',
        'Human passkey/OIDC completion and remote client application access need owner acceptance',
        'No reboot, Docker-daemon restart, durability drill or current-node backup created',
    ]
    result['secrets'] = 'No credentials, key contents or expanded agent configuration displayed'
    text = json.dumps(result, indent=2) + '\n'
    if args.save:
        args.save.write_text(text)
    print(text)


if __name__ == '__main__':
    main()
