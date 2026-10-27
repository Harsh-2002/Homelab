import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const base = dirname(fileURLToPath(import.meta.url));
const inv = JSON.parse(readFileSync(join(base, 'inventory.json')));
const internal = process.argv.includes('--internal');
const addresses = internal ? JSON.parse(readFileSync(join(base, 'internal-addresses.local.json'))) : {};
const extra = internal ? JSON.parse(readFileSync(join(base, 'topology-addresses.local.json'))) : {};
const out = internal ? join(base, 'internal') : base;
const sourceDigest=createHash('sha256').update(readFileSync(fileURLToPath(import.meta.url))).update(readFileSync(join(base,'inventory.json')));
if(internal) for(const name of ['internal-addresses.local.json','topology-addresses.local.json']) sourceDigest.update(readFileSync(join(base,name)));
const sourceHash=sourceDigest.digest('hex');
mkdirSync(out, {recursive: true});
const nodes = new Map(), edges = [], elements = [];
const palette = {physical:'#e7eff8', guest:'#e8f4f0', logical:'#f0edf9', service:'#ffffff', device:'#fff3df'};
const endpoint = id => internal ? addresses[id] || extra[id] || '' : '';
const node = (id, name, category='service', detail='') => {
  const ip = endpoint(id);
  if(nodes.has(id)) throw new Error('Duplicate topology node: '+id);
  nodes.set(id, {id, name, category, label:[name, ip || detail].filter(Boolean).join('\n')});
  return id;
};
const edge = (a,b,label='') => edges.push({a,b,label});
const add = (parent,id,name,category='service',detail='',label='') => {node(id,name,category,detail); edge(parent,id,label);};
node('internet','Internet','physical');
add('internet','router','Home router','physical','Model not verified','WAN');
add('router','lan','LAN switching / Ethernet','physical','Switch model & port map unknown','LAN');
add('router','wifi','Home Wi-Fi / AP','physical','AP model not verified','Wi-Fi');
add('wifi','bulb','Wipro bulb','device','Tuya LAN / TCP 6668');
add('wifi','ac','Samsung AC','device','Local DTLS / UDP 49154');
add('lan','camera','Outdoor camera','device','Network attachment type unverified');
add('lan','clients','Your phone / workstation','device','Client addresses vary');
add('internet','tailscale','Tailscale','logical','Subnet routes on px10 / px20 / px30');
add('internet','cloudflare','Cloudflare DNS','logical','DNS records / ACME DNS-01, not a tunnel');
add('internet','model-apis','External model APIs','logical','Hermes: DeepSeek Flash / Codex fallback');
add('internet','github','GitHub / Homelab repository','logical','Declarative configuration');
add('internet','slate','slate / GCP VM','physical','External, documented; no fresh health check');
add('slate','slate-caddy','Caddy'); add('slate','slate-kuma','Uptime Kuma'); add('slate','slate-ntfy','ntfy');
for (const h of inv.hosts) {
  add('lan',h.name,`${h.name} / ${h.model}`,'physical',`${h.cpu} / ${h.ramGB} GB / ZFS`,'1 GbE');
  for (const g of inv.guests.filter(g=>g.host===h.name)) add(h.name,g.name,`${g.kind} ${g.id} / ${g.name}`,'guest');
  add(h.name,h.name+'-zfs','Local ZFS / rpool + data','physical','Guest OS / data volumes');
}
add('px10','usb-av','Crucial X9 Pro / 4 TB','physical','USB: AV + BACKUP','USB');
add('px10','usb-iso','SSD / 256 GB','physical','USB: ISO images / imports','USB');
for (const share of ['AV','BACKUP','ISO']) add('store','share-'+share,`SMB / ${share}`,'service','TCP 445');
add('dev','agents','Coding & personal agents','logical');
for (const a of ['Codex','Claude Code','Hermes','OpenCode']) add('agents',a.toLowerCase().replaceAll(' ','-'),a);
add('opencode','opencode-claude','Claude subscription bridge','service','Loopback only / Agent SDK');
add('opencode-claude','claude-sdk-cli','Claude Code CLI / SDK','logical','Existing CLI-owned Claude Max login');
add('internet','anthropic-subscription','Anthropic / Claude plan','logical','Existing CLI-owned subscription login');
add('dev','herdr','Herdr','service','Terminal sessions');
for (const [p,id,label] of [
 ['proxy','caddy','Caddy / HTTPS + PostgreSQL proxy'],['dns','adguard','AdGuard Home'],['adguard','unbound','Unbound'],
 ['auth','pocketid','Pocket ID / OIDC'],['auth','tinyauth','Tinyauth / forward-auth'],
 ['observability','beszel','Beszel'],['observability','grafana','Grafana'],['observability','victoriametrics','VictoriaMetrics'],
 ['observability','kuma','Uptime Kuma'],['observability','exporters','PVE / node exporters'],
 ['s3','cairn','Cairn S3'],['s3','rustfs','RustFS S3'],['haos','homeassistant','Home Assistant'],['haos','mosquitto','Mosquitto / MQTT']
]) add(p,id,label);
add('orva','quickshare','Quick Share function','service','Upload → temporary object / short URL');
add('ctr','docker','Docker engine','logical','Intel iGPU passed through to ctr');
const stacks = [
 ['media','Media',['jellyfin','frigate','qbittorrent','motrix-server']],
 ['immich-stack','Immich stack',['immich-server','immich-machine-learning','immich-postgres','immich-redis']],
 ['karakeep-stack','Karakeep stack',['karakeep','karakeep-chrome','karakeep-meilisearch']],
 ['paperless-stack','Paperless stack',['paperless','paperless-valkey']],
 ['n8n-stack','Automation stack',['n8n','n8n-db','searxng','sandbox-api','sandbox-runner']],
 ['memory-stack','Shared memory stack',['openviking','openviking-ollama']],
 ['other-apps','Applications & management',['nivra','nivra-theking','opencloud','forgejo','registry','omni','portainer','watchtower','gitea-mirror']]
];
for (const [id,label,services] of stacks) {
  add('docker',id,label,'logical');
  for (const s of services) add(id,s,s,'service',s==='gitea-mirror'?'Restarting / not healthy':'Docker-internal unless published');
}
add('lan','kubernetes','Kubernetes / logical cluster','logical','Members: k8s-201 / 202 / 203');
for (const [id,label,services] of [
 ['kube-network','Cluster networking',['Cilium','CoreDNS']],
 ['kube-platform','Platform / GitOps',['Argo CD','Headlamp','Homepage','metrics-server','vmagent','kube-state-metrics']],
 ['kube-volumes','Distributed block storage',['Longhorn']],
 ['supabase','Supabase suite',['Studio','Kong','Auth','REST','Realtime','Storage','imgproxy','pooler','meta','functions','analytics']],
 ['cnpg','CloudNativePG',['PostgreSQL primary','PostgreSQL standby A','PostgreSQL standby B']]
]) {
  add('kubernetes',id,label,'logical');
  for (const s of services) add(id,'kube-'+s.toLowerCase().replaceAll(' ','-'),s,'service',id==='cnpg'?'Streaming replication':id==='kube-volumes'?'2 replicas per current volume':'Kubernetes Service');
}
for(const g of inv.guests.filter(g=>g.kubernetes)) add(g.name,g.name+'-disk','Longhorn data disk','physical','500 GiB / host-local ZFS');
add('frigate','recordings','Frigate recordings','service','ctr local /data/apps/frigate/media');
const Q = x=>JSON.stringify(x);
const dot = ['digraph G {','graph [rankdir=LR, ordering=out, splines=polyline, nodesep=0.20, ranksep=0.95, margin=0.2];',
 'node [shape=box, fontname="Helvetica", fontsize=15, margin="0.15,0.1"];','edge [arrowsize=0.5];'];
for(const n of nodes.values()) {
  const longest = Math.max(...n.label.split('\n').map(s=>s.length));
  dot.push(`${Q(n.id)} [label=${Q(n.label)}, width=${Math.max(2.7,longest*.14).toFixed(2)}, height=${n.label.includes('\n')?'.8':'.52'}];`);
}
for(const e of edges) dot.push(`${Q(e.a)} -> ${Q(e.b)};`);
dot.push('}');
writeFileSync(join(out,'topology.dot'),dot.join('\n'));
const tokens = line => line.match(/"(?:\\.|[^"\\])*"|\S+/g) || [];
const unq = s=>s.startsWith('"')?JSON.parse(s):s;
const plain = execFileSync('dot',['-Tplain'],{input:dot.join('\n'),encoding:'utf8'}).split('\n').map(tokens);
const size = plain.find(p=>p[0]==='graph'), W=Number(size[2])*72, H=Number(size[3])*72;
let serial=0;
const common = (id,type,x,y,width,height,frameId=null)=>({id,type,x,y,width,height,angle:0,strokeColor:'#263848',backgroundColor:'transparent',fillStyle:'solid',strokeWidth:1.4,strokeStyle:'solid',roughness:0,opacity:100,groupIds:[],frameId,index:null,roundness:null,seed:12345+(serial++),version:1,versionNonce:1,isDeleted:false,boundElements:[],updated:1,link:null,locked:false});
function text(id,x,y,value,size=16,color='#263848',frameId=null) {
 const ls=value.split('\n'); const t={...common(id,'text',x,y,Math.max(...ls.map(s=>s.length))*size*.58,ls.length*size*1.25,frameId),text:value,fontSize:size,fontFamily:2,textAlign:'left',verticalAlign:'top',containerId:null,originalText:value,autoResize:true,lineHeight:1.25,strokeColor:color}; elements.push(t); return t;
}
function shape(id,x,y,w,h,name,fill,frameId,detail='') {
 const r={...common(id,'rectangle',x,y,w,h,frameId),backgroundColor:fill,roundness:{type:3,radius:6}};
 const t=text(id+'-text',x+12,y+10,name,16,'#233647',frameId); t.width=w-24; t.height=h-20; t.autoResize=false; t.containerId=id;
 r.boundElements=[{id:t.id,type:'text'}]; elements.push(r); return r;
}
function arrow(id,points,frameId,color='#9caab4',label='',startId=null,endId=null,dashed=false) {
 const x=points[0][0],y=points[0][1],rel=points.map(p=>[p[0]-x,p[1]-y]);
 const a={...common(id,'arrow',x,y,Math.max(...rel.map(p=>p[0]))-Math.min(...rel.map(p=>p[0])),Math.max(...rel.map(p=>p[1]))-Math.min(...rel.map(p=>p[1])),frameId),points:rel,lastCommittedPoint:null,startBinding:null,endBinding:null,startArrowhead:null,endArrowhead:'arrow',elbowed:false,strokeColor:color,strokeStyle:dashed?'dashed':'solid'};
 if(startId){a.startBinding={elementId:startId,focus:0,gap:5};elements.find(e=>e.id===startId)?.boundElements.push({id,type:'arrow'});}
 if(endId){a.endBinding={elementId:endId,focus:0,gap:5};elements.find(e=>e.id===endId)?.boundElements.push({id,type:'arrow'});}
 elements.push(a);
 if(label) text(id+'-label',(points[0][0]+points.at(-1)[0])/2-label.length*3.5,(points[0][1]+points.at(-1)[1])/2-80,label,13,color,frameId);
}
function frame(id,x,y,w,h,title) {elements.push({...common(id,'frame',x,y,w,h),name:title});text(id+'-title',x+36,y+30,title,30,'#142b3c',id);}
frame('tree',0,0,W+100,H+170,'Homelab / physical → virtual → service tree');
text('tree-key',36,80,`${internal?'INTERNAL / IP:port labels':'Names only / address source not loaded'} · ${inv.verifiedOn} · Arrows show network attachment or service ownership`,17,'#536575','tree');
const coords=new Map();
for (const p of plain.filter(p=>p[0]==='node')) {
 const id=unq(p[1]),cx=Number(p[2])*72+50,cy=H-Number(p[3])*72+130,w=Number(p[4])*72,h=Number(p[5])*72,n=nodes.get(id);
 coords.set(id,{x:cx-w/2,y:cy-h/2,w,h});
 shape(id,cx-w/2,cy-h/2,w,h,n.label,palette[n.category],'tree');
}
plain.filter(p=>p[0]==='edge').forEach((p,i)=>{
 const count=Number(p[3]),pts=[];
 for(let j=0;j<count;j++) pts.push([Number(p[4+j*2])*72+50,H-Number(p[5+j*2])*72+130]);
 arrow('tree-edge-'+i,pts,'tree','#9baab5','',unq(p[1]),unq(p[2]));
});

// Focused data-flow frames live beside the same full-tree scene, not in a remote workspace.
const flows = [
 ['Camera / events to Home Assistant',['camera','frigate','mosquitto','homeassistant'],['RTSP :554','events / MQTT :1883','HA integration']],
 ['Bulb / local control',['clients','homeassistant','bulb'],['HTTPS / app','Tuya LAN :6668']],
 ['AC / local control',['clients','homeassistant','ac'],['HTTPS / app','DTLS / CoAP :49154']],
 ['Media / downloads to playback',['qbittorrent','share-AV','jellyfin','clients'],['writes via SMB3 :445','reads media over SMB3','HTTP playback :8096']],
 ['Temporary sharing',['clients','quickshare','cairn'],['upload via Orva HTTPS','S3 object PUT / GET']],
 ['Container registry',['clients','registry','rustfs'],['Docker Registry API / HTTPS','S3 image layer storage']],
 ['Shared agent memory',['agents','openviking','openviking-ollama','model-apis'],['memory API / account key','local embeddings :11434','separate inference dependency']],
 ['Private browser access',['clients','caddy','tinyauth','pocketid'],['HTTPS :443','selected routes / auth check','OIDC / passkeys']],
 ['Kubernetes membership',['k8s-201','kubernetes','k8s-202','k8s-203'],['member','member / not packet path','member / not packet path']],
 ['Metrics / dashboards',['exporters','victoriametrics','grafana','homeassistant'],['scrape / remote-write','query API','separate API query, not through Grafana']],
 ['Camera / live video',['camera','frigate','homeassistant','clients'],['RTSP :554','authenticated RTSP :8554','HA media / playback']],
 ['Camera / recording storage',['camera','frigate','recordings'],['RTSP main stream','writes local recording files']],
 ['Browser / application request',['clients','caddy','nivra'],['HTTPS :443','HTTP backend :3020']],
 ['DNS / name resolution',['clients','adguard','unbound','internet'],['DNS :53','local recursion :5335','authoritative DNS queries']],
 ['Supabase / database API',['clients','caddy','kube-kong','kube-rest','kube-postgresql-primary'],['HTTPS :443','gateway upstream','REST API','PostgreSQL connection']],
 ['Store / physical media path',['usb-av','store','share-AV','jellyfin'],['host bind mount','encrypted SMB3 :445','media reads']],
 ['Talos / management',['omni','kubernetes'],['manages Talos machines; not app deployment']],
 ['GitOps / desired state',['github','kube-argo-cd','kubernetes'],['tracked manifests / charts','reconciles declared resources']],
 ['Motrix / download to playback',['motrix-server','share-AV','jellyfin','clients'],['writes via SMB3','reads media files','playback']],
 ['Longhorn / replicated volumes',['kube-longhorn','k8s-201-disk','k8s-202-disk','k8s-203-disk'],['eligible disk','eligible disk','eligible disk']],
 ['OpenCode / Claude subscription',['opencode','opencode-claude','claude-sdk-cli','anthropic-subscription'],['local chat / tool bridge','official Agent SDK','Claude CLI / existing Max subscription']]
];
// Maximum five nodes per flow; exact internal endpoints come from the local map.
const flowX=W+240, fw=2800, fh=400;
flows.forEach(([title,ids,labels],i)=>{
 const fy=i*(fh+50),fid='flow-'+i;
 frame(fid,flowX,fy,fw,fh,title);
 const nw=420, gap=110;
 ids.forEach((id,j)=>{
  const n=nodes.get(id),x=flowX+40+j*(nw+gap),y=fy+130;
  shape(`${fid}-${id}`,x,y,nw,90,n.label,palette[n.category],fid);
  if(j)arrow(`${fid}-edge-${j}`,[[x-gap+5,y+45],[x-5,y+45]],fid,'#2c7185',labels[j-1],`${fid}-${ids[j-1]}`,`${fid}-${id}`);
 });
});
// Replace misleading serial membership/metrics chains with explicit fan-out geometry.
function replaceFlow(index,title,center,targets,labels,incoming=[]) {
 const fid='flow-'+index,fy=index*(fh+50);
 for(let i=elements.length-1;i>=0;i--) if(elements[i].frameId===fid || elements[i].id===fid) elements.splice(i,1);
 frame(fid,flowX,fy,fw,fh,title);
 const n=nodes.get(center);shape(fid+'-center',flowX+40,fy+155,420,90,n.label,palette[n.category],fid);
 targets.forEach((id,j)=>{
   const t=nodes.get(id),x=flowX+1000,y=fy+85+j*100;
   shape(fid+'-'+id,x,y,700,80,t.label,palette[t.category],fid);
   let pts=[[flowX+465,fy+200],[flowX+700,fy+200],[flowX+700,y+40],[x-5,y+40]];
   const reverse=incoming.includes(id);if(reverse) pts=pts.reverse();
   arrow(fid+'-branch-'+j,pts,fid,'#2c7185','',reverse?fid+'-'+id:fid+'-center',reverse?fid+'-center':fid+'-'+id,true);
   text(fid+'-label-'+j,flowX+750,y+14,labels[j],14,'#2c7185',fid);
 });
}
replaceFlow(8,'Kubernetes / three VM members','kubernetes',['k8s-201','k8s-202','k8s-203'],['member','member','member'],['k8s-201','k8s-202','k8s-203']);
replaceFlow(9,'Metrics / independent readers','victoriametrics',['grafana','homeassistant','exporters'],['queries API','queries API','scrapes exporters'],['grafana','homeassistant']);
replaceFlow(6,'Memory / independent local and external dependencies','openviking',['agents','openviking-ollama','model-apis'],['memory read / write','local embeddings','remote inference'],['agents']);
replaceFlow(16,'Omni / Talos machine management','omni',['k8s-201','k8s-202','k8s-203'],['machine management','machine management','machine management']);
replaceFlow(19,'Longhorn / 2 replicas per volume, across eligible disks','kube-longhorn',['k8s-201-disk','k8s-202-disk','k8s-203-disk'],['eligible disk','eligible disk','eligible disk']);
const scene={type:'excalidraw',version:2,source:'https://excalidraw.com',elements,appState:{viewBackgroundColor:'#f8fafc',gridSize:null,exportBackground:true,exportWithDarkMode:false},files:{}};
writeFileSync(join(out,'homelab-topology.excalidraw'),JSON.stringify(scene,null,2)+'\n');
writeFileSync(join(out,'topology-manifest.json'),JSON.stringify({date:inv.verifiedOn,internal,sourceHash,nodes:nodes.size,ownershipEdges:edges.length,frames:['tree',...flows.map((_,i)=>'flow-'+i)],width:W+100,height:H+170},null,2)+'\n');
console.log(`Created editable scene: ${nodes.size} nodes, ${edges.length} tree edges, ${flows.length+1} frames. ${Math.round(W)} × ${Math.round(H)} tree canvas.`);
