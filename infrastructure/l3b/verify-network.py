#!/usr/bin/env python3
"""Read-only l3b network/ACL verification. Run as root for private config reads."""
import argparse
import ipaddress
import json
import subprocess
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()

    def docker(*command):
        return subprocess.check_output(['docker', *command], text=True)

    network = json.loads(docker('network', 'inspect', 'l3b'))[0]
    assert network['Driver'] == 'bridge'
    assert network['IPAM']['Config'] == [{'Subnet': '10.1.3.0/24', 'Gateway': '10.1.3.1'}]
    cidr = ipaddress.ip_network('10.1.3.0/24')
    names = {'adguard', 'unbound', 'pocketid', 'tinyauth', 'caddy', 'homepage',
             'portainer', 'openviking', 'ollama'}
    containers = json.loads(docker('inspect', *sorted(names)))
    attached = {v['Name'] for v in network['Containers'].values()}
    assert names <= attached
    for c in containers:
        name = c['Name'].lstrip('/')
        endpoint = c['NetworkSettings']['Networks']['l3b']
        assert c['State']['Running']
        assert endpoint['NetworkID'] == network['Id']
        assert ipaddress.ip_address(endpoint['IPAddress']) in cidr
        assert name in endpoint['Aliases']
        if name == 'caddy':
            assert {'auth.l3b.cc.cd', 'login.l3b.cc.cd'} <= set(endpoint['Aliases'])
            assert 'DOCKER_CIDR=10.1.3.0/24' in c['Config']['Env']
        if name == 'tinyauth':
            assert 'TINYAUTH_AUTH_TRUSTEDPROXIES=10.1.3.0/24' in c['Config']['Env']
        if name in {'caddy', 'homepage'}:
            assert 'opencode:10.1.3.1' in c['HostConfig']['ExtraHosts']
    config = yaml.safe_load(Path('/data/apps/adguard/conf/AdGuardHome.yaml').read_text())
    assert '10.1.3.0/24' in config['dns']['allowed_clients']
    assert '172.17.0.0/16' not in config['dns']['allowed_clients']
    assert config['dns']['upstream_dns'] == ['unbound:5335']
    assert 'access-control: 10.1.3.0/24 allow' in Path('/data/apps/unbound/unbound.conf').read_text()
    config = yaml.safe_load(Path('/data/apps/hermes/home/config.yaml').read_text())
    assert config['dashboard']['trusted_proxies'] == ['10.1.3.0/24']
    routes = subprocess.check_output(['ip', '-4', 'route'], text=True)
    assert '10.1.1.0/24 dev eno1' in routes and '10.1.2.0/24 dev wg0' in routes
    assert '10.1.3.0/24 dev br-' in routes and '172.17.' not in routes
    subprocess.run(['systemctl', 'is-active', '--quiet', 'wg-quick@wg0'], check=True)
    result = {'checkedOn': '2026-11-02', 'network': 'l3b', 'checks': {
        'ownerRequestedSubnetAndGateway': True, 'coreAndRestoredAppContainersOnNewBridge': True,
        'serviceAndIdentityProxyAliasesPreserved': True, 'lanAndWireguardRoutesPreserved': True,
        'adguardAndUnboundAclUpdated': True, 'caddyAndTinyauthEffectiveTrustUpdated': True,
        'nativeUpstreamAliasesUpdated': True, 'stoppedHermesTrustUpdated': True,
        'oldBridgeRouteAbsent': True},
        'limits': ['Native OpenCode and DNS policy have separate passing service/policy verifiers',
                   'Host migrated live to networkd; Docker live-restore restart was tested during DNS setup',
                   'No reboot or independent owner VPN client test performed']}
    text = json.dumps(result, indent=2) + '\n'
    if args.save:
        args.save.write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
