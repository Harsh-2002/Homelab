import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';

const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

function layout(inv, addresses = {}) {
  const pages = [{id:'tree', title:'l3b / physical → Docker → service tree', nodes:[], edges:[]},
    {id:'core-flow', title:'l3b / DNS, HTTPS, identity and persistent data', nodes:[], edges:[]}];
  const add = (page, id, x, y, title, body = [], fill = '#edf4f8') => {
    const wrap = value => {
      const lines=[]; let line='';
      for(const word of value.split(' ')) {
        if(line && line.length+word.length+1>36) {lines.push(line);line='';}
        line+=(line?' ':'')+word;
      }
      if(line) lines.push(line);
      return lines;
    };
    const lines = [title, ...body, ...(addresses[id] ? [addresses[id]] : [])].flatMap(wrap);
    pages[page].nodes.push({id,x,y,w:380,h:Math.max(118,lines.length*25+18),lines,fill});
  };
  const edge = (page,a,b) => pages[page].edges.push({a,b});
  add(0,'clients',55,620,'Phone / workstation',['Private LAN access']);
  add(0,'lan',500,620,'LAN',['Physical path not re-audited']);
  add(0,'l3b',945,620,inv.host.name+' / '+inv.host.model,[inv.host.cpu,inv.host.ram+' / Debian 13.7','Native networkd + resolved','Playwright CLI browser']);
  add(0,'docker',1390,160,'Docker engine / l3b bridge',['One bare-metal Debian host','Dedicated subnet; service-name routing','Embedded DNS → internal AdGuard']);
  add(0,'wireguard',1390,620,'WireGuard / native host',['Routed LAN access; no source NAT','iPhone accepted; MacBook not yet tested']);
  add(0,'opencode',1390,800,'OpenCode / native host',['Session history preserved; no duplicate',inv.opencodeRemote?.state==='verified'?'Private HTTPS / browser verified':'Private HTTPS / handover pending']);
  add(0,'nvme',1390,990,'Samsung NVMe / XFS',['Root OS; Docker-managed runtime','Images and named volumes']);
  add(0,'data',1390,1150,'Seagate SATA / XFS',['/data/apps/<service>','Application bind data']);
  add(0,'backup',1390,1310,'Crucial USB / ext4',['Existing backup mounted temporarily','Not current-node backup coverage']);
  for (const [a,b] of [['clients','lan'],['lan','l3b'],['l3b','docker'],['l3b','wireguard'],['l3b','opencode'],['l3b','nvme'],['l3b','data'],['l3b','backup']]) edge(0,a,b);
  const groups = [
    ['portainer','Portainer / management',['Saved users / 30 legacy stack files','Browser login and local engine verified']],
    ['core-dns','dns / AdGuard and Unbound',['AdGuard Home → public Unbound image','Only UDP DNS published; UI via Caddy']],
    ['core-proxy','proxy / Caddy',['Custom Caddy binary / saved certificates','Only HTTPS TCP/UDP published']],
    ['core-identity','identity / Pocket ID and Tinyauth',['Container: pocketid / tinyauth','Original identity and OIDC clients']],
    ['homepage','dashboard / Homepage',['Private apex; Tinyauth forward-auth','Only current core service cards']],
    ['memory','memory / OpenViking and Ollama',['Restored context; local embeddings','OpenCode plugin and memory skills']],
    ['apps','apps / Portainer restores',['16 running app stacks; Forgejo retained stopped','media, docs, automation, HA, git, registry and S3']],
    ['hermes','Hermes / native',['Telegram, Photon/iMessage and API server connected','OpenViking provider; Playwright CLI only']],
    ['smb','smb / Samba shares',['Host-native smbd; TCP 445, LAN only','MEDIA + BACKUP (USB SSD, Time Machine)']]
  ];
  groups.forEach(([id,title,body],i)=>{add(0,id,1835,170+i*185,title,body,'#edf5f1');edge(0,'docker',id);});

  if (inv.localDeviceIntegrations?.some(device => device.id === 'gaming-pc-plug')) {
    add(0,'homeassistant-local',55,920,'Home Assistant / local devices',['Shared Smart Plugs dashboard','One device filter; guarded controls']);
    add(0,'gaming-pc-plug',500,920,'Gaming PC / 10A smart plug',['Tuya 3.5 over LAN','Reserved address; local telemetry','Energy calculated from power']);
    edge(0,'l3b','homeassistant-local');
    edge(0,'homeassistant-local','gaming-pc-plug');
  }

  add(1,'flow-client',80,260,'DNS clients',['LAN / WireGuard / host / Docker','Host: native systemd-networkd','Internal AdGuard; no public fallback']);
  add(1,'flow-adguard',650,260,'AdGuard Home',['UDP DNS only; UI through Caddy','Internal apex / wildcard rewrites']);
  add(1,'flow-unbound',1220,260,'Unbound',['Recursion; DNSSEC validation']);
  add(1,'flow-root',1790,260,'Authoritative DNS',['External recursion, not forwarding']);
  for (const [a,b] of [['flow-client','flow-adguard'],['flow-adguard','flow-unbound'],['flow-unbound','flow-root']]) edge(1,a,b);
  add(1,'flow-browser',80,620,'Browser',['Existing service subdomains']);
  add(1,'flow-caddy',650,620,'Caddy',['Source denial before auth/proxy','Public DNS: exact names, no wildcard','DNS-01 TLS; no HTTP listener']);
  add(1,'flow-apps',1220,620,'Portainer / AdGuard UI',['Portainer: native authentication','AdGuard: Tinyauth forward-auth']);
  add(1,'flow-tinyauth',650,870,'Tinyauth',['DNS / Homepage UI forward-auth']);
  add(1,'flow-homepage',1790,620,'Homepage / private apex',['Current core cards and DNS metrics','No host port or Docker socket']);
  edge(1,'flow-caddy','flow-homepage');
  add(1,'flow-memory',1790,870,'OpenViking / Ollama',['Native OpenCode recall and capture','API key; Studio additionally SSO']);
  edge(1,'flow-homepage','flow-memory');
  add(1,'flow-opencode',1790,1060,'OpenCode / native',['Official plugin / automatic memory',inv.opencodeRemote?.state==='verified'?'Private HTTPS / browser verified':'Private HTTPS / handover pending']);
  edge(1,'flow-opencode','flow-memory');
  add(1,'flow-pocket',1220,870,'Pocket ID',['OIDC / original passkeys','Human sign-in acceptance pending']);
  for (const [a,b] of [['flow-browser','flow-caddy'],['flow-caddy','flow-apps'],['flow-caddy','flow-tinyauth'],['flow-tinyauth','flow-pocket'],['flow-apps','flow-pocket']]) edge(1,a,b);
  add(1,'flow-portainer',80,1240,'Portainer API',['Reviewed stack definitions','No automatic legacy-stack restore']);
  add(1,'flow-docker',650,1240,'Docker / l3b bridge',['Stack lifecycle; dedicated subnet']);
  add(1,'flow-data',1220,1240,'SATA application data',['Service-specific bind directories']);
  add(1,'flow-runtime',1790,1240,'NVMe Docker state',['Images / runtime / named volumes']);
  for (const [a,b] of [['flow-portainer','flow-docker'],['flow-docker','flow-data'],['flow-docker','flow-runtime']]) edge(1,a,b);
  if (inv.localDeviceIntegrations?.some(device => device.id === 'gaming-pc-plug')) {
    add(1,'flow-ha-local',80,1470,'Home Assistant / Tuya Local',['Private Smart Plugs dashboard','One filter; estimated kWh history']);
    add(1,'flow-pc-plug',650,1470,'PC smart plug / LAN',['Tuya 3.5; TCP 6668','Local key; no routine cloud login']);
    edge(1,'flow-ha-local','flow-pc-plug');
  }
  return pages;
}

function segment(page, edge) {
  const a=page.nodes.find(n=>n.id===edge.a),b=page.nodes.find(n=>n.id===edge.b);
  if(b.x>a.x+a.w+400 && a.y===b.y) return [[a.x+a.w/2,a.y+a.h],
    [a.x+a.w/2,a.y+a.h+85],[b.x+b.w/2,b.y+b.h+85],[b.x+b.w/2,b.y+b.h]];
  if(b.x>a.x) return [[a.x+a.w,a.y+a.h/2],[b.x,b.y+b.h/2]];
  if(b.x<a.x) return [[a.x,a.y+a.h/2],[b.x+b.w,b.y+b.h/2]];
  if(b.y>a.y) return [[a.x+a.w/2,a.y+a.h],[b.x+b.w/2,b.y]];
  return [[a.x+a.w/2,a.y],[b.x+b.w/2,b.y+b.h]];
}

export function renderSingleNodeSheets(base, inv, internal=false) {
  const output=internal?join(base,'internal'):base;
  const addresses=internal?JSON.parse(readFileSync(join(base,'internal-addresses.local.json'))):{};
  mkdirSync(output,{recursive:true});
  for (const [index,page] of layout(inv,addresses).entries()) {
    const body=[`<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="1820" viewBox="0 0 2400 1820" role="img"><title>${esc(page.title)}</title><desc>Single-node Docker restoration verified ${inv.verifiedOn}; historical cluster not recreated.</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#52636d"/></marker></defs><rect width="2400" height="1820" fill="#f8fafb"/><g font-family="Arial, sans-serif">`,
      `<text x="55" y="76" font-size="36">${esc(page.title)}</text>`,
      `<text x="55" y="120" font-size="21">${inv.verifiedOn} · Single host, no HA claim · OpenViking memory restored</text>`];
    for (const e of page.edges) {
      const points=segment(page,e);
      body.push(`<path d="${points.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join('')}" fill="none" stroke="#52636d" stroke-width="2" marker-end="url(#arrow)"/>`);
    }
    for (const n of page.nodes) {
      body.push(`<g data-node="true"><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="10" fill="${n.fill}" stroke="#aebfc7"/>`);
      n.lines.forEach((line,i)=>body.push(`<text x="${n.x+14}" y="${n.y+27+i*25}" font-size="${i?16:19}" fill="#18252c">${esc(line)}</text>`));
      body.push('</g>');
    }
    body.push('<text x="55" y="1730" font-size="20">Existing backups preserved; passkey/OIDC and paid model acceptance require separate tests.</text></g></svg>');
    writeFileSync(join(output,(index?'flows':'homelab')+'.svg'),body.join('\n')+'\n');
  }
}

export function buildSingleNodeScene(base,inv,internal=false) {
  const output=internal?join(base,'internal'):base;
  const addresses=internal?JSON.parse(readFileSync(join(base,'internal-addresses.local.json'))):{};
  const digest=createHash('sha256').update(readFileSync(join(base,'excalidraw-build.mjs')))
    .update(readFileSync(join(base,'inventory.json'))).update(readFileSync(join(base,'single-node.mjs')));
  if(internal) digest.update(readFileSync(join(base,'internal-addresses.local.json')));
  const elements=[];let serial=0;
  const common=(id,type,x,y,width,height,frameId=null)=>({id,type,x,y,width,height,frameId,angle:0,
    strokeColor:'#263848',backgroundColor:'transparent',fillStyle:'solid',strokeWidth:1.5,
    strokeStyle:'solid',roughness:0,opacity:100,groupIds:[],roundness:null,seed:1+serial++,version:1,
    versionNonce:1,isDeleted:false,boundElements:[],updated:1,link:null,locked:false});
  for (const [index,page] of layout(inv,addresses).entries()) {
    const offset=index*1900;
    elements.push({...common(page.id,'frame',0,offset,2400,1820),name:page.title});
    const text=(id,x,y,value,size=16,containerId=null)=>{
      const lines=value.split('\n');
      elements.push({...common(id,'text',x,y,Math.max(...lines.map(s=>s.length))*size*.58,lines.length*size*1.25,page.id),
        text:value,originalText:value,fontSize:size,fontFamily:2,textAlign:'left',verticalAlign:'top',
        containerId,autoResize:true,lineHeight:1.25});
    };
    text(page.id+'-title',55,offset+40,page.title,30);
    text(page.id+'-key',55,offset+95,inv.verifiedOn+' / One Debian host / No VM or LXC restore / No HA claim',19);
    for(const n of page.nodes) {
      elements.push({...common(n.id,'rectangle',n.x,n.y+offset,n.w,n.h,page.id),
        backgroundColor:n.fill,roundness:{type:3},boundElements:[{id:n.id+'-text',type:'text'}]});
      text(n.id+'-text',n.x+14,n.y+offset+14,n.lines.join('\n'),16,n.id);
    }
    for(const [i,e] of page.edges.entries()) {
      const points=segment(page,e),a=points[0],id=page.id+'-edge-'+i;
      elements.push({...common(id,'arrow',a[0],a[1]+offset,Math.max(...points.map(p=>p[0]))-Math.min(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))-Math.min(...points.map(p=>p[1])),page.id),
        points:points.map(p=>[p[0]-a[0],p[1]-a[1]]),lastCommittedPoint:null,startArrowhead:null,endArrowhead:'arrow',
        startBinding:{elementId:e.a,focus:0,gap:0},endBinding:{elementId:e.b,focus:0,gap:0},elbowed:false});
      for(const target of [e.a,e.b]) elements.find(el=>el.id===target).boundElements.push({id,type:'arrow'});
    }
    text(page.id+'-limits',55,offset+1680,'Hermes gateway active; OpenCode and WireGuard intentionally stay native.\nExisting USB backup preserved; new-node backup coverage not established.',18);
  }
  mkdirSync(output,{recursive:true});
  writeFileSync(join(output,'homelab-topology.excalidraw'),JSON.stringify({type:'excalidraw',version:2,
    source:'https://excalidraw.com',elements,appState:{viewBackgroundColor:'#f8fafb'},files:{}},null,2)+'\n');
  writeFileSync(join(output,'topology-manifest.json'),JSON.stringify({sourceHash:digest.digest('hex'),
    frames:['tree','core-flow'],nodes:layout(inv).flatMap(page=>page.nodes.map(n=>n.id))},null,2)+'\n');
}
