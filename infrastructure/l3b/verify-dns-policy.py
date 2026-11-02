#!/usr/bin/env python3
"""Verify internal DNS and private routing, including a temporary untrusted source.

Run as root. The reserved test address is removed in finally; no public service,
DNS record, container, listener or credential is created by these checks.
"""
import json
import socket
import ssl
import subprocess
from pathlib import Path

import yaml


def main():
    def run(*command):
        return subprocess.check_output(command, text=True, timeout=60)

    assert json.loads(Path('/etc/docker/daemon.json').read_text())['dns'] == ['10.1.1.10']
    host = Path('/etc/resolv.conf')
    assert host.is_symlink() and host.resolve() == Path('/run/systemd/resolve/resolv.conf')
    config = Path('/etc/systemd/network/10-eno1.network').read_text()
    assert 'DNS=10.1.1.10' in config and 'Name=eno1' in config
    status = run('networkctl', 'status', 'eno1', '--no-pager')
    assert '/etc/systemd/network/10-eno1.network' in status and 'configured' in status
    assert run('resolvectl', 'dns', 'eno1').strip().endswith('10.1.1.10')
    for service in ['systemd-networkd', 'systemd-resolved']:
        run('systemctl', 'is-enabled', service)
        run('systemctl', 'is-active', service)
    for package in ['ifupdown', 'resolvconf', 'netplan.io']:
        installed = subprocess.run(['dpkg-query', '-W', '-f=${Status}', package], capture_output=True, text=True)
        assert 'install ok installed' not in installed.stdout
    links = run('networkctl', 'list', '--no-legend', '--no-pager')
    for line in links.splitlines():
        if ' wg0 ' in line or ' br-' in line:
            assert 'unmanaged' in line
    assert not any(ip in run('ss', '-H', '-lunt') for ip in ['127.0.0.53:53', '127.0.0.54:53'])
    assert [s for s in Path('/etc/resolv.conf').read_text().splitlines()
            if s.startswith('nameserver')] == ['nameserver 10.1.1.10']
    containers = json.loads(run('docker', 'inspect', *run('docker', 'ps', '-q').split()))
    for c in containers:
        resolver = Path(c['ResolvConfPath']).read_text()
        assert 'nameserver 127.0.0.11' in resolver
        assert any('ExtServers:' in s and '10.1.1.10' in s for s in resolver.splitlines())
        assert not c['HostConfig'].get('Dns') or c['HostConfig']['Dns'] == ['10.1.1.10']
    config = yaml.safe_load(Path('/data/apps/adguard/conf/AdGuardHome.yaml').read_text())
    assert config['dns']['upstream_dns'] == ['unbound:5335']
    assert not config['dns']['fallback_dns']
    assert set(config['dns']['allowed_clients']) == {'127.0.0.0/8', '10.1.1.0/24', '10.1.2.0/24', '10.1.3.0/24'}
    state = json.loads(Path('/etc/wireguard/l3b.json').read_text())
    assert state['dns'] == '10.1.1.10'
    for name in state['peers']:
        lines = Path('/etc/wireguard/clients', name + '.conf').read_text().splitlines()
        assert 'DNS = 10.1.1.10' in lines
        assert 'AllowedIPs = 10.1.1.0/24, 10.1.2.0/24' in lines
    run('wg.sh', 'verify')
    for name in ['dns-policy-check.l3b.cc.cd', 'oc.l3b.cc.cd']:
        assert '10.1.1.10' in run('dig', '@10.1.1.10', name, 'A', '+short')
    assert run('dig', '@10.1.1.10', 'example.com', 'A', '+short').strip()


    # Direct bridge connection avoids local published-port proxy source rewriting.
    caddy = next(c for c in containers if c['Name'] == '/caddy')
    target = caddy['NetworkSettings']['Networks']['l3b']['IPAddress']
    source = '198.18.0.2'
    addresses = json.loads(run('ip', '-j', 'address'))
    assert not any(a.get('local') == source for device in addresses for a in device['addr_info'])
    run('ip', 'address', 'add', source + '/32', 'dev', 'lo')
    try:
        for host in ['oc.l3b.cc.cd', 'dns.l3b.cc.cd', 'auth.l3b.cc.cd',
                     'portainer.l3b.cc.cd', 'memory.l3b.cc.cd', 'l3b.cc.cd',
                     'notes.l3b.cc.cd', 'pin.l3b.cc.cd', 'photos.l3b.cc.cd',
                     'drive.l3b.cc.cd', 'orva.l3b.cc.cd']:
            connection = socket.create_connection((target, 443), timeout=15, source_address=(source, 0))
            with ssl.create_default_context().wrap_socket(connection, server_hostname=host) as stream:
                stream.sendall(('GET / HTTP/1.1\r\nHost: ' + host +
                                '\r\nX-Forwarded-For: 10.1.1.10\r\nConnection: close\r\n\r\n').encode())
                data = b''
                while chunk := stream.recv(4096):
                    data += chunk
                assert data.startswith(b'HTTP/1.1 403')
                assert b"You don't have access." in data
                assert b'cache-control: no-store' in data.lower()
                assert b'content-type: text/html' in data.lower()
    finally:
        run('ip', 'address', 'del', source + '/32', 'dev', 'lo')
    print(json.dumps({'checkedOn': '2026-11-02', 'checks': {
        'hostInternalResolverOnly': True, 'hostDnsOwnedByNetworkdAndResolved': True,
        'ifupdownResolvconfAndNetplanAbsent': True, 'dockerAndWireguardLinksUnmanagedByNetworkd': True,
        'resolvedHasNoDnsStubListener': True,
        'dockerDaemonInternalDefault': True,
        'allRunningContainersEmbeddedDnsInternalUpstream': True,
        'privateWildcardAndPublicRecursion': True,
        'adguardUnboundNoPublicFallback': True, 'wireguardProfilesInternalDns': True,
        'sourceDenialBeforeProxyAndAuth': True, 'forwardedHeaderCannotBypassSourceGate': True,
        'customHtml403NoStore': True},
        'limits': ['Synthetic untrusted source, not independent WAN/VPN-device acceptance',
                   'Already imported owner VPN profiles require re-import',
                   'Single internal resolver remains a dependency; no public secondary configured']}, indent=2))


if __name__ == '__main__':
    main()
