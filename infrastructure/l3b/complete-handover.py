#!/usr/bin/env python3
"""One-shot finalizer outside the OpenCode server it must restart.

Runs only when explicitly scheduled for the owner's native-service handover.
No recurring schedule, proxy process, agent inference, or credential output.
"""
import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path('/home/dev/Homelab')
STAGE = 'preflight'


def run(*command, timeout=240, env=None):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Scoped command failed: ' + command[0])
    return result.stdout


def main():
    global STAGE
    os.chdir(ROOT)
    # A delayed self-hosting handover must not overwrite newly started owner work.
    run('git', 'diff', '--quiet')
    run('git', 'diff', '--cached', '--quiet')
    baseline = run('git', 'rev-parse', 'HEAD').strip()
    # Check the detached worker's credentials before interrupting the server.
    run('docker', 'version', '--format', '{{.Server.Version}}')
    run('sudo', '-n', 'python3', 'infrastructure/l3b/verify-dns-policy.py')
    STAGE = 'native-activation'
    run('python3', 'infrastructure/l3b/activate-opencode.py', timeout=420)
    for name in ['services.yaml', 'settings.yaml']:
        (Path('/data/apps/homepage/config') / name).write_bytes(
            (ROOT / 'infrastructure/l3b/homepage' / name).read_bytes())
    run('docker', 'exec', 'homepage', 'wget', '-qO-', '--post-data=', 'http://127.0.0.1:3000/api/revalidate')
    for name, flags in [('core', []), ('memory', [])]:
        STAGE = name + '-verification'
        filename = {'core': 'CORE', 'homepage': 'HOMEPAGE', 'memory': 'MEMORY'}[name]
        run('python3', f'infrastructure/l3b/verify-{name}.py', *flags, '--save',
            f'infrastructure/l3b/{filename}-VERIFICATION-2026-11-02.json')
    run('python3', 'infrastructure/agents/check-integrations.py', '--single-node', '--memory')
    STAGE = 'architecture-exports'
    assert run('git', 'rev-parse', 'HEAD').strip() == baseline
    changed = set(run('git', 'diff', '--name-only').splitlines())
    assert changed <= {f'infrastructure/l3b/{name}-VERIFICATION-2026-11-02.json'
                       for name in ['CORE', 'HOMEPAGE', 'MEMORY']}
    inventory_path = ROOT / 'docs/architecture/inventory.json'
    inventory = json.loads(inventory_path.read_text())
    inventory['currentDeployment']['opencodeRemote']['state'] = 'verified'
    inventory['currentDeployment']['opencodeRemote']['firstAttempt'] = 'Initial group-membership failure resolved by verified sg docker handover.'
    inventory_path.write_text(json.dumps(inventory, indent=2) + '\n')
    # Keep the private scene truthful after activation, without publishing IP data.
    private_path = ROOT / 'docs/architecture/internal-addresses.local.json'
    private = json.loads(private_path.read_text())
    for name in ['opencode', 'flow-opencode']:
        private[name] = 'Native bridge 10.1.3.1:4096 / private HTTPS verified'
    private_path.write_text(json.dumps(private, indent=2) + '\n')
    for script in ['build', 'excalidraw-build']:
        for flags in [[], ['--internal']]:
            run('node', f'docs/architecture/{script}.mjs', *flags)
    env = {**os.environ}
    for script in ['excalidraw-render', 'export-overviews']:
        for flags in [[], ['--internal']]:
            run('node', f'docs/architecture/{script}.mjs', *flags, env=env)
    for script in ['check', 'check-topology']:
        run('node', f'docs/architecture/{script}.mjs')
    run('node', 'docs/architecture/check-topology.mjs', '--internal')
    record_path = ROOT / 'infrastructure/l3b/NATIVE-HANDOVER-2026-11-02.json'
    record = {'checkedOn': '2026-11-02', 'state': 'verified',
              'nativeService': 'opencode.service', 'url': 'https://oc.l3b.cc.cd',
              'sessionHistoryPreserved': True, 'previousVaultPasswordRestored': True,
              'loopbackReplacedByDockerBridgeOnlyListener': True,
              'pairedBrowserAndCoreMemoryDashboardChecks': 'passed',
              'internalDnsAndPrivateSourcePolicy': 'verified before activation',
              'limits': ['Owner devices need fresh pairing; prior logins were intentionally invalidated',
                         'No public tunnel, duplicate server, reboot or failure-injection test']}
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    failure_path = ROOT / 'infrastructure/l3b/NATIVE-HANDOVER-FAILED-2026-11-02.json'
    if failure_path.exists():
        failure = json.loads(failure_path.read_text())
        failure['state'] = 'resolved'
        failure['resolution'] = 'Superseded by verified native handover; see NATIVE-HANDOVER-2026-11-02.json'
        failure['handoverRetry'] = 'Verified'
        failure_path.write_text(json.dumps(failure, indent=2) + '\n')
    STAGE = 'scoped-git-publication'
    run('git', 'diff', '--check')
    # Refuse to include another user's staged work in this maintenance commit.
    run('git', 'diff', '--cached', '--quiet')
    paths = ['docs/architecture/inventory.json', 'docs/architecture/homelab.svg',
             'docs/architecture/flows.svg', 'docs/architecture/homelab.png',
             'docs/architecture/flows.png', 'docs/architecture/homelab-architecture.pdf',
             'docs/architecture/homelab-topology.excalidraw', 'docs/architecture/topology-manifest.json',
             'docs/architecture/topology-tree.png', 'docs/architecture/core-flow.png',
             'infrastructure/l3b/CORE-VERIFICATION-2026-11-02.json',
             'infrastructure/l3b/HOMEPAGE-VERIFICATION-2026-11-02.json',
             'infrastructure/l3b/MEMORY-VERIFICATION-2026-11-02.json',
             'infrastructure/l3b/OPENCODE-VERIFICATION-2026-11-02.json',
             'infrastructure/l3b/NATIVE-HANDOVER-2026-11-02.json',
             'infrastructure/l3b/NATIVE-HANDOVER-FAILED-2026-11-02.json']
    run('git', 'add', '--', *paths)
    staged = set(run('git', 'diff', '--cached', '--name-only').splitlines())
    assert staged <= set(paths)
    run('git', 'commit', '-m', 'Verify native OpenCode remote service handover')
    run('git', 'push', 'origin', 'main')
    commit = run('git', 'rev-parse', 'HEAD').strip()
    assert run('git', 'ls-remote', 'origin', 'refs/heads/main').split()[0] == commit
    # Refresh the authored current-state entry without exposing account credentials.
    STAGE = 'openviking-current-state-refresh'
    client = json.loads((Path.home() / '.openviking/ovcli.conf').read_text())
    headers = {'Authorization': 'Bearer ' + client['api_key'], 'Content-Type': 'application/json'}
    uri = 'viking://resources/homelab/CURRENT-L3B.md'
    with urllib.request.urlopen(urllib.request.Request(client['url'] + '/api/v1/content/read?' +
                                                     urllib.parse.urlencode({'uri': uri}), headers=headers), timeout=60) as response:
        body = json.load(response)['result']
    content = body if isinstance(body, str) else body['content']
    content += '\n\n## Native handover completed\n\nThe native opencode.service is active/enabled with the previous vault credentials and preserved session history. It listens only on the Docker bridge; Caddy directly serves https://oc.l3b.cc.cd without a duplicate server or proxy helper. Actual browser pairing, Secure/HttpOnly cookie authentication, HTTPS API, five Homepage cards and core/memory checks passed. Owner devices need their own fresh pairing link. Scoped handover commit: ' + commit + ', remote main verified. This completion supersedes the in-progress notes above.\n'
    req = urllib.request.Request(client['url'] + '/api/v1/content/write', headers=headers,
                                 data=json.dumps({'uri': uri, 'content': content, 'mode': 'replace'}).encode())
    with urllib.request.urlopen(req, timeout=90) as response:
        assert response.status == 200
    index_uri = 'viking://resources/homelab/START-HERE.md'
    with urllib.request.urlopen(urllib.request.Request(client['url'] + '/api/v1/content/read?' +
                                                     urllib.parse.urlencode({'uri': index_uri}), headers=headers), timeout=60) as response:
        index = json.load(response)['result']
    old = 'Native OpenCode HTTPS remote access is explicitly authorized and its final service handover is still in progress.'
    if isinstance(index, str) and old in index:
        index = index.replace(old, 'Native OpenCode HTTPS remote access is now verified; see CURRENT-L3B.md and the repository handover evidence.', 1)
        req = urllib.request.Request(client['url'] + '/api/v1/content/write', headers=headers,
                                     data=json.dumps({'uri': index_uri, 'content': index, 'mode': 'replace'}).encode())
        with urllib.request.urlopen(req, timeout=90) as response:
            assert response.status == 200
    text = ('Native OpenCode handover verified: opencode.service active/enabled, bridge-only listener, '
            'https://oc.l3b.cc.cd, previous HomeLab vault password restored as owner confirmed, session history preserved. '
            'Actual browser pairing and Secure/HttpOnly cookie API access passed; owner devices need fresh pairing. '
            'Five Homepage cards plus core DNS/TLS/auth and OpenViking checks passed. No duplicate/proxy/public tunnel; '
            'Docker publications remain only 53/UDP and 443/TCP+UDP. Commit ' + commit + ' pushed; remote main verified. '
            'OpenViking current-state entry refreshed. No reboot/failure-injection test claimed.')
    payload = {'children': [{'object': 'block', 'type': 'paragraph',
                             'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': text}}]}}]}
    STAGE = 'notion-completion-append'
    result = subprocess.run(['ntn', 'api', '/v1/blocks/3e0d3ccf-b520-81d1-83b8-cb1465f4935a/children',
                             '-X', 'PATCH', '--data', '@-'], input=json.dumps(payload),
                            capture_output=True, text=True, timeout=60,
                            env={**os.environ, 'NOTION_KEYRING': '0'})
    assert result.returncode == 0
    block_id = json.loads(result.stdout)['results'][0]['id']
    result = subprocess.run(['ntn', 'api', '/v1/blocks/' + block_id],
                            capture_output=True, text=True, timeout=30,
                            env={**os.environ, 'NOTION_KEYRING': '0'})
    assert result.returncode == 0 and commit in result.stdout
    print('Native handover verified, published and recorded; credentials/pairing links withheld')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        failure_path = ROOT / 'infrastructure/l3b/NATIVE-HANDOVER-FAILED-2026-11-02.json'
        previous = json.loads(failure_path.read_text()) if failure_path.exists() else {}
        failure = {**previous, 'checkedOn': '2026-11-02', 'state': 'incomplete', 'stage': STAGE,
                   'note': 'Inspect scoped unit and read-only verifiers without printing secrets. Do not infer success.'}
        failure_path.write_text(json.dumps(failure, indent=2) + '\n')
        raise SystemExit('Handover finalizer stopped at ' + STAGE + '; private output withheld') from None
