#!/usr/bin/env python3
"""Render pinned upstream chart plus explicit Kubernetes/HA compatibility patches.

Print public manifests to stdout; apply through apply_patch, never print Secrets.
Usage: python3 render-components.py /path/to/supabase-kubernetes
"""
import pathlib
import subprocess
import sys
import yaml

root=pathlib.Path(__file__).resolve().parents[2]
upstream=pathlib.Path(sys.argv[1])
commit=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
assert commit=='14806daa859670133b1139faebb473855806899a','Unexpected upstream source revision'
raw=subprocess.check_output(['helm','template','supabase-prod',str(upstream/'charts/supabase'),'-n','supabase-prod','-f',str(root/'gitops/apps/supabase-prod/components-values.yaml')],text=True)
objects=[x for x in yaml.safe_load_all(raw) if x]
assert not any(x['kind']=='Secret' for x in objects),'Refusing generated credentials in Git'
for obj in objects:
    obj['metadata']['namespace']='supabase-prod'
    if obj['kind']!='Deployment':
        continue
    pod=obj['spec']['template']['spec']
    name=obj['metadata']['name']
    if name.endswith('-analytics'):
        pass
    for container in pod.get('containers',[]):
        env=container.setdefault('env',[])
        envmap={x['name']:x for x in env}
        if 'DB_SSL' in envmap:
            # Postgres URL users consume sslmode; Realtime expects a boolean.
            envmap['DB_SSL']['value']='true' if name.endswith('-realtime') else 'verify-full'
        if 'POSTGRES_BACKEND_URL' in envmap:
            envmap['POSTGRES_BACKEND_URL']['value']+='?ssl=true'
        for key in ['GOTRUE_DB_DATABASE_URL','PGRST_DB_URI','DATABASE_URL','SUPABASE_DB_URL']:
            if key in envmap and '?sslmode=' in envmap[key].get('value',''):
                # URI substitutions must follow the SSL variable definition.
                pass
        env.extend([
            {'name':'PGSSLROOTCERT','value':'/etc/supabase-tls/ca.crt'},
            {'name':'NODE_EXTRA_CA_CERTS','value':'/etc/supabase-tls/ca.crt'},
        ])
        if name.endswith('-meta'):
            env.extend([{'name':'PG_META_DB_SSL','value':'true'},{'name':'PG_META_DB_SSL_ROOT_CERT','value':'/etc/supabase-tls/ca.crt'}])
        if name.endswith('-realtime'):
            env.append({'name':'DB_SSL_CA_CERT','value':'/etc/supabase-tls/ca.crt'})
        container.setdefault('volumeMounts',[]).append({'name':'postgres-ca','mountPath':'/etc/supabase-tls','readOnly':True})
    pod.setdefault('volumes',[]).append({'name':'postgres-ca','secret':{'secretName':'supabase-db-ca','items':[{'key':'ca.crt','path':'ca.crt'}]}})
    pdb={'apiVersion':'policy/v1','kind':'PodDisruptionBudget','metadata':{'name':name,'namespace':'supabase-prod'},'spec':{'minAvailable':1,'selector':obj['spec']['selector']}}
    # Appended after traversal to keep iteration bounded.
    obj['_pdb']=pdb
extra=[]
for obj in objects:
    if '_pdb' in obj:extra.append(obj.pop('_pdb'))
print(yaml.safe_dump_all(objects+extra,sort_keys=False))
