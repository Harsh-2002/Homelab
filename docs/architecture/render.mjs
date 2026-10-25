// Optional export step: npm install --prefix /tmp/homelab-diagram-render playwright
// PLAYWRIGHT_MODULE=/tmp/homelab-diagram-render/node_modules/playwright/index.mjs \
//   node docs/architecture/render.mjs [--internal]
// Set CHROMIUM_EXECUTABLE if using an existing browser rather than Playwright's.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = dirname(fileURLToPath(import.meta.url));
const internal = process.argv.includes('--internal');
const dir = internal ? join(base, 'internal') : base;
const names = internal ? ['homelab', 'flows', 'endpoints'] : ['homelab', 'flows'];
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE || undefined });
const page = await browser.newPage({viewport: {width: 2400, height: 1820}, deviceScaleFactor: 1.5});
const all = [];
try {
  for (const name of names) {
    const svg = readFileSync(join(dir, name + '.svg'), 'utf8');
    all.push(svg);
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.screenshot({path: join(dir, name + '.png'), fullPage: true});
    const defects = await page.locator('svg text').evaluateAll(nodes => nodes.flatMap(n => {
      const b = n.getBBox();
      return b.x < 0 || b.y < 0 || b.x + b.width > 2400 || b.y + b.height > 1820 ? [n.textContent] : [];
    }));
    if (defects.length) throw new Error('Out-of-canvas text: ' + defects.join('; '));
    const overflow = await page.locator('g[data-node]').evaluateAll(groups => groups.flatMap(g => {
      const r = g.querySelector('rect').getBBox();
      return [...g.querySelectorAll('text')].flatMap(t => {
        const b = t.getBBox();
        return b.x < r.x + 10 || b.x + b.width > r.x + r.width - 10 || b.y + b.height > r.y + r.height - 5 ? [t.textContent] : [];
      });
    }));
    if (overflow.length) throw new Error('Node text overflow: ' + overflow.join('; '));
  }
  await page.setContent(`<html><head><style>@page{size:2400px 1820px;margin:0}body{margin:0}svg{display:block;break-after:page}svg:last-child{break-after:auto}</style></head><body>${all.join('')}</body></html>`);
  await page.pdf({path:join(dir, 'homelab-architecture.pdf'), printBackground:true, preferCSSPageSize:true});
  console.log(`Exported ${names.length} PNGs and PDF to ${dir}.`);
} finally { await browser.close(); }
