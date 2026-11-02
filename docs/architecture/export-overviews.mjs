// Export current SVG sheets locally through the already-running tool browser.
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const base = dirname(fileURLToPath(import.meta.url));
const dir = process.argv.includes('--internal') ? join(base, 'internal') : base;
const container = process.env.EXCALIDRAW_BROWSER_CONTAINER || 'playwright';
const source = ['homelab', 'flows'].map(name => readFileSync(join(dir, name + '.svg'), 'utf8'));
const code = `
const fs=require('node:fs');
const {chromium}=require('/app/node_modules/playwright-core');
(async()=>{
 const source=JSON.parse(fs.readFileSync(0,'utf8'));
 const browser=await chromium.connectOverCDP('http://127.0.0.1:9222');
 const context=await browser.newContext({viewport:{width:2400,height:1820}});
 try {
  const page=await context.newPage(); const images=[];
  for(const svg of source){
   await page.setContent('<style>body{margin:0}svg{display:block}</style>'+svg);
   images.push((await page.screenshot()).toString('base64'));
  }
  await page.setContent('<style>@page{size:2400px 1820px;margin:0}body{margin:0}section{width:2400px;height:1820px;break-after:page}section:last-child{break-after:auto}svg{display:block}*{-webkit-print-color-adjust:exact}</style>'+source.map(svg=>'<section>'+svg+'</section>').join(''));
  const pdf=await page.pdf({preferCSSPageSize:true,printBackground:true});
  console.log(JSON.stringify({images,pdf:pdf.toString('base64')}));
 } finally {await context.close()}
 process.exit(0);
})().catch(()=>{console.error('Local overview export failed');process.exit(1)});
`;
const result = JSON.parse(execFileSync('docker', ['exec', '-i', container, 'node', '-e', code], {
  input: JSON.stringify(source), encoding: 'utf8', maxBuffer: 50 * 1024 * 1024, timeout: 90000,
}));
for (const [index, name] of ['homelab', 'flows'].entries()) {
  writeFileSync(join(dir, name + '.png'), Buffer.from(result.images[index], 'base64'));
}
writeFileSync(join(dir, 'homelab-architecture.pdf'), Buffer.from(result.pdf, 'base64'));
console.log('Exported current overview PNGs and two-page PDF locally.');
