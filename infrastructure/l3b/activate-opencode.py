#!/usr/bin/env python3
"""One-shot native service takeover. Run outside the OpenCode process being stopped.

Restores the owner-approved previous vault password, retaining all other settings.
Failure restores the pre-handover configuration and starts the same native unit.
No credentials, pairing links, config contents or subprocess output are printed.
"""
import base64
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    home = Path.home()
    path = home / '.config/opencode/service.json'
    original = json.loads(path.read_text())
    assert original['hostname'] == '127.0.0.1' and original['port'] == 4096
    assert not path.stat().st_mode & 0o077
    env = os.environ.copy()
    env['OP_SERVICE_ACCOUNT_TOKEN'] = (home / '.config/op/service-account-token').read_text().strip()
    item = json.loads(subprocess.run(['op', 'item', 'get', 'OpenCode', '--vault', 'HomeLab', '--format', 'json'],
                                    env=env, capture_output=True, text=True, check=True, timeout=30).stdout)
    fields = {field['id']: field.get('value') for field in item['fields']}
    assert fields['username'] == 'opencode' and fields['password']

    def sessions(config):
        headers = {'Authorization': 'Basic ' + base64.b64encode(('opencode:' + config['password']).encode()).decode()}
        query = urllib.parse.urlencode({'location[directory]': '/home/dev/Homelab'})
        req = urllib.request.Request(f'http://{config["hostname"]}:{config["port"]}/api/session?' + query, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return {item['id'] for item in json.load(response)['data']}

    before = sessions(original)
    assert before, 'Expected the existing native session history'
    changed = {**original, 'hostname': '10.1.3.1', 'password': fields['password']}

    def save(config):
        # Preserve the original file and its private mode; no credential backup copy.
        path.write_text(json.dumps(config, indent=2) + '\n')
        path.chmod(0o600)

    def run(*command):
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)

    run('opencode', 'service', 'stop')
    try:
        save(changed)
        run('systemctl', '--user', 'start', 'opencode.service')
        deadline = time.monotonic() + 120
        while True:
            try:
                after = sessions(changed)
                assert before <= after
                break
            except (OSError, ValueError, KeyError):
                if time.monotonic() >= deadline:
                    raise RuntimeError('Native service did not become ready') from None
                time.sleep(2)
        run('python3', 'infrastructure/l3b/verify-opencode.py', '--browser', '--save',
            'infrastructure/l3b/OPENCODE-VERIFICATION-2026-11-02.json')
        print('Native OpenCode service takeover and HTTPS/browser verification passed; session history preserved')
    except Exception:
        subprocess.run(['systemctl', '--user', 'stop', 'opencode.service'], capture_output=True, timeout=90)
        save(original)
        subprocess.run(['systemctl', '--user', 'start', 'opencode.service'], capture_output=True, timeout=90)
        raise RuntimeError('Native handover failed; previous configuration restored; details withheld') from None


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Native handover failed; inspect scoped unit status without printing credentials') from None
