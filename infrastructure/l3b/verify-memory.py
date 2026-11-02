#!/usr/bin/env python3
"""Read-only checks of the restored memory backend and native OpenCode integration."""
import argparse
import base64
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    config_path = Path.home() / '.openviking/ovcli.conf'
    assert not config_path.stat().st_mode & 0o077
    config = json.loads(config_path.read_text())
    checks = {}

    def request(url, headers=None, body=None):
        req = urllib.request.Request(url, headers=headers or {},
                                     data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)

    headers = {'Authorization': 'Bearer ' + config['api_key'], 'Content-Type': 'application/json'}
    base = config['url']
    assert base == 'https://memory.l3b.cc.cd'
    assert request(base + '/health')
    for path in ['/api/v1/fs/ls?uri=viking%3A%2F%2Fresources', '/studio', '/mcp']:
        try:
            request(base + path, {'Accept': 'application/json'})
            raise AssertionError('Missing memory authentication boundary')
        except urllib.error.HTTPError as error:
            assert error.code == 401
    checks['privateStudioAndApiAuthentication'] = True
    status = request(base + '/api/v1/system/status', headers)['result']
    assert status['initialized']
    request(base + '/api/v1/fs/ls?uri=viking%3A%2F%2Fresources', headers)
    checks['restoredAccountKeyAndResourcesAccessible'] = True
    for name in ['queue', 'models']:
        observer = request(base + '/api/v1/observer/' + name, headers)['result']
        assert observer['is_healthy'] and not observer['has_errors']
        checks[name + 'ObserverHealthy'] = True
    result = request(base + '/api/v1/search/find', headers, {
        'query': 'current single-node generic stack naming and OpenViking memory',
        'target_uri': 'viking://resources/homelab/CURRENT-L3B.md',
        'limit': 3, 'score_threshold': 0.1})['result']
    assert 'viking://resources/homelab/CURRENT-L3B.md' in json.dumps(result)
    checks['newCurrentStateWriteReadAndSemanticIndex'] = True
    doctor = subprocess.run(['docker', 'exec', 'openviking', 'openviking-server', 'doctor'],
                            capture_output=True, text=True, timeout=120)
    for label in ['Embedding', 'VLM', 'Authentication', 'Native Engine']:
        assert re.search(re.escape(label) + r':\s+PASS', doctor.stdout)
    checks['localEmbeddingAndSavedVlmDoctorProbes'] = True
    checks['botDisabled'] = True
    containers = json.loads(subprocess.check_output(['docker', 'inspect', 'openviking', 'ollama'], text=True))
    for item in containers:
        assert item['State']['Health']['Status'] == 'healthy'
        assert item['Config']['Labels']['com.docker.compose.project'] == 'memory'
        assert not item['HostConfig'].get('PortBindings')
    assert 'OPENVIKING_WITH_BOT=0' in containers[0]['Config']['Env']
    checks['memoryStackHealthyWithoutPublishedPorts'] = True
    service = json.loads((Path.home() / '.config/opencode/service.json').read_text())
    host = service.get('hostname', '127.0.0.1')
    if host in ['0.0.0.0', '::']:
        host = '127.0.0.1'
    native = f'http://{host}:{service["port"]}'
    auth = {'Authorization': 'Basic ' + base64.b64encode(('opencode:' + service['password']).encode()).decode()}
    query = urllib.parse.urlencode({'location[directory]': '/home/dev/Homelab'})
    plugins = request(native + '/api/plugin?' + query, auth)['data']
    assert sum(item['id'] == 'openviking' for item in plugins) == 1
    assert any(item['id'] == 'herdr.opencode' for item in plugins)
    mcps = request(native + '/api/mcp?' + query, auth)['data']
    assert next(item for item in mcps if item['name'] == 'openviking')['status']['status'] == 'connected'
    skills = request(native + '/api/skill?' + query, auth)['data']
    names = {item['name'] for item in skills}
    assert {'openviking-memory', 'openviking-skills', 'ov-experience-memory'} <= names
    assert config['plugin']['autoCapture'] and config['plugin']['autoRecall']
    checks['officialPluginMcpAndThreeSkillsAvailable'] = True
    checks['herdrPreservedAndAutomaticRecallCaptureConfigured'] = True
    result = {'checkedOn': '2026-11-02', 'stack': 174, 'checks': checks,
              'limits': ['Automatic raw conversation/tool capture explicitly chosen by owner',
                         'Redaction filters reduce risk but cannot guarantee arbitrary secret removal',
                         'No old Codex/Claude client config or old automation restored',
                         'Bot gateway is intentionally disabled; doctor bot-client warning is not a VLM failure']}
    text = json.dumps(result, indent=2) + '\n'
    if args.save:
        args.save.write_text(text)
    print(text)


if __name__ == '__main__':
    main()
