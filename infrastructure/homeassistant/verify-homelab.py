#!/usr/bin/env python3
"""Read-only HA entity, media and video checks. No credentials/URLs printed."""
import json
import gzip
from pathlib import Path
import time
import urllib.request
from urllib.parse import urljoin, urlsplit, urlunsplit
from websockets.sync.client import connect

values={}
for line in Path('/home/dev/.hermes/.env').read_text().splitlines():
    k,s,v=line.partition('=')
    if s and k in ('HASS_URL','HASS_TOKEN'):values[k]=v.strip().strip('\"\'')
base=values['HASS_URL'].rstrip('/')
headers={'Authorization':'Bearer '+values['HASS_TOKEN']}


def get(path):
    with urllib.request.urlopen(urllib.request.Request(urljoin(base+'/',path),headers=headers),timeout=25) as r:
        data=r.read()
        if r.headers.get('Content-Encoding')=='gzip':data=gzip.decompress(data)
        return r.status,r.headers.get('Content-Type',''),data


u=urlsplit(base)
with connect(urlunsplit(('wss' if u.scheme=='https' else 'ws',u.netloc,'/api/websocket','','')),proxy=None,open_timeout=10) as ws:
    ws.recv();ws.send(json.dumps({'type':'auth','access_token':values['HASS_TOKEN']}))
    assert json.loads(ws.recv())['type']=='auth_ok'
    mid=0

    def call(kind,**kw):
        global mid
        mid+=1;ws.send(json.dumps({'id':mid,'type':kind,**kw}))
        while True:
            r=json.loads(ws.recv(timeout=30))
            if r.get('id')==mid:break
        if not r.get('success'):raise RuntimeError(kind+': '+r.get('error',{}).get('code','failed'))
        return r.get('result')

    states=call('get_states')
    metrics=[x for x in states if x['entity_id'].startswith(('sensor.px10_','sensor.px20_','sensor.px30_'))]
    assert len(metrics)==27
    assert all(x['state'] not in ('unknown','unavailable') for x in metrics)
    print('27 physical-node sensors available')
    for eid in ['camera.outdoor','switch.outdoor_detect','switch.outdoor_recordings','binary_sensor.outdoor_motion','light.behind_monitor_bulb','climate.samsung_room_ac']:
        s=next(x for x in states if x['entity_id']==eid)
        assert s['state'] not in ('unknown','unavailable')
        print(eid,s['state'])
    dash=call('lovelace/config',url_path='homelab-status',force=True)
    assert [v['title'] for v in dash['views']]==['Cameras','Nodes']
    print('Homelab dashboard views ready')
    code,ctype,data=get('/api/camera_proxy/camera.outdoor')
    assert code==200 and ctype.startswith('image/') and len(data)>1000
    print('Camera still verified:',len(data),'bytes')
    media=call('media_source/browse_media',media_content_id='media-source://frigate')
    print('Frigate media browser:',len(media.get('children',[])),'top-level entries')
    stream=call('camera/stream',entity_id='camera.outdoor',format='hls')
    status,ctype,data=get(stream['url'])
    print('HLS master response:',status,ctype,len(data),'bytes')
    assert status==200 and b'#EXTM3U' in data
    variants=[s for s in data.decode().splitlines() if s and not s.startswith('#')]
    status,ctype,data=get(urljoin(urljoin(base,stream['url']),variants[0]))
    assert status==200 and b'#EXTM3U' in data
    segments=[s for s in data.decode().splitlines() if s and not s.startswith('#')]
    assert segments,'HLS media playlist has no segments'
    status,ctype,segment=get(urljoin(urljoin(urljoin(base,stream['url']),variants[0]),segments[0]))
    assert status==200 and len(segment)>1000
    print('Authenticated HLS media segment verified:',len(segment),'bytes')
    print('No recording/detection or appliance control commands sent')
