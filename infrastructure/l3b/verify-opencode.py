#!/usr/bin/env python3
"""Check the single native OpenCode service and its private HTTPS/browser access."""
import argparse
import base64
import json
import os
import socket
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    config_path = Path.home() / '.config/opencode/service.json'
    config = json.loads(config_path.read_text())
    assert not config_path.stat().st_mode & 0o077
    assert config['hostname'] == '172.17.0.1' and config['port'] == 4096
    for action in ['is-active', 'is-enabled']:
        subprocess.run(['systemctl', '--user', action, '--quiet', 'opencode.service'], check=True)
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
    checks = {'nativeUserServiceActiveAndEnabled': True, 'previousVaultCredentialsRestored': True,
              'dockerBridgeOnlyBindAndNoLan4096': True, 'httpsUiAndAuthenticatedApi': True,
              'anonymousApiRejected': True, 'noDuplicateOrHostProxy': True}
    if args.browser:
        code = json.loads(request('/api/pair', auth, 'POST')[1])['code']
        browser = r'''
const fs=require('node:fs');const {chromium}=require('/app/node_modules/playwright-core');
(async()=>{const pair=JSON.parse(fs.readFileSync(0,'utf8'));const b=await chromium.connectOverCDP('http://127.0.0.1:9222');const c=await b.newContext();try{const p=await c.newPage();const errors=[];p.on('pageerror',()=>errors.push('pageerror'));await p.goto(pair.url,{waitUntil:'domcontentloaded'});await p.waitForFunction(()=>document.title.toLowerCase().includes('opencode')&&document.body.innerText.trim().length>20,{timeout:30000});const r=await c.request.get('https://oc.l3b.cc.cd/api/info');if(r.status()!==200)throw Error('Cookie authentication');const cookies=(await c.cookies('https://oc.l3b.cc.cd')).filter(x=>x.name.startsWith('opencode'));if(!cookies.length||cookies.some(x=>!x.secure||!x.httpOnly))throw Error('Cookie security');if(errors.length)throw Error('Browser page errors');await p.screenshot({path:'/tmp/opencode-native.png',fullPage:true});console.log(JSON.stringify({pairedBrowserApi:true,renderedBrowserUi:true,secureCookie:true,httpOnly:true,pageErrors:0}));}finally{await c.close()}process.exit(0)})().catch(()=>{console.error('Native OpenCode browser validation failed; private details withheld');process.exit(1)});
'''
        result = subprocess.run(['docker', 'exec', '-i', 'playwright', 'node', '-e', browser],
                                input=json.dumps({'url': 'https://oc.l3b.cc.cd/auth/connect/' + code}),
                                capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise SystemExit('Native browser pairing failed; pairing token/output withheld')
        checks.update(json.loads(result.stdout))
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
