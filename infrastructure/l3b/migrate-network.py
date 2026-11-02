#!/usr/bin/env python3
"""One-time owner-approved l3b bridge migration; preserves containers and aliases.

Run as root during maintenance. No volumes, identities or application databases
are removed. Stack definition/env updates follow through Portainer separately.
Native OpenCode is deliberately not restarted by this script.
"""
import json
import subprocess
from pathlib import Path

import yaml


def docker(*args):
    return subprocess.run(['docker', *args], capture_output=True, text=True,
                          check=True, timeout=180).stdout


def main():
    network = json.loads(docker('network', 'inspect', 'l3b'))[0]
    assert network['Driver'] == 'bridge' and not network['Internal']
    assert network['IPAM']['Config'] == [{'Subnet': '172.17.0.0/16', 'Gateway': '172.17.0.1'}]
    assert not network['Options'] and not network['EnableIPv6']
    ids = list(network['Containers'])
    containers = json.loads(docker('inspect', *ids))
    assert all(set(c['NetworkSettings']['Networks']) == {'l3b'} for c in containers)
    aliases = {c['Name'].lstrip('/'): c['NetworkSettings']['Networks']['l3b'].get('Aliases') or []
               for c in containers}
    running = [c['Name'].lstrip('/') for c in containers if c['State']['Running']]
    assert set(running) == set(aliases), 'Review stopped endpoints before migrating'
    assert all(not c['NetworkSettings']['Networks']['l3b'].get('IPAMConfig') for c in containers)
    paths = [Path('/data/apps/caddy/runtime.env'), Path('/data/apps/tinyauth/runtime.env'),
             Path('/data/apps/adguard/conf/AdGuardHome.yaml'),
             Path('/data/apps/unbound/unbound.conf'), Path('/data/apps/hermes/home/config.yaml')]
    originals = {p: p.read_bytes() for p in paths}
    order = ['unbound', 'adguard', 'portainer', 'pocketid', 'tinyauth',
             'caddy', 'homepage', 'ollama', 'openviking', 'playwright']
    assert set(order) == set(running)

    def attach(subnet, gateway):
        docker('network', 'create', '--driver', 'bridge', '--subnet', subnet,
               '--gateway', gateway, 'l3b')
        for name, names in aliases.items():
            flags = [arg for alias in names for arg in ['--alias', alias]]
            docker('network', 'connect', *flags, 'l3b', name)

    try:
        docker('stop', '--time', '60', *running)
        # Force removes stopped endpoints too; preserve aliases for reattachment.
        for name in aliases:
            docker('network', 'disconnect', '--force', 'l3b', name)
        docker('network', 'rm', 'l3b')
        for p, original in originals.items():
            text = original.decode()
            if p.name == 'runtime.env':
                key = 'DOCKER_CIDR' if p.parent.name == 'caddy' else 'TINYAUTH_AUTH_TRUSTEDPROXIES'
                lines = text.splitlines()
                assert sum(line.startswith(key + '=') for line in lines) == 1
                text = '\n'.join(key + '=10.1.3.0/24' if line.startswith(key + '=') else line
                                 for line in lines) + '\n'
            elif p.name == 'AdGuardHome.yaml':
                config = yaml.safe_load(text)
                clients = config['dns']['allowed_clients']
                assert '172.17.0.0/16' in clients
                config['dns']['allowed_clients'] = ['10.1.3.0/24' if v == '172.17.0.0/16' else v for v in clients]
                text = yaml.safe_dump(config, sort_keys=False)
            elif p.parent.name == 'unbound':
                text = Path(__file__).with_name('unbound.conf').read_text()
            else:
                config = yaml.safe_load(text)
                config.setdefault('dashboard', {})['trusted_proxies'] = ['10.1.3.0/24']
                text = yaml.safe_dump(config, sort_keys=False)
            p.write_text(text)
        attach('10.1.3.0/24', '10.1.3.1')
        for name in order:
            docker('start', name)
        actual = json.loads(docker('network', 'inspect', 'l3b'))[0]
        assert actual['IPAM']['Config'] == [{'Subnet': '10.1.3.0/24', 'Gateway': '10.1.3.1'}]
        assert len(actual['Containers']) == len(containers)
        print('l3b migrated to 10.1.3.0/24, gateway 10.1.3.1; ten existing containers and aliases retained.')
        print('Native OpenCode unchanged; complete the reviewed Portainer env/host-alias updates next.')
    except Exception:
        # Restore the original network and files without exposing captured data.
        for name in running:
            subprocess.run(['docker', 'stop', '--time', '30', name], capture_output=True, timeout=90)
            subprocess.run(['docker', 'network', 'disconnect', '--force', 'l3b', name], capture_output=True, timeout=30)
        subprocess.run(['docker', 'network', 'rm', 'l3b'], capture_output=True, timeout=30)
        for p, original in originals.items():
            p.write_bytes(original)
        attach('172.17.0.0/16', '172.17.0.1')
        for name in order:
            docker('start', name)
        raise RuntimeError('Migration failed; original network restored; private output withheld') from None


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Network migration stopped; inspect selected network/service status; private output withheld') from None
