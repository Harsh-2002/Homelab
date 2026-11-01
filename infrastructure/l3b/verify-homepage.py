#!/usr/bin/env python3
"""Check Homepage's real UI and private gateway separately; never bypass public SSO."""
import argparse
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    for spoof in [False, True]:
        headers = {'Accept': 'application/json'}
        if spoof:
            headers.update({'Remote-User': 'admin', 'Remote-Groups': 'infrastructure-admins'})
        try:
            urllib.request.urlopen(urllib.request.Request('https://l3b.cc.cd', headers=headers), timeout=15)
            raise AssertionError('Homepage gateway allowed an unauthenticated request')
        except urllib.error.HTTPError as error:
            assert error.code == 401
    code = r'''
const {chromium}=require('/app/node_modules/playwright-core');
(async()=>{
  const browser=await chromium.connectOverCDP('http://127.0.0.1:9222');
  const results=[];
  for(const [name,width,height,colorScheme] of [['desktop',1440,900,'light'],['mobile',390,844,'dark']]){
    const context=await browser.newContext({viewport:{width,height},colorScheme});
    const page=await context.newPage();const errors=[];
    page.on('pageerror',()=>errors.push('pageerror'));
    page.on('console',m=>{if(m.type()==='error')errors.push('console-error')});
    const response=await page.goto('http://homepage:3000',{waitUntil:'networkidle'});
    if(response.status()!==200)throw Error('Backend UI response');
    for(const title of ['AdGuard Home','Portainer','Pocket ID'])await page.getByRole('link',{name:new RegExp('^'+title)}).first().waitFor();
    if(await page.getByText('API Error',{exact:false}).count())throw Error('Widget API error');
    const details=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,theme:document.documentElement.classList.contains('dark')?'dark':'light',cards:document.querySelectorAll('.service-card').length}));
    if(details.overflow||details.cards!==3||details.theme!==colorScheme||errors.length){console.error(JSON.stringify({device:name,...details,errors}));throw Error('UI acceptance');}
    await page.screenshot({path:'/tmp/homepage-'+name+'.png',fullPage:true});
    results.push({device:name,...details,consoleErrors:errors.length});
    await context.close();
  }
  console.log(JSON.stringify(results));process.exit(0);
})().catch(error=>{console.error(['Backend UI response','Widget API error','UI acceptance'].includes(error.message)?error.message:'Homepage browser validation failed; target content withheld');process.exit(1)});
'''
    run = subprocess.run(['docker', 'exec', 'playwright-mcp', 'node', '-e', code],
                         capture_output=True, text=True, timeout=120)
    if run.returncode:
        raise SystemExit('Homepage browser validation failed: ' + run.stderr.strip())
    result = {'checkedOn': '2026-11-02', 'stack': 168,
              'publicGatewayAndSpoofRejection': True, 'backendBrowser': json.loads(run.stdout),
              'limits': ['Public browser passkey/OIDC sign-in remains a human acceptance test',
                         'Backend browser test uses internal Docker service DNS; it does not claim SSO completion']}
    text = json.dumps(result, indent=2) + '\n'
    if args.save:
        args.save.write_text(text)
    print(text)


if __name__ == '__main__':
    main()
