#!/usr/bin/env python3
"""Deploy one reviewed stack through the local Portainer API; never print secrets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'deploy', 'rename', 'remove', 'stop'])
    parser.add_argument('--name')
    parser.add_argument('--file', type=Path)
    parser.add_argument('--url', default=os.environ.get('PORTAINER_URL', 'https://portainer.l3b.cc.cd'))
    parser.add_argument('--endpoint', type=int, default=2)
    parser.add_argument('--env', action='append', default=[])
    parser.add_argument('--prune', action='store_true', help='Remove orphan services only within this selected stack')
    parser.add_argument('--timeout', type=int, default=180, help='Wait for native asynchronous deployment completion')
    args = parser.parse_args()
    env = os.environ.copy()
    token_file = Path(env.get('OP_SERVICE_ACCOUNT_TOKEN_FILE',
                             '/home/dev/.config/op/service-account-token'))
    env['OP_SERVICE_ACCOUNT_TOKEN'] = token_file.read_text().strip()
    result = subprocess.run(
        ['/home/dev/.local/bin/op', 'item', 'get', 'Portainer', '--vault',
         'HomeLab', '--format', 'json'], env=env, capture_output=True,
        text=True, check=True, timeout=30)
    fields = json.loads(result.stdout)['fields']
    values = {field['id']: field.get('value') for field in fields}
    headers = {'Content-Type': 'application/json'}

    def request(method, path, body=None):
        req = urllib.request.Request(
            args.url.rstrip('/') + '/api' + path, method=method,
            headers=headers, data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(req, timeout=300) as response:
            content = response.read()
            return json.loads(content) if content else None

    auth = request('POST', '/auth', {'Username': values['username'],
                                   'Password': values['password']})
    headers['Authorization'] = 'Bearer ' + auth['jwt']
    if args.action == 'status':
        print('Portainer version:', request('GET', '/status')['Version'])
        for item in request('GET', '/endpoints'):
            print('Environment:', item['Id'], item['Name'], item['URL'], item['Status'])
        stacks = request('GET', '/stacks')
        print('Saved stack count:', len(stacks))
        for item in stacks:
            if item['Name'] in ['portainer', 'agent-tools', 'core-dns', 'core-identity', 'core-proxy', 'homepage', 'hermes', 'opencode']:
                print('Managed stack:', item['Id'], item['Name'], item['Status'])
    elif args.action == 'rename':
        if not args.name:
            parser.error('--name is required')
        request('PUT', f'/endpoints/{args.endpoint}', {'Name': args.name})
        print('Environment renamed:', args.name)
    elif args.action in ['remove', 'stop']:
        if not args.name:
            parser.error('--name is required')
        matches = [item for item in request('GET', '/stacks')
                   if item['Name'] == args.name and item['EndpointId'] == args.endpoint]
        if len(matches) != 1:
            raise ValueError('Expected exactly one matching stack')
        path = f'/stacks/{matches[0]["Id"]}'
        if args.action == 'remove':
            request('DELETE', path + f'?endpointId={args.endpoint}')
        else:
            request('POST', path + f'/stop?endpointId={args.endpoint}')
        print(args.action.capitalize() + ' scoped stack:', args.name)
    else:
        if not args.name or not args.file:
            parser.error('--name and --file are required')
        if args.name in ['portainer', 'portainer-bootstrap']:
            raise SystemExit('Portainer cannot safely recreate its own server; use the documented bootstrap maintenance procedure')
        content = args.file.read_text()
        stack_env = [{'name': key, 'value': value} for key, value in
                     (entry.split('=', 1) for entry in args.env)]
        document = yaml.safe_load(content)
        expanded = False
        for service_name, service in document.get('services', {}).items():
            for env_path in service.pop('env_file', []):
                path = Path(env_path)
                if not path.is_relative_to('/data/apps'):
                    raise ValueError('Runtime env files must be under /data/apps')
                for line in path.read_text().splitlines():
                    if '=' not in line or line.lstrip().startswith('#'):
                        continue
                    key, value = line.split('=', 1)
                    if len(value) > 1 and value[0] == value[-1] and value[0] in ['"', "'"]:
                        value = value[1:-1]
                    variable = f'L3B_{service_name}_{key}'.upper().replace('-', '_')
                    service.setdefault('environment', {})[key] = '${' + variable + '}'
                    stack_env.append({'name': variable, 'value': value})
                    expanded = True
        if expanded:
            # Portainer cannot read arbitrary host env_file paths. Keep only
            # references in its stack definition; values stay in protected DB Env.
            content = yaml.safe_dump(document, sort_keys=False)
        existing = [item for item in request('GET', '/stacks')
                    if item['Name'] == args.name and item['EndpointId'] == args.endpoint]
        if existing:
            item = request('PUT', f'/stacks/{existing[0]["Id"]}?endpointId={args.endpoint}',
                           {'StackFileContent': content, 'Env': stack_env,
                            'Prune': args.prune, 'PullImage': False})
        else:
            item = request('POST', f'/stacks/create/standalone/string?endpointId={args.endpoint}',
                           {'Name': args.name, 'StackFileContent': content, 'Env': stack_env})
        deadline = time.monotonic() + args.timeout
        while item['Status'] == 3 and time.monotonic() < deadline:
            time.sleep(2)
            item = request('GET', f'/stacks/{item["Id"]}')
        if item['Status'] != 1:
            raise SystemExit(f'Stack {item["Id"]} did not become active; inspect its native Portainer deployment log')
        print('Verified active stack:', item['Id'], item['Name'])


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'Portainer API failed: HTTP {error.code}; response withheld')
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Operation failed: {type(error).__name__}; credentials/output withheld')
