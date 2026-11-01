#!/usr/bin/env python3
"""Copy only required core service data from the saved roots, never modifying them."""
import argparse
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    parser.add_argument('--address', required=True)
    parser.add_argument('--resume', action='store_true', help='Resume this script\'s interrupted staging, before any core service starts')
    args = parser.parse_args()
    roots = args.backup / 'final-cutover/containers'
    dest = Path('/data/apps')
    sources = {name: roots / directory / 'rootfs' for name, directory in
               [('proxy', '101-proxy'), ('dns', '102-dns'), ('identity', '103-identity')]}
    for name in ['caddy', 'adguard', 'unbound', 'pocket-id', 'tinyauth']:
        if (dest / name).exists() and not args.resume:
            raise SystemExit(f'{name}: destination exists; refusing overwrite')
        if args.resume:
            result = subprocess.run(['docker', 'inspect', '--format', '{{.State.Running}}',
                                     'adguard' if name == 'adguard' else name],
                                    capture_output=True, text=True, check=False)
            if result.stdout.strip() == 'true':
                raise SystemExit('Refusing staging resume while a core service is running')
    for name in ['caddy', 'adguard', 'unbound', 'pocket-id', 'tinyauth']:
        (dest / name).mkdir(mode=0o700, exist_ok=args.resume)

    def copy(src, dst):
        if src.is_dir():
            shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=args.resume)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def env_read(path):
        result = {}
        for line in path.read_text().splitlines():
            if '=' not in line or line.lstrip().startswith('#'):
                continue
            key, value = line.split('=', 1)
            if len(value) > 1 and value[0] == value[-1] and value[0] in ['"', "'"]:
                value = value[1:-1]
            result[key] = value
        return result

    def env_write(path, values):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            for key, value in values.items():
                if '\n' in value:
                    raise ValueError('Multiline environment value requires manual migration')
                stream.write(f'{key}={value}\n')

    local = Path(__file__).parent
    p = dest / 'caddy'
    copy(sources['proxy'] / 'usr/bin/caddy.custom', p / 'caddy')
    copy(sources['proxy'] / 'var/lib/caddy/.local/share/caddy', p / 'data/caddy')
    # Locks describe old processes, not recoverable state. Do not copy them.
    for lock in (p / 'data/caddy/locks').glob('*'):
        if lock.is_file():
            lock.unlink()
    (p / 'config').mkdir(exist_ok=args.resume)
    copy(local / 'Caddyfile', p / 'Caddyfile')
    old = env_read(sources['proxy'] / 'etc/caddy/cloudflare.env')
    env_write(p / 'runtime.env', {'CF_API_TOKEN': old['CLOUDFLARE_API_TOKEN'],
                                'LAN_CIDR': args.address.rsplit('.', 1)[0] + '.0/24',
                                'VPN_CIDR': '10.1.2.0/24',
                                'DOCKER_CIDR': '172.17.0.0/16'})

    p = dest / 'adguard'
    (p / 'conf').mkdir(exist_ok=args.resume)
    copy(sources['dns'] / 'opt/AdGuardHome/data', p / 'work/data')
    conf = yaml.safe_load((sources['dns'] / 'opt/AdGuardHome/AdGuardHome.yaml').read_text())
    conf['http']['address'] = '0.0.0.0:3000'
    conf['dns']['bind_hosts'] = ['0.0.0.0']
    conf['dns']['upstream_dns'] = ['unbound:5335']
    # Docker's DNS resolves the Unbound service name; no public DNS fallback.
    conf['dns']['bootstrap_dns'] = ['127.0.0.11']
    conf['dns']['fallback_dns'] = []
    conf['dns']['allowed_clients'] = ['127.0.0.0/8', '10.1.1.0/24', '10.1.2.0/24', '172.17.0.0/16']
    conf['filtering']['rewrites'] = [
        {'domain': 'l3b.cc.cd', 'answer': args.address, 'enabled': True},
        {'domain': '*.l3b.cc.cd', 'answer': 'l3b.cc.cd', 'enabled': True}]
    (p / 'conf/AdGuardHome.yaml').write_text(yaml.safe_dump(conf, sort_keys=False))
    (p / 'conf/AdGuardHome.yaml').chmod(0o600)

    p = dest / 'unbound'
    copy(local / 'unbound.conf', p / 'unbound.conf')
    (p / 'state').mkdir(mode=0o755, exist_ok=args.resume)
    copy(sources['dns'] / 'var/lib/unbound/root.key', p / 'state/root.key')
    os.chown(p / 'state', 1000, 1000)
    os.chown(p / 'state/root.key', 1000, 1000)

    identity = sources['identity']
    p = dest / 'pocket-id'
    (p / 'data').mkdir(exist_ok=args.resume)
    for name in ['pocket-id.db', 'pocket-id.db-wal', 'pocket-id.db-shm']:
        src = identity / 'var/lib/pocket-id' / name
        if src.exists():
            copy(src, p / 'data' / name)
    copy(identity / 'var/lib/pocket-id/data/uploads', p / 'data/uploads')
    copy(identity / 'etc/pocket-id/encryption-key', p / 'encryption-key')
    p.joinpath('encryption-key').chmod(0o600)
    old = env_read(identity / 'etc/pocket-id/pocket-id.env')
    old.update(DB_CONNECTION_STRING='/app/data/pocket-id.db',
               GEOLITE_DB_PATH='/app/data/GeoLite2-City.mmdb',
               ENCRYPTION_KEY_FILE='/run/secrets/pocket-id-key')
    env_write(p / 'runtime.env', old)

    p = dest / 'tinyauth'
    copy(identity / 'var/lib/tinyauth', p / 'data')
    old = env_read(identity / 'etc/tinyauth/tinyauth.env')
    old.update(TINYAUTH_DATABASE_PATH='/data/tinyauth.db',
               TINYAUTH_RESOURCES_PATH='/data/resources',
               TINYAUTH_AUTH_TRUSTEDPROXIES='172.17.0.0/16')
    env_write(p / 'runtime.env', old)

    for name in ['pocket-id', 'tinyauth']:
        root = dest / name
        for path in [root, *root.rglob('*')]:
            if not path.is_symlink():
                os.chown(path, 1000, 1000)
        database = root / 'data' / ('pocket-id.db' if name == 'pocket-id' else 'tinyauth.db')
        with sqlite3.connect(database) as connection:
            result = connection.execute('PRAGMA quick_check').fetchone()[0]
            if result != 'ok':
                raise ValueError(f'{name}: SQLite integrity failed')
            connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        print(f'{name}: copied database integrity passed; encryption/auth retained')
    print('Core data prepared; backup source unchanged. No service started by this script.')


if __name__ == '__main__':
    main()
