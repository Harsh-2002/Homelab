#!/usr/bin/env python3
"""Persist fresh production keys in 1Password, then provision Secrets via stdin.

Never regenerate secrets if the canonical item already exists. Never print them.
"""
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[2]
op=str(root/'scripts/op-sa')
def run(args,data=None):
    result=subprocess.run(args,input=data,capture_output=True,text=True)
    if result.returncode:
        raise SystemExit('Operation failed (private output withheld): '+args[0])
    return result.stdout
items=json.loads(run([op,'item','list','--vault','HomeLab','--format','json']))
items=[item for item in items if item['title']=='Supabase Production']
assert len(items)<=1, 'Duplicate canonical items'
if items:
    item=json.loads(run([op,'item','get',items[0]['id'],'--vault','HomeLab','--format','json']))
    values=json.loads(next(f['value'] for f in item['fields'] if f.get('label')=='deployment-secrets'))
else:
    # Fail closed if existing database state exists without the original key source.
    existing=json.loads(run(['kubectl','--context','k8s','get','pvc','-A','-o','json']))
    assert not any(p['metadata']['namespace']=='supabase-prod' for p in existing['items']), 'Existing PVCs without canonical vault keys'
    values=json.loads(run(['node',str(root/'infrastructure/supabase-prod/generate-secrets.mjs')]))
    payload={'title':'Supabase Production','category':'LOGIN','urls':[{'href':'https://supabase-prod.l3b.cc.cd','primary':True}], 'fields':[
        {'id':'username','type':'STRING','purpose':'USERNAME','value':values['username']},
        {'id':'password','type':'CONCEALED','purpose':'PASSWORD','value':values['dashboardPassword']},
        {'id':'deployment-secrets','label':'deployment-secrets','type':'CONCEALED','value':json.dumps(values)},
        {'id':'publishable-key','label':'publishable-key','type':'CONCEALED','value':values['publishableKey']},
        {'id':'secret-key','label':'secret-key','type':'CONCEALED','value':values['secretKey']},
        {'id':'postgres-password','label':'postgres-password','type':'CONCEALED','value':values['password']},
    ]}
    run([op,'item','create','--vault','HomeLab','--format','json','-'],json.dumps(payload))
def secret(name,data,typ='Opaque'):
    return {'apiVersion':'v1','kind':'Secret','metadata':{'name':name,'namespace':'supabase-prod'},'type':typ,'stringData':data}
groups={
 'jwt':{k:values[k] for k in ['anonKey','serviceKey']},
 'apikey':{k:values[k] for k in ['publishableKey','secretKey','anonKeyAsymmetric','serviceRoleKeyAsymmetric','jwtKeys','jwtJwks']},
 'db':{'password':values['password'],'passwordEncoded':values['password'],'database':'postgres','host':'supabase-db-rw.supabase-prod.svc.cluster.local','port':'5432'},
 'analytics':{k:values[k] for k in ['publicAccessToken','privateAccessToken']},
 'dashboard':{'username':values['username'],'password':values['dashboardPassword'],'openAiApiKey':''},
 'realtime':{k:values[k] for k in ['secretKeyBase','dbEncKey']},
 'meta':{'cryptoKey':values['cryptoKey']},
 'smtp':{'username':'','password':''},
 's3':{k:values[k] for k in ['keyId','accessKey']},
 'pgsodium':{'root.key':values['rootKey']},
}
groups['jwt']['secret']=values['jwtSecret']
objects=[secret('supabase-prod-'+group,data) for group,data in groups.items()]
objects.append(secret('supabase-prod-superuser',{'username':'postgres','password':values['password']},'kubernetes.io/basic-auth'))
run(['kubectl','--context','k8s','apply','-f','-'],json.dumps({'apiVersion':'v1','kind':'List','items':objects}))
print('Production secrets provisioned from canonical HomeLab / Supabase Production; no secret values displayed')
