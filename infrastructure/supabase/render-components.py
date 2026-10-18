#!/usr/bin/env python3
"""Render pinned upstream chart plus explicit Kubernetes/HA compatibility patches.

Print public manifests to stdout; apply through apply_patch, never print Secrets.
Usage: python3 render-components.py /path/to/supabase-kubernetes
"""
import pathlib
import hashlib
import subprocess
import sys
import yaml

root=pathlib.Path(__file__).resolve().parents[2]
upstream=pathlib.Path(sys.argv[1])
commit=subprocess.check_output(['git','-C',str(upstream),'rev-parse','HEAD'],text=True).strip()
assert commit=='14806daa859670133b1139faebb473855806899a','Unexpected upstream source revision'
subprocess.run([sys.executable,str(root/'infrastructure/supabase/check-init-contract.py'),str(upstream)],check=True,stdout=sys.stderr)
raw=subprocess.check_output(['helm','template','supabase-prod',str(upstream/'charts/supabase'),'-n','supabase-prod','--skip-tests','-f',str(root/'gitops/apps/supabase/components-values.yaml')],text=True)
objects=[x for x in yaml.safe_load_all(raw) if x]
assert not any(x['kind']=='Secret' for x in objects),'Refusing generated credentials in Git'
for obj in objects:
    obj['metadata']['namespace']='supabase-prod'
    if obj['kind']=='ConfigMap' and obj['metadata']['name']=='supabase-prod-functions-main':
        script=obj['data']['index.ts']
        script=script.replace("const VERIFY_JWT", "const JWKS = jose.createLocalJWKSet(JSON.parse(Deno.env.get('SUPABASE_JWKS')!))\nconst VERIFY_JWT",1)
        script=script.replace('await jose.jwtVerify(jwt, secretKey)', "const { alg } = jose.decodeProtectedHeader(jwt)\n    if (alg === 'HS256') await jose.jwtVerify(jwt, secretKey, { algorithms: ['HS256'] })\n    else await jose.jwtVerify(jwt, JWKS, { algorithms: ['ES256'] })")
        obj['data']['index.ts']=script
    if obj['kind']=='ConfigMap' and obj['metadata']['name']=='supabase-prod-kong':
        # Preserve upstream Lua quoting: its entrypoint evals this text before
        # Kong parses YAML, so a generic YAML round-trip is unsafe here.
        original=obj['data']['kong.yml']
        start=original.index('  - name: mcp\n')
        end=original.index('  - name: dashboard\n',start)
        section=original[start:end]
        plugins=section.index('    plugins:\n')
        # The bundled Studio MCP transport intermittently closes reused HTTP/1.1
        # sockets before a response. Scope Connection: close to this route only;
        # retain normal keepalive for REST/Auth/Storage/Realtime and clients.
        section=section[:plugins]+'''    plugins:
      - name: ip-restriction
        config:
          allow:
            - 10.1.1.3/32
      - name: post-function
        config:
          access:
            - |
              ngx.var.upstream_connection = 'close'

'''
        obj['data']['kong.yml']=original[:start]+section+original[end:]
    if obj['kind']!='Deployment':
        continue
    pod=obj['spec']['template']['spec']
    obj['spec']['template']['metadata'].setdefault('labels',{})['homelab.l3b.cc/supabase-production']='true'
    pod['securityContext']=dict(pod.get('securityContext') or {},fsGroup=1000,fsGroupChangePolicy='OnRootMismatch',seccompProfile={'type':'RuntimeDefault'})
    name=obj['metadata']['name']
    config_name=name if name.endswith('-kong') else name+'-main' if name.endswith('-functions') else None
    if config_name:
        config=next(item['data'] for item in objects if item['kind']=='ConfigMap' and item['metadata']['name']==config_name)
        content=yaml.safe_dump(config)
        if name.endswith('-functions'):content+=(root/'gitops/apps/supabase/files/hello.ts').read_text()
        obj['spec']['template']['metadata'].setdefault('annotations',{})['checksum/config']=hashlib.sha256(content.encode()).hexdigest()
    if name.endswith(('-storage','-imgproxy')):
        obj['spec']['strategy']={'type':'Recreate','rollingUpdate':None}
    for container in pod.get('containers',[]):
        env=container.setdefault('env',[])
        envmap={x['name']:x for x in env}
        if 'DB_SSL' in envmap:
            # Postgres URL users consume sslmode; Realtime expects a boolean.
            envmap['DB_SSL']['value']='true' if name.endswith('-realtime') else 'verify-full'
        if 'POSTGRES_BACKEND_URL' in envmap:
            # Logflare's dynamic PostgreSQL adaptor does not pass its Repo CA
            # options to per-source pools. Keep those private-cluster connections
            # on the upstream default until that adaptor supports a custom CA.
            pass
        for key in ['GOTRUE_DB_DATABASE_URL','PGRST_DB_URI','DATABASE_URL','SUPABASE_DB_URL']:
            if key in envmap and '?sslmode=' in envmap[key].get('value',''):
                # URI substitutions must follow the SSL variable definition.
                pass
        env.extend([
            {'name':'PGSSLROOTCERT','value':'/etc/supabase-tls/ca.crt'},
            {'name':'NODE_EXTRA_CA_CERTS','value':'/etc/supabase-tls/ca.crt'},
        ])
        if name.endswith('-meta'):
            env[:]=[item for item in env if item['name']!='PG_META_DB_SSL_MODE']
            env.extend([{'name':'PG_META_DB_SSL_MODE','value':'verify-full'},{'name':'PG_META_DB_SSL_ROOT_CERT','valueFrom':{'secretKeyRef':{'name':'supabase-db-ca','key':'ca.crt'}}}])
        if name.endswith('-analytics'):
            env.extend([
                {'name':'DB_SSL','value':'true'},
                {'name':'DB_SSL_CA_CERT_PATH','value':'/etc/supabase-tls/ca.crt'},
                {'name':'DB_SSL_CLIENT_CERT_PATH','value':'/etc/supabase-client/tls.crt'},
                {'name':'DB_SSL_CLIENT_KEY_PATH','value':'/etc/supabase-client/tls.key'},
            ])
            container.setdefault('volumeMounts',[]).append({'name':'postgres-client','mountPath':'/etc/supabase-client','readOnly':True})
            pod.setdefault('volumes',[]).append({'name':'postgres-client','secret':{'secretName':'supabase-prod-admin-client-cert'}})
        if name.endswith('-realtime'):
            # The stock entrypoint uses sudo. Run its documented release commands
            # directly as nobody instead, retaining the restricted capabilities.
            container['securityContext']['runAsUser']=65534
            container['securityContext']['runAsGroup']=65534
            container['command']=['/bin/sh','-c']
            container['args']=['/app/bin/migrate && /app/bin/realtime eval "Realtime.Release.seeds(Realtime.Repo)" && exec /app/bin/server']
            env.append({'name':'DB_SSL_CA_CERT','value':'/etc/supabase-tls/ca.crt'})
        if name.endswith('-functions'):
            env.append({'name':'SUPABASE_JWKS','valueFrom':{'secretKeyRef':{'name':'supabase-prod-apikey','key':'jwtJwks'}}})
            container.setdefault('volumeMounts',[]).append({'name':'hello-function','mountPath':'/home/deno/functions/hello/index.ts','subPath':'index.ts','readOnly':True})
            pod.setdefault('volumes',[]).append({'name':'hello-function','configMap':{'name':'supabase-prod-functions-hello'}})
        container.setdefault('volumeMounts',[]).append({'name':'postgres-ca','mountPath':'/etc/supabase-tls','readOnly':True})
    pod.setdefault('volumes',[]).append({'name':'postgres-ca','secret':{'secretName':'supabase-db-ca','items':[{'key':'ca.crt','path':'ca.crt'}]}})
    pdb={'apiVersion':'policy/v1','kind':'PodDisruptionBudget','metadata':{'name':name,'namespace':'supabase-prod'},'spec':{'minAvailable':0 if name.endswith(('-storage','-imgproxy')) else 1,'selector':obj['spec']['selector']}}
    # Appended after traversal to keep iteration bounded.
    obj['_pdb']=pdb
extra=[]
for obj in objects:
    if '_pdb' in obj:extra.append(obj.pop('_pdb'))
print(yaml.safe_dump_all(objects+extra,sort_keys=False))
