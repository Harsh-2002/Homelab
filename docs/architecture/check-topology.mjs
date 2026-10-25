import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const base=dirname(fileURLToPath(import.meta.url));
const internal=process.argv.includes('--internal');
const dir=internal?join(base,'internal'):base;
const raw=readFileSync(join(dir,'homelab-topology.excalidraw'),'utf8');
const scene=JSON.parse(raw), els=new Map(scene.elements.map(e=>[e.id,e]));
const manifest=JSON.parse(readFileSync(join(dir,'topology-manifest.json')));
const digest=createHash('sha256').update(readFileSync(join(base,'excalidraw-build.mjs'))).update(readFileSync(join(base,'inventory.json')));
if(internal) for(const name of ['internal-addresses.local.json','topology-addresses.local.json']) digest.update(readFileSync(join(base,name)));
const hash=digest.digest('hex');
assert.equal(manifest.sourceHash,hash,'stale topology: source changed; rebuild the native scene');
assert.equal(scene.type,'excalidraw');assert.equal(scene.version,2);
assert.equal(els.size,scene.elements.length,'duplicate native element IDs');
for(const el of els.values()) {
 assert([el.x,el.y,el.width,el.height].every(Number.isFinite),el.id+': invalid geometry');
 if(el.frameId) assert.equal(els.get(el.frameId)?.type,'frame',el.id+': missing frame');
 if(el.containerId) assert(els.has(el.containerId),el.id+': missing text container');
 for(const b of [el.startBinding,el.endBinding].filter(Boolean)) assert(els.has(b.elementId),el.id+': broken arrow binding');
 if(el.type==='arrow') assert(el.points.length>=2 && el.points.flat().every(Number.isFinite),el.id+': invalid arrow');
}
if(!internal) assert(!/\b(?:\d{1,3}\.){3}\d{1,3}\b/.test(raw),'IP address in public scene');
const texts=scene.elements.filter(e=>e.type==='text').map(e=>e.text).join('\n');
for(const label of ['Home router','LAN switching','Outdoor camera','Wipro bulb','Samsung AC','Docker engine','Kubernetes','Home Assistant','Cairn','RustFS','Supabase']) assert(texts.includes(label),'missing '+label);
console.log(`PASS: ${internal?'internal':'public'} editable scene; ${els.size} unique elements, native arrow/text bindings, required coverage${internal?'':', no IP addresses'}.`);
