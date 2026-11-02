#!/usr/bin/python3
"""Small host-native WireGuard peer manager. Never logs private keys."""
import argparse
import base64
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BASE = Path('/etc/wireguard')
STATE = BASE / 'l3b.json'
CONF = BASE / 'wg0.conf'
CLIENTS = BASE / 'clients'
FIREWALL = '/usr/local/libexec/l3b-wg-firewall'
NETWORK = ipaddress.ip_network('10.1.2.0/24')

def run(*args, data=None):
    p = subprocess.run(args, input=data, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args[:2]) + ' (private output suppressed)')
    return p.stdout.strip()

def write(path, text, mode=0o600):
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'w') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def load():
    if not STATE.exists():
        raise RuntimeError('Initialize with wg.sh init first')
    return json.loads(STATE.read_text())

def public(key):
    return run('wg', 'pubkey', data=key + '\n')

def live():
    return subprocess.run(['ip', 'link', 'show', 'wg0'], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0

def server(s):
    lines = ['[Interface]', 'Address = 10.1.2.1/24', 'ListenPort = 51820',
             'PrivateKey = ' + s['private'],
             'PostUp = ' + FIREWALL + ' up', 'PostDown = ' + FIREWALL + ' down']
    for name, p in sorted(s['peers'].items()):
        lines += ['', '# ' + name, '[Peer]', 'PublicKey = ' + p['public'],
                  'PresharedKey = ' + p['psk'], 'AllowedIPs = ' + p['address'] + '/32']
    return '\n'.join(lines) + '\n'

def profile(s, p):
    return '\n'.join(['[Interface]', 'PrivateKey = ' + p['private'],
                      'Address = ' + p['address'] + '/32', 'DNS = ' + s['dns'], '',
                      '[Peer]', 'PublicKey = ' + public(s['private']),
                      'PresharedKey = ' + p['psk'],
                      'Endpoint = ' + s['endpoint'] + ':51820',
                      'AllowedIPs = 10.1.1.0/24, 10.1.2.0/24',
                      'PersistentKeepalive = 25', ''])

def apply(s):
    # Replace complete managed files atomically; no SaveConfig rewrite on shutdown.
    write(CONF, server(s))
    write(STATE, json.dumps(s, indent=2) + '\n')
    for name, p in s['peers'].items():
        write(CLIENTS / (name + '.conf'), profile(s, p))
    if live():
        stripped = run('wg-quick', 'strip', str(CONF))
        run('wg', 'syncconf', 'wg0', '/dev/stdin', data=stripped + '\n')
        run(FIREWALL, 'up')

def verify(s, name=None):
    if CONF.read_text() != server(s):
        raise RuntimeError('Server config differs from managed state')
    addresses = set()
    keys = set()
    for key in [s['private']] + [p['psk'] for p in s['peers'].values()]:
        if len(base64.b64decode(key, validate=True)) != 32:
            raise RuntimeError('Invalid key encoding in private state')
    for n, p in s['peers'].items():
        ip = ipaddress.ip_address(p['address'])
        if ip not in NETWORK or int(str(ip).split('.')[-1]) not in range(2, 255):
            raise RuntimeError('Invalid client address: ' + n)
        if p['address'] in addresses or p['public'] in keys:
            raise RuntimeError('Duplicate client address/key')
        addresses.add(p['address'])
        keys.add(p['public'])
        if public(p['private']) != p['public']:
            raise RuntimeError('Client key mismatch: ' + n)
        if CLIENTS.joinpath(n + '.conf').read_text() != profile(s, p):
            raise RuntimeError('Client profile differs from managed state: ' + n)
    for p in [BASE, CLIENTS, STATE, CONF] + list(CLIENTS.glob('*.conf')):
        st = p.stat()
        if st.st_uid != 0 or st.st_mode & 0o077:
            raise RuntimeError('Unsafe owner or permissions: ' + str(p))
    if live():
        if run('wg', 'show', 'wg0', 'public-key') != public(s['private']):
            raise RuntimeError('Running server key mismatch')
        if run('wg', 'show', 'wg0', 'listen-port') != '51820':
            raise RuntimeError('Running listen port mismatch')
        actual = run('wg', 'show', 'wg0', 'allowed-ips')
        expected = {p['public']: p['address'] + '/32' for p in s['peers'].values()}
        observed = dict(line.split() for line in actual.splitlines()) if actual else {}
        if observed != expected:
            raise RuntimeError('Running peer/address set differs from managed state')
        actual_psks = run('wg', 'show', 'wg0', 'preshared-keys')
        observed_psks = dict(line.split() for line in actual_psks.splitlines()) if actual_psks else {}
        if observed_psks != {p['public']: p['psk'] for p in s['peers'].values()}:
            raise RuntimeError('Running preshared keys differ from managed state')
    if name is not None and name not in s['peers']:
        raise RuntimeError('Unknown profile: ' + name)
    print('Verified: saved keys, unique addresses, profiles, permissions' +
          (' and running peer configuration.' if live() else '; interface is down.'))

def endpoint(value):
    # IPv4 or DNS hostname; no ports, URLs, shell syntax or placeholders.
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?', value):
        raise argparse.ArgumentTypeError('Use a public IPv4 address or DNS hostname without a port')
    return value

def name(value):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,31}', value):
        raise argparse.ArgumentTypeError('Use 1-32 lowercase letters, digits, underscores or hyphens')
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init')
    p = sub.add_parser('configure')
    p.add_argument('--endpoint', type=endpoint)
    p.add_argument('--dns', type=ipaddress.IPv4Address)
    p.add_argument('--mode', choices=['nat', 'routed'])
    for cmd in ['add', 'revoke', 'export']:
        p = sub.add_parser(cmd)
        p.add_argument('name', type=name)
        if cmd == 'export':
            p.add_argument('--output', type=Path, help='Write a new mode-600 file; never overwrite an existing path')
    p = sub.add_parser('verify')
    p.add_argument('name', nargs='?', type=name)
    sub.add_parser('list')
    sub.add_parser('status')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError('Run with sudo wg.sh ...')
    os.umask(0o077)
    with open('/run/lock/l3b-wireguard.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.cmd == 'init':
            BASE.mkdir(mode=0o700, exist_ok=True)
            BASE.chmod(0o700)
            CLIENTS.mkdir(mode=0o700, exist_ok=True)
            if STATE.exists() or CONF.exists():
                raise RuntimeError('Existing state/config preserved; refusing to initialize again')
            s = {'private': run('wg', 'genkey'), 'endpoint': '', 'dns': '10.1.1.10',
                 'mode': 'nat', 'peers': {}}
            apply(s)
            print('Initialized wg0; configure a real public endpoint before adding clients.')
            return
        s = load()
        if args.cmd == 'configure':
            if args.endpoint is not None:
                s['endpoint'] = args.endpoint
            if args.dns is not None:
                s['dns'] = str(args.dns)
            if args.mode is not None:
                s['mode'] = args.mode
            apply(s)
            verify(s)
            print('Settings updated; re-export and re-import existing device profiles if DNS/endpoint changed.')
        elif args.cmd == 'add':
            if not s['endpoint']:
                raise RuntimeError('Set your real endpoint first: wg.sh configure --endpoint HOSTNAME')
            if args.name in s['peers']:
                raise RuntimeError('Profile exists; refusing to replace its identity')
            used = {p['address'] for p in s['peers'].values()}
            address = next((f'10.1.2.{i}' for i in range(2, 255) if f'10.1.2.{i}' not in used), None)
            if address is None:
                raise RuntimeError('No available client addresses')
            key = run('wg', 'genkey')
            s['peers'][args.name] = {'private': key, 'public': public(key),
                                    'psk': run('wg', 'genpsk'), 'address': address}
            apply(s)
            verify(s, args.name)
            print('Created ' + args.name + ': ' + address + '/32; use export explicitly to retrieve its secret profile.')
        elif args.cmd == 'revoke':
            if args.name not in s['peers']:
                raise RuntimeError('Unknown profile')
            del s['peers'][args.name]
            apply(s)
            CLIENTS.joinpath(args.name + '.conf').unlink(missing_ok=True)
            verify(s)
            print('Revoked saved and running peer: ' + args.name)
        elif args.cmd == 'verify':
            verify(s, args.name)
        elif args.cmd == 'export':
            # Verification output goes to stderr so stdout is only importable config.
            from contextlib import redirect_stdout
            with redirect_stdout(sys.stderr):
                verify(s, args.name)
            text = profile(s, s['peers'][args.name])
            if args.output is None:
                sys.stdout.write(text)
            else:
                # Do not overwrite files or follow symlinks; export file belongs to sudo caller.
                uid = int(os.environ.get('SUDO_UID', '0'))
                gid = int(os.environ.get('SUDO_GID', '0'))
                if not args.output.is_absolute():
                    raise RuntimeError('Output path must be absolute')
                if args.output.parent.stat().st_uid != uid:
                    raise RuntimeError('Export parent must belong to the invoking user')
                fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, 'w') as f:
                    os.fchown(f.fileno(), uid, gid)
                    f.write(text)
                print('Exported protected profile to ' + str(args.output))
        elif args.cmd == 'list':
            print('NAME                             ADDRESS')
            for n, p in sorted(s['peers'].items()):
                print(f'{n:32} {p["address"]}/32')
        elif args.cmd == 'status':
            print('Endpoint: ' + (s['endpoint'] or 'NOT SET'))
            print('DNS: ' + s['dns'] + '; LAN access: ' + s['mode'])
            if live():
                print(run('wg', 'show', 'wg0'))
            else:
                print('wg0 is down')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
