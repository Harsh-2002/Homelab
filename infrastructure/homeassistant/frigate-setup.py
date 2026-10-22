#!/usr/bin/env python3
"""Scoped operator helper. Secrets stay in process memory and native stores.

Run inspect, mqtt, frigate-stack, or ha-flow. Requires PyYAML and existing
operator access to HA, SSH, Portainer and HomeLab 1Password. No secret output.
"""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import urllib.request
import urllib.error
import yaml


def ssh(host, command, data=None):
    return subprocess.check_output(['ssh', host, command], input=data)


def api(base, path, headers, data=None, method=None):
    req = urllib.request.Request(base.rstrip('/') + path, headers=headers,
        data=json.dumps(data).encode() if data is not None else None, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        if e.code == 400 and 'config_entries/flow' in path:
            detail = json.loads(e.read())
            print({'status':400,'message':detail.get('message','Flow validation failed')})
        raise


hv = {}
for line in Path('/home/dev/.hermes/.env').read_text().splitlines():
    k, sep, val = line.partition('=')
    if sep and k in ('HASS_URL', 'HASS_TOKEN'):
        hv[k] = val.strip().strip('\"\'')
hh = {'Authorization': 'Bearer ' + hv['HASS_TOKEN'], 'Content-Type': 'application/json'}


def ha(path, data=None):
    return api(hv['HASS_URL'], path, hh, data)


def supervisor(path, data=None):
    method = 'POST' if data is not None else 'GET'
    cmd = 'curl -fsS -X '+method+' -H "Authorization: Bearer $SUPERVISOR_TOKEN" -H "Content-Type: application/json" '
    cmd += ('--data-binary @- ' if data is not None else '')+'http://supervisor'+path
    return json.loads(ssh('haos',cmd,json.dumps(data).encode() if data is not None else None))


def frigate_env():
    r = json.loads(ssh('ctr', 'sudo docker inspect frigate --format "{{json .Config.Env}}"'))
    return dict(x.split('=', 1) for x in r if '=' in x)


def install_runtime_config():
    current=yaml.safe_load(ssh('ctr','sudo cat /data/apps/frigate/config/config.yml'))
    desired=yaml.safe_load(Path(__file__).parents[1].joinpath('frigate/config.yml').read_text())
    assert 'outdoor' in current.get('cameras',{})
    go=current.setdefault('go2rtc',{})
    assert 'outdoor' in go.get('streams',{})
    go['rtsp']=desired['go2rtc']['rtsp']
    go['streams']['outdoor_ha']=desired['go2rtc']['streams']['outdoor_ha']
    ssh('ctr','sudo tee /data/apps/frigate/config/config.yml >/dev/null',yaml.safe_dump(current,sort_keys=False).encode())


def op_item(name):
    env = os.environ.copy()
    env['OP_SERVICE_ACCOUNT_TOKEN'] = Path('/home/dev/.config/op/service-account-token').read_text().strip()
    r = json.loads(subprocess.check_output(['op', 'item', 'get', name, '--vault', 'HomeLab', '--format', 'json'], env=env))
    return r, env


phase = sys.argv[1]
if phase == 'inspect':
    item, env = op_item('Portainer')
    token = next(f['value'] for f in item['fields'] if f.get('label') == 'access-token')
    headers = {'X-API-Key': token}
    stacks = api('http://10.1.1.4:9000', '/api/stacks', headers)
    print([{'id':s['Id'], 'name':s['Name'], 'endpoint':s['EndpointId']} for s in stacks if s['Name'] == 'frigate'])
elif phase == 'mqtt':
    e = frigate_env()
    assert e['FRIGATE_MQTT_USER'] and e['FRIGATE_MQTT_PASSWORD']
    info = supervisor('/addons/core_mosquitto/info')['data']
    opts = info['options']
    assert not opts['logins'], 'Do not overwrite existing broker users'
    opts['logins'] = [{'username':e['FRIGATE_MQTT_USER'], 'password':e['FRIGATE_MQTT_PASSWORD']}]
    supervisor('/addons/core_mosquitto/options', {'options':opts,
        'network':{'1883/tcp':1883,'1884/tcp':None,'8883/tcp':None,'8884/tcp':None},
        'boot':'auto','watchdog':True})
    supervisor('/addons/core_mosquitto/start', {})
    print('Mosquitto configured with existing Frigate MQTT credential; auto start/watchdog; only port1883 published')
elif phase == 'frigate-stack':
    item, env = op_item('Portainer')
    token = next(f['value'] for f in item['fields'] if f.get('label') == 'access-token')
    headers = {'X-API-Key':token,'Content-Type':'application/json'}
    stack = next(s for s in api('http://10.1.1.4:9000','/api/stacks',headers) if s['Name']=='frigate')
    path = f"/api/stacks/{stack['Id']}"
    source = api('http://10.1.1.4:9000',path+'/file',headers)['StackFileContent']
    original = yaml.safe_load(source)
    service = original['services']['frigate']
    # Preserve all live stack fields except these narrowly scoped additions.
    service['ports'] = list(dict.fromkeys(service.get('ports',[])+['10.1.1.4:8554:8554']))
    if isinstance(service['environment'], list):
        service['environment'] = dict(x.split('=',1) for x in service['environment'])
    for key in ('FRIGATE_RTSP_USER','FRIGATE_RTSP_PASSWORD'):
        service['environment'][key] = '${'+key+'}'
    vals = {x['name']:x['value'] for x in stack['Env']}
    vals['FRIGATE_MQTT_HOST'] = '10.1.1.13'
    vals.setdefault('FRIGATE_RTSP_USER', 'homeassistant')
    vals.setdefault('FRIGATE_RTSP_PASSWORD', secrets.token_urlsafe(36))
    vault, op_env = op_item('Frigate')
    for key, label, typ in [('FRIGATE_RTSP_USER','RTSP Username','STRING'),('FRIGATE_RTSP_PASSWORD','RTSP Password','CONCEALED')]:
        f = next((f for f in vault['fields'] if f.get('label')==label), None)
        if f is None:
            f={'id':key.lower(),'label':label,'type':typ};vault['fields'].append(f)
        f['value']=vals[key]
    subprocess.run(['op','item','edit',vault['id'],'--vault','HomeLab','--format','json'],
        env=op_env,input=json.dumps(vault).encode(),stdout=subprocess.DEVNULL,check=True)
    # Runtime config is managed via SSH; source contains only env placeholders.
    ssh('ctr','sudo cp -an /data/apps/frigate/config/config.yml /data/apps/frigate/config/config.before-ha-20261022.yml')
    install_runtime_config()
    api('http://10.1.1.4:9000',path+f"?endpointId={stack['EndpointId']}",headers,
        {'StackFileContent':yaml.safe_dump(original,sort_keys=False),'Env':[{'name':k,'value':v} for k,v in vals.items()],
        'Prune':False,'PullImage':False},method='PUT')
    print('Frigate updated through Portainer; MQTT host corrected; authenticated LAN RTSP enabled; credentials in HomeLab/Frigate')
elif phase == 'ha-flow':
    domain=sys.argv[2]
    r=ha('/api/config/config_entries/flow',{'handler':domain,'show_advanced_options':True})
    print({'flow_id':r.get('flow_id'),'type':r.get('type'),'step_id':r.get('step_id'),
        'fields':[x.get('name') for x in r.get('data_schema',[])]})
elif phase == 'mqtt-flow':
    r=ha('/api/config/config_entries/flow/'+sys.argv[2], {'next_step_id':'broker'})
    print({'flow_id':r.get('flow_id'),'type':r.get('type'),'step_id':r.get('step_id'),
        'fields':[x.get('name') for x in r.get('data_schema',[])]})
elif phase == 'mqtt-submit':
    e=frigate_env()
    r=ha('/api/config/config_entries/flow/'+sys.argv[2], {'broker':'10.1.1.13','port':1883,'protocol':'3.1.1',
        'other_settings':{'set_client_cert':False,'set_ca_cert':'off','transport':'tcp'},
        'username':e['FRIGATE_MQTT_USER'],'password':e['FRIGATE_MQTT_PASSWORD']})
    print({'flow_id':r.get('flow_id'),'type':r.get('type'),'step_id':r.get('step_id'),
        'errors':r.get('errors'),'fields':[x.get('name') for x in r.get('data_schema',[])]})
elif phase == 'frigate-submit':
    r=ha('/api/config/config_entries/flow/'+sys.argv[2], {'url':'https://frigate.l3b.cc.cd',
        'username':'','password':'','validate_ssl':True})
    print({'flow_id':r.get('flow_id'),'type':r.get('type'),'step_id':r.get('step_id'),
        'errors':r.get('errors'),'entry_id':r.get('result',{}).get('entry_id')})
elif phase == 'metrics-secret':
    pwd=ssh('root@10.1.1.7','cat /etc/victoriametrics/api-password').decode().strip()
    payload='\nha_victoriametrics_password: '+json.dumps(pwd)+'\n'
    ssh('haos','umask 077; test -f /config/secrets.yaml && cp -an /config/secrets.yaml /config/secrets.before-node-metrics-20261022.yaml; ! grep -q "^ha_victoriametrics_password:" /config/secrets.yaml && { touch /config/secrets.yaml; chmod 600 /config/secrets.yaml; tee -a /config/secrets.yaml >/dev/null; }',payload.encode())
    print('Existing VictoriaMetrics credential saved as protected HA secret; no value displayed')
elif phase == 'frigate-options':
    e=frigate_env()
    r=ha('/api/config/config_entries/options/flow',{'handler':sys.argv[2],'show_advanced_options':True})
    template='rtsp://'+e['FRIGATE_RTSP_USER']+':'+e['FRIGATE_RTSP_PASSWORD']+'@10.1.1.4:8554/{{ name }}_ha'
    r=ha('/api/config/config_entries/options/flow/'+r['flow_id'], {
        'rtsp_url_template':template,'enable_webrtc':False,'notification_proxy_enable':False,
        'media_browser_enable':True,'notification_proxy_expire_after_seconds':0})
    print({'type':r.get('type'),'errors':r.get('errors')})
elif phase == 'frigate-restart':
    item,env=op_item('Portainer')
    token=next(f['value'] for f in item['fields'] if f.get('label')=='access-token')
    headers={'X-API-Key':token,'Content-Type':'application/json'}
    stack=next(s for s in api('http://10.1.1.4:9000','/api/stacks',headers) if s['Name']=='frigate')
    install_runtime_config()
    api('http://10.1.1.4:9000',f"/api/endpoints/{stack['EndpointId']}/docker/containers/frigate/restart?t=30",headers,{},method='POST')
    print('Frigate targeted restart via Portainer after config update; recordings preserved')
else:
    raise SystemExit('Unknown phase')
