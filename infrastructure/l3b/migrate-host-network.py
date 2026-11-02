#!/usr/bin/env python3
"""Owner-approved ifupdown -> native networkd migration with detached rollback.

Only eno1 is managed; Docker bridges and native WireGuard stay with their owners.
No interface-down, networking restart, or manual firewall command is used.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
STATE = Path('/var/lib/l3b-network-migration')
NETWORK = Path('/etc/systemd/network/10-eno1.network')
RESOLVED = Path('/etc/systemd/resolved.conf.d/l3b.conf')
OVERRIDE = Path('/run/systemd/system/networking.service.d/l3b-migration.conf')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          timeout=kwargs.pop('timeout', 90), **kwargs).stdout


def rollback():
    # Stopping networkd retains the static interface configuration. ifupdown is
    # retained until the new manager has passed checks, so it can resume ownership.
    run('systemctl', 'disable', '--now', 'systemd-networkd.service')
    subprocess.run(['systemctl', 'disable', '--now', 'systemd-resolved.service'], capture_output=True)
    NETWORK.unlink(missing_ok=True)
    RESOLVED.unlink(missing_ok=True)
    host = Path('/etc/resolv.conf')
    host.unlink(missing_ok=True)
    host.write_text((STATE / 'resolv.conf').read_text())
    Path('/etc/network/interfaces').write_text((STATE / 'interfaces').read_text())
    OVERRIDE.unlink(missing_ok=True)
    run('systemctl', 'daemon-reload')
    run('systemctl', 'unmask', 'networking.service')
    run('systemctl', 'enable', '--now', 'networking.service')
    print('Original interface ownership and internal DNS restored; no private output.')


def main():
    assert os.geteuid() == 0
    if '--rollback' in sys.argv:
        rollback()
        return
    assert not NETWORK.exists() and not RESOLVED.exists()
    assert not STATE.exists(), 'Previous migration state exists; review rather than overwrite'
    run('systemctl', 'is-active', 'networking.service')
    STATE.mkdir(mode=0o700)
    (STATE / 'interfaces').write_text(Path('/etc/network/interfaces').read_text())
    (STATE / 'resolv.conf').write_text(Path('/etc/resolv.conf').read_text())
    run('systemd-run', '--unit=l3b-network-rollback', '--on-active=180s',
        '--timer-property=AccuracySec=1s', '--collect', sys.executable, str(Path(__file__).resolve()), '--rollback')
    try:
        NETWORK.parent.mkdir(parents=True, exist_ok=True)
        RESOLVED.parent.mkdir(parents=True, exist_ok=True)
        NETWORK.write_bytes((ROOT / NETWORK.name).read_bytes())
        RESOLVED.write_bytes((ROOT / 'resolved.conf').read_bytes())
        # Clear ifupdown's ExecStop for this handover, so stopping its oneshot
        # cannot run ifdown or withdraw the address underneath the active session.
        OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
        OVERRIDE.write_text('[Service]\nExecStop=\n')
        run('systemctl', 'daemon-reload')
        run('systemctl', 'enable', '--now', 'systemd-networkd.service')
        run('networkctl', 'reload')
        run('networkctl', 'reconfigure', 'eno1')
        run('systemctl', 'disable', '--now', 'networking.service')
        run('systemctl', 'mask', 'networking.service')
        # resolved conflicts with resolvconf; apt replaces only that resolver
        # integration. The real network manager is already networkd at this point.
        env = {**os.environ, 'DEBIAN_FRONTEND': 'noninteractive', 'NEEDRESTART_MODE': 'l'}
        run('apt-get', 'install', '-y', '--no-install-recommends', 'systemd-resolved', env=env, timeout=120)
        # Refresh the existing bus's newly installed policy/user mapping; do not
        # restart the system bus or any network interface.
        run('systemctl', 'reload', 'dbus.service')
        run('systemctl', 'enable', '--now', 'systemd-resolved.service')
        run('systemctl', 'restart', 'systemd-resolved.service')
        link = Path('/etc/resolv.conf')
        link.unlink(missing_ok=True)
        link.symlink_to('/run/systemd/resolve/resolv.conf')
        deadline = time.monotonic() + 40
        while True:
            resolvers = [s for s in link.read_text().splitlines() if s.startswith('nameserver')]
            if resolvers == ['nameserver 10.1.1.10']:
                break
            if time.monotonic() > deadline:
                raise RuntimeError('Interface DNS was not adopted')
            time.sleep(1)
        status = run('networkctl', 'status', 'eno1', '--no-pager')
        assert str(NETWORK) in status and 'configured' in status
        assert '10.1.1.10' in run('resolvectl', 'dns', 'eno1')
        routes = run('ip', '-4', 'route')
        assert 'default via 10.1.1.1 dev eno1' in routes
        assert '10.1.2.0/24 dev wg0' in routes and '10.1.3.0/24 dev br-' in routes
        with urllib.request.urlopen('https://oc.l3b.cc.cd', timeout=15) as response:
            assert response.status == 200
        run('systemctl', 'is-active', 'docker.service', 'wg-quick@wg0.service')
        run('systemctl', 'stop', 'l3b-network-rollback.timer')
        print('networkd/resolved adopted static eno1 and internal DNS; HTTPS/Docker/WireGuard checks passed.')
    except Exception:
        rollback()
        subprocess.run(['systemctl', 'stop', 'l3b-network-rollback.timer'], capture_output=True)
        raise RuntimeError('Network migration failed; original ownership restored; private output withheld') from None
    # Only remove the old manager after the replacement has passed acceptance.
    run('apt-get', 'purge', '-y', 'ifupdown', 'resolvconf', env=env, timeout=120)
    old = Path('/etc/network/interfaces')
    if old.exists():
        assert old.read_text() == (STATE / 'interfaces').read_text()
        old.unlink()
    OVERRIDE.unlink(missing_ok=True)
    run('systemctl', 'daemon-reload')
    print('ifupdown/resolvconf removed. Only native networkd manages eno1; no netplan installed.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Host network migration stopped; inspect scoped services/state, not private configuration') from None
