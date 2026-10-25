import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {homedir} from 'node:os';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const base=dirname(fileURLToPath(import.meta.url));
const dir=process.argv.includes('--internal')?join(base,'internal'):base;
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
