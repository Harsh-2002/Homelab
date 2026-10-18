#!/usr/bin/env python3
"""Consolidate canonical vault records while preserving existing agent MCP auth.

No credentials are printed or passed through argv. Safe to rerun after cutover.
"""
import json
from pathlib import Path
import subprocess

op=str(Path(__file__).resolve().parents[2]/'scripts/op-sa')
def run(args,data=None):
    r=subprocess.run(args,input=data,text=True,capture_output=True)
    assert r.returncode==0,'Vault operation failed; private output withheld'
    return r.stdout
def get(name):
    return json.loads(run([op,'item','get',name,'--vault','HomeLab','--format','json']))
items=json.loads(run([op,'item','list','--vault','HomeLab','--format','json']))
if any(item['title']=='Supabase Production' for item in items):
    current=get('Supabase Production')
    previous=get('Supabase')
    values=json.loads(next(f['value'] for f in current['fields'] if f.get('label')=='deployment-secrets'))
    values['mcpKey']=next(f['value'] for f in previous['fields'] if f.get('id')=='mcp-api-key')
    for field in current['fields']:
        if field.get('label')=='deployment-secrets':field['value']=json.dumps(values)
    previous['title']='Supabase - retired VM108'
    run([op,'item','edit',previous['id'],'--vault','HomeLab','--format','json','-'],json.dumps(previous))
    current['title']='Supabase'
    current['urls']=[{'href':'https://supabase.l3b.cc.cd','primary':True}]
    for field_id,value in {'mcp-api-key':values['mcpKey'],'mcp-url':'https://sb.l3b.cc.cd/mcp','api-url':'https://sb.l3b.cc.cd','postgres-host':'sb.l3b.cc.cd'}.items():
        current['fields'].append({'id':field_id,'label':field_id,'type':'CONCEALED' if field_id=='mcp-api-key' else 'STRING','value':value})
    run([op,'item','edit',current['id'],'--vault','HomeLab','--format','json','-'],json.dumps(current))
print('Canonical Supabase vault record prepared; existing agent MCP credential preserved')
