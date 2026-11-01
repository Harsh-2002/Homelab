import {readFileSync,writeFileSync,readdirSync,existsSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {homedir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const base=dirname(fileURLToPath(import.meta.url));
const dir=process.argv.includes('--internal')?join(base,'internal'):base;
const container=process.env.EXCALIDRAW_BROWSER_CONTAINER;
if(container) {
 const manifest=JSON.parse(readFileSync(join(dir,'topology-manifest.json')));
 const scene='/tmp/homelab-architecture-scene.excalidraw';
 const png='/tmp/homelab-architecture-frame.png';
 const browser=execFileSync('docker',['exec',container,'node','-e',
  'console.log(require("/app/node_modules/playwright-core").chromium.executablePath())'],{encoding:'utf8'}).trim();
 try {
  execFileSync('docker',['exec','-i',container,'node','-e',
   'require("node:fs").writeFileSync(process.argv[1],require("node:fs").readFileSync(0),{mode:0o600})',scene],
   {input:readFileSync(join(dir,'homelab-topology.excalidraw'))});
  for(const frame of manifest.frames) {
   execFileSync('docker',['exec',container,'npx','--yes','@excalidraw/cli@0.2.0','render',scene,
    '--frame-id',frame,'--out',png,'--browser-path',browser,'--fonts-url','none',
    '--max-width','4000','--max-height','4000','--timeout','60000'],{stdio:['ignore','pipe','pipe'],timeout:90000});
   const bytes=execFileSync('docker',['exec',container,'node','-e',
    'process.stdout.write(require("node:fs").readFileSync(process.argv[1]))',png],{maxBuffer:50*1024*1024});
   writeFileSync(join(dir,frame==='tree'?'topology-tree.png':frame+'.png'),bytes);
  }
 } finally {
  execFileSync('docker',['exec',container,'node','-e',
   'for (const p of process.argv.slice(1)) require("node:fs").rmSync(p,{force:true})',scene,png]);
 }
 console.log(`Verified official CLI rendering of ${manifest.frames.length} frames using the local Docker browser.`);
 process.exit(0);
}
const cache=join(homedir(),'.cache/ms-playwright');
const candidates=existsSync(cache)?readdirSync(cache).filter(x=>/^chromium-\d+$/.test(x)).sort((a,b)=>Number(b.split('-')[1])-Number(a.split('-')[1])).map(x=>join(cache,x,'chrome-linux64/chrome')):[];
const browser=process.env.EXCALIDRAW_BROWSER_PATH||candidates.find(existsSync);
if(!browser) throw new Error('Set EXCALIDRAW_BROWSER_PATH to an installed browser; no browser is automatically downloaded.');
const manifest=JSON.parse(readFileSync(join(dir,'topology-manifest.json')));
for(const frame of manifest.frames) {
 const out=join(dir,frame==='tree'?'topology-tree.png':frame+'.png');
 execFileSync('excalidraw',['render',join(dir,'homelab-topology.excalidraw'),'--frame-id',frame,'--out',out,'--browser-path',browser,'--fonts-url','none','--max-width','8000','--max-height','8000','--timeout','60000'],{stdio:['ignore','pipe','pipe'],timeout:70000});
}
console.log(`Verified official CLI rendering of all ${manifest.frames.length} frames to ${dir}.`);
