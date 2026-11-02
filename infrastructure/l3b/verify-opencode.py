#!/usr/bin/env python3
"""Check the single native OpenCode service and its private HTTPS/browser access."""
import argparse
import base64
import grp
import json
import os
import socket
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    config_path = Path.home() / '.config/opencode/service.json'
    config = json.loads(config_path.read_text())
    assert not config_path.stat().st_mode & 0o077
    assert config['hostname'] == '10.1.3.1' and config['port'] == 4096
    for action in ['is-active', 'is-enabled']:
        subprocess.run(['systemctl', '--user', action, '--quiet', 'opencode.service'], check=True)
    pid = int(subprocess.check_output(['systemctl', '--user', 'show', 'opencode.service',
                                      '--property=MainPID', '--value'], text=True))
    cgroup = subprocess.check_output(['systemctl', '--user', 'show', 'opencode.service',
                                     '--property=ControlGroup', '--value'], text=True).strip()
    pids = {pid, *map(int, (Path('/sys/fs/cgroup') / cgroup.lstrip('/') / 'cgroup.procs').read_text().split())}
    native_pids = []
    for value in pids:
        try:
            if (Path('/proc') / str(value) / 'comm').read_text().strip() == 'opencode':
                native_pids.append(value)
        except FileNotFoundError:
            continue
    assert native_pids
    for value in native_pids:
        status = (Path('/proc') / str(value) / 'status').read_text().splitlines()
        group_ids = set()
        for line in status:
            if line.startswith(('Gid:', 'Groups:')):
                group_ids.update(int(group) for group in line.split()[1:])
        assert grp.getgrnam('docker').gr_gid in group_ids
    env = os.environ.copy()
    env['OP_SERVICE_ACCOUNT_TOKEN'] = (Path.home() / '.config/op/service-account-token').read_text().strip()
    item = json.loads(subprocess.run(['op', 'item', 'get', 'OpenCode', '--vault', 'HomeLab', '--format', 'json'],
                                    env=env, capture_output=True, text=True, check=True, timeout=30).stdout)
    fields = {field['id']: field.get('value') for field in item['fields']}
    assert fields['username'] == 'opencode' and fields['password'] == config['password']
    auth = {'Authorization': 'Basic ' + base64.b64encode(('opencode:' + config['password']).encode()).decode()}

    def request(path, headers=None, method='GET'):
        req = urllib.request.Request('https://oc.l3b.cc.cd' + path, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=45) as response:
            return response.status, response.read()

    assert request('/')[0] == 200
    try:
        request('/api/info')
        raise AssertionError('Native API allowed anonymous access')
    except urllib.error.HTTPError as error:
        assert error.code == 401
    assert request('/api/info', auth)[0] == 200
    for address in ['10.1.1.10', '127.0.0.1']:
        with socket.socket() as sock:
            sock.settimeout(2)
            assert sock.connect_ex((address, 4096)) != 0
    names = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    assert 'opencode' not in names and 'opencode-host-proxy' not in names
    checks = {'nativeUserServiceActiveAndEnabled': True, 'nativeDockerGroupEffective': True,
              'previousVaultCredentialsRestored': True,
              'dockerBridgeOnlyBindAndNoLan4096': True, 'httpsUiAndAuthenticatedApi': True,
              'anonymousApiRejected': True, 'noDuplicateOrHostProxy': True}
    result = {'checkedOn': '2026-11-02', 'url': 'https://oc.l3b.cc.cd', 'checks': checks,
              'limits': ['Password restoration signs out old browser/app logins, not session history',
                         'Owner devices require their own fresh single-use pairing link',
                         'No public tunnel, reboot or failure-injection test performed']}
    text = json.dumps(result, indent=2) + '\n'
    if args.save:
        args.save.write_text(text)
    print(text)


if __name__ == '__main__':
    main()
