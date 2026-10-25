// Export the existing scene, never rebuild it: preserve native/manual edits.
import {readFileSync,writeFileSync,readdirSync,existsSync} from 'node:fs';
import {createServer} from 'node:http';
import {dirname,join,resolve,sep,extname} from 'node:path';
import {homedir} from 'node:os';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';

const base=dirname(fileURLToPath(import.meta.url));
const internal=process.argv.includes('--internal');
const dir=internal?join(base,'internal'):base;
const cli=process.env.EXCALIDRAW_CLI_DIR||join(homedir(),'.local/lib/node_modules/@excalidraw/cli');
const mermaid=process.env.MERMAID_DIR||join(homedir(),'.local/share/nivra-checks/mcp-candidate/node_modules/mermaid');
if(!existsSync(join(mermaid,'dist/mermaid.esm.min.mjs'))) throw new Error('Set MERMAID_DIR to an installed Mermaid package directory.');
const {chromium}=await import(pathToFileURL(join(cli,'node_modules/playwright-core/index.mjs')).href);
const cache=join(homedir(),'.cache/ms-playwright');
const browserPath=process.env.EXCALIDRAW_BROWSER_PATH||readdirSync(cache).filter(x=>/^chromium-\d+$/.test(x)).sort((a,b)=>Number(b.split('-')[1])-Number(a.split('-')[1])).map(x=>join(cache,x,'chrome-linux64/chrome')).find(existsSync);
if(!browserPath) throw new Error('Set EXCALIDRAW_BROWSER_PATH to an existing Chromium.');
const scene=JSON.parse(readFileSync(join(dir,'homelab-topology.excalidraw'),'utf8'));
const all=new Map(scene.elements.filter(e=>!e.isDeleted).map(e=>[e.id,e]));
const frames=[...all.values()].filter(e=>e.type==='frame');
const escapeLabel=s=>s.replaceAll('&','&amp;').replaceAll('"','#quot;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('|','#124;').replaceAll('\n','<br/>');

function mermaidSource(frame,combined=false) {
 const shapes=[...all.values()].filter(e=>e.frameId===frame.id && ['rectangle','ellipse','diamond'].includes(e.type));
 const ids=new Map(shapes.map((e,i)=>[e.id,`n_${frame.id.replace(/\W/g,'_')}_${i}`]));
 const lines=combined?[`subgraph f_${frame.id.replace(/\W/g,'_')}["${escapeLabel(frame.name)}"]`,'direction LR']:['flowchart LR'];
 const colors=[...new Set(shapes.map(e=>e.backgroundColor))];
 for(const e of shapes) {
  const text=(e.boundElements||[]).filter(b=>b.type==='text').map(b=>all.get(b.id)?.text||'').join('\n');
  const label=escapeLabel(text||e.id);
  lines.push(`  ${ids.get(e.id)}["${label}"]`);
 }
 let edges=0;
 for(const e of all.values()) if(e.frameId===frame.id && e.type==='arrow') {
  const a=ids.get(e.startBinding?.elementId), b=ids.get(e.endBinding?.elementId);
  assert(a&&b,`Unbound/unsupported arrow in ${frame.id}: ${e.id}`);
  const labelElement=all.get(e.id+'-label')||all.get(e.id.replace(/-branch-(\d+)$/,'-label-$1'));
  const label=labelElement?.text;
  const connector=e.strokeStyle==='dashed'?'-.->':'-->';
  lines.push(`  ${a} ${connector}${label?'|"'+escapeLabel(label)+'"|':''} ${b}`);edges++;
 }
 colors.forEach((color,i)=>{
  assert(/^#[0-9a-f]{6}$/i.test(color),'unexpected fill value');
  const name=`c_${frame.id.replace(/\W/g,'_')}_${i}`;
  lines.push(`  classDef ${name} fill:${color},stroke:#6c7f8c,color:#233647;`);
  lines.push(`  class ${shapes.filter(e=>e.backgroundColor===color).map(e=>ids.get(e.id)).join(',')} ${name};`);
 });
 if(combined) lines.push('end');
 return {source:lines.join('\n')+'\n',nodes:shapes.length,edges};
}

const sources=frames.map(frame=>({frame,...mermaidSource(frame)}));
for(const item of sources) writeFileSync(join(dir,item.frame.id==='tree'?'homelab-topology.mmd':item.frame.id+'.mmd'),item.source);
const combined='flowchart TB\n'+frames.map(f=>mermaidSource(f,true).source).join('\n');
writeFileSync(join(dir,'homelab-complete.mmd'),combined);
writeFileSync(join(dir,'homelab-mermaid.md'),'# Homelab topology and flows\n\n'+(internal?'Internal IP edition. Do not publish.':'Address-free reference edition.')+'\n\n'+sources.map(i=>`## ${i.frame.name}\n\n\`\`\`mermaid\n${i.source}\`\`\`\n`).join('\n'));

// Serve ONLY installed public renderer assets, loopback-only, for this export.
const roots={'/excalidraw/':join(cli,'dist'),'/mermaid/':join(mermaid,'dist')};
const server=createServer((req,res)=>{
 try {
  const url=new URL(req.url,'http://localhost').pathname;
  if(url==='/'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><meta charset="utf-8"><title>Local diagram export</title>');return;}
  const prefix=Object.keys(roots).find(p=>url.startsWith(p));
  if(!prefix){res.writeHead(404).end();return;}
  const root=resolve(roots[prefix]),target=resolve(root,decodeURIComponent(url.slice(prefix.length)));
  if(!target.startsWith(root+sep)||!['.js','.mjs','.json','.woff','.woff2','.css'].includes(extname(target))){res.writeHead(403).end();return;}
  res.setHeader('Content-Type',({'.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.woff2':'font/woff2','.woff':'font/woff','.css':'text/css'})[extname(target)]);
  res.end(readFileSync(target));
 }catch{res.writeHead(404).end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=`http://127.0.0.1:${server.address().port}`;
let browser;
try {
 browser=await chromium.launch({headless:true,executablePath:browserPath});
 const page=await browser.newPage();
 await page.goto(origin);
 await page.evaluate(async origin=>{
  window.EXCALIDRAW_ASSET_PATH=origin+'/excalidraw/';
  window.nativeExporter=await import(origin+'/excalidraw/renderer.js');
  window.mermaid=(await import(origin+'/mermaid/mermaid.esm.min.mjs')).default;
  window.mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'neutral',maxEdges:2000,maxTextSize:1000000});
 },origin);
 const exportSvg=async(elements)=>page.evaluate(async({elements,appState,files})=>{
   // Official CLI 0.2.0 bundles the data/config export wrapper, not the older
   // React package's flat options signature. Re-check after CLI upgrades.
   const svg=await window.nativeExporter.exportToSvg({data:{elements,appState:{...appState,exportBackground:true,exportWithDarkMode:false,exportEmbedScene:false},files},config:{padding:24}});
   return svg.outerHTML;
 },{elements,appState:scene.appState,files:scene.files||{}});
 for(const frame of frames){
  const elements=[...all.values()].filter(e=>e.frameId===frame.id);
  const svg=await exportSvg(elements);
  assert(svg.includes('<text')&&!svg.includes('<image'),'Expected true-vector SVG, not a raster wrapper.');
  writeFileSync(join(dir,frame.id==='tree'?'homelab-topology.svg':frame.id+'.svg'),svg+'\n');
 }
 writeFileSync(join(dir,'homelab-complete.svg'),(await exportSvg([...all.values()]))+'\n');
 for(const {frame,source} of sources) await page.evaluate(async({frame,source})=>{const parsed=await window.mermaid.parse(source);if(!parsed)throw new Error('Mermaid parse failed: '+frame);},{frame:frame.id,source});
 await page.evaluate(async source=>window.mermaid.parse(source),combined);
 const rendered=await page.evaluate(async source=>(await window.mermaid.render('topologyMermaid',source)).svg,sources.find(s=>s.frame.id==='tree').source);
 writeFileSync(join(dir,'homelab-mermaid.svg'),rendered+'\n');
 const tree=sources.find(s=>s.frame.id==='tree');
 assert.equal(tree.nodes,[...all.values()].filter(e=>e.frameId==='tree'&&['rectangle','ellipse','diamond'].includes(e.type)).length);
 assert.equal(tree.edges,[...all.values()].filter(e=>e.frameId==='tree'&&e.type==='arrow').length);
 if(!internal) for(const data of [combined,rendered])assert(!/\b(?:\d{1,3}\.){3}\d{1,3}\b/.test(data),'IP in public export');
 console.log(`Exported native SVG + Mermaid for ${frames.length} frames; tree ${tree.nodes} nodes / ${tree.edges} edges. Mermaid parsed all frames + combined source and rendered the tree.`);
} finally {
 await browser?.close();
 await new Promise(r=>server.close(r));
}
