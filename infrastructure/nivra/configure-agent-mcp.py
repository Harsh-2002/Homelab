#!/usr/bin/env python3
"""Add owner-provided Nivra MCP credential to local clients, never print it.

Read the credential from stdin. Back up protected files and preserve all other
settings semantically. Requires PyYAML. No credential is committed with this file.
"""
import datetime
import json
from pathlib import Path
import shutil
import sys
import tomllib
import urllib.error
import urllib.request
import yaml

key=sys.stdin.read().strip()
assert key.startswith('nivra_') and len(key)>40
url='https://notes.l3b.cc.cd/mcp'
header={'Authorization':'Bearer '+key}
home=Path.home()
backup=home/'.local/state/nivra-mcp-backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
backup.mkdir(parents=True,mode=0o700)
paths=[home/'.codex/config.toml',home/'.claude.json',home/'.hermes/config.yaml']
for path in paths:
    old=path.read_text()
    if path.suffix=='.toml':
        doc=tomllib.loads(old)
        assert 'nivra' not in doc.get('mcp_servers',{}),'Nivra already exists; review before replacing'
        new=old.rstrip()+'\n\n[mcp_servers.nivra]\nurl = '+json.dumps(url)+'\nhttp_headers = { Authorization = '+json.dumps(header['Authorization'])+' }\n'
        updated=tomllib.loads(new)
        added=updated['mcp_servers'].pop('nivra')
        assert updated==doc
    else:
        doc=json.loads(old) if path.suffix=='.json' else yaml.safe_load(old)
        servers=doc.setdefault('mcpServers' if path.suffix=='.json' else 'mcp_servers',{})
        assert 'nivra' not in servers,'Nivra already exists; review before replacing'
        servers['nivra']={'url':url,'headers':header}
        if path.suffix=='.json':servers['nivra']['type']='http'
        new=json.dumps(doc,indent=2)+'\n' if path.suffix=='.json' else yaml.safe_dump(doc,sort_keys=False)
    saved=backup/path.name
    shutil.copy2(path,saved);saved.chmod(0o600)
    path.write_text(new);path.chmod(0o600)
print('Nivra configured in Codex, Claude and Hermes; protected backups created; no secret output')
for client in ['Codex','Claude','Hermes']:
    request=urllib.request.Request(url,json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':client.lower()+'-validation','version':'1.0'}}}).encode(),{'Content-Type':'application/json','Accept':'application/json, text/event-stream',**header})
    with urllib.request.urlopen(request,timeout=25) as response:
        assert response.status==200
        body=response.read().decode()
        result=json.loads(body) if body.lstrip().startswith('{') else json.loads(next(line[6:] for line in body.splitlines() if line.startswith('data: ')))
        assert 'result' in result
    request=urllib.request.Request(url,json.dumps({'jsonrpc':'2.0','id':2,'method':'tools/list'}).encode(),{'Content-Type':'application/json','Accept':'application/json, text/event-stream',**header})
    with urllib.request.urlopen(request,timeout=25) as response:
        body=response.read().decode()
        result=json.loads(body) if body.lstrip().startswith('{') else json.loads(next(line[6:] for line in body.splitlines() if line.startswith('data: ')))
        tools=result['result']['tools']
        assert tools
    print('PASS:',client,'MCP initialize and discovery:',len(tools),'tools')
