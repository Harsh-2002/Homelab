#!/usr/bin/env python3
"""Bounded read-only MCP stability audit. Never print credentials or SQL contents."""
import concurrent.futures
import collections
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import argparse

p = argparse.ArgumentParser()
p.add_argument('--calls', type=int, default=60)
p.add_argument('--workers', type=int, default=2)
args = p.parse_args()
assert 1 <= args.calls <= 300 and 1 <= args.workers <= 4
root = Path(__file__).resolve().parents[2]
item = json.loads(subprocess.check_output([str(root/'scripts/op-sa'),'item','get','Supabase','--vault','HomeLab','--format','json']))
key = next(f['value'] for f in item['fields'] if f.get('id')=='mcp-api-key')
methods = [('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'homelab-stability-audit','version':'1'}}),
           ('tools/list',{}),
           ('tools/call',{'name':'execute_sql','arguments':{'query':'select 1 as homelab_stability_probe'}})]

def call(index):
    method, params = methods[index % len(methods)]
    request_id = str(uuid.uuid4())
    request = urllib.request.Request('https://sb.l3b.cc.cd/mcp',
        json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':params}).encode(),
        {'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
    start = time.monotonic()
    result = {'index':index,'operation':method,'http':None,'ok':False}
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            result['http'] = response.status
            body = json.load(response)
            result['ok'] = 'result' in body and not body['result'].get('isError',False)
            if 'error' in body: result['rpc_code'] = body['error'].get('code')
            if not result['ok']: result['category'] = 'rpc_or_tool_error'
    except urllib.error.HTTPError as error:
        result['http'] = error.code
        result['kong_request_id'] = error.headers.get('X-Kong-Request-Id')
        try:
            body = json.loads(error.read())
            result['kong_request_id'] = body.get('request_id',result['kong_request_id'])
            result['category'] = 'kong_invalid_upstream' if body.get('message')=='An invalid response was received from the upstream server' else 'http_error'
        except (ValueError,AttributeError): result['category'] = 'non_json_http_error'
    except Exception as error:
        result['category'] = type(error).__name__
    result['seconds'] = round(time.monotonic()-start,3)
    return result

start = time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
    results = list(pool.map(call,range(args.calls)))
counts = collections.Counter(str(r['http'])+('/ok' if r['ok'] else '/failed') for r in results)
print(json.dumps({'calls':args.calls,'workers':args.workers,'elapsed_seconds':round(time.monotonic()-start,2),
    'counts':dict(counts),'max_latency_seconds':max(r['seconds'] for r in results),
    'failure_count':sum(not r['ok'] for r in results),
    'failure_sample':[r for r in results if not r['ok']][:10]},indent=2))
raise SystemExit(0 if all(r['ok'] for r in results) else 1)
