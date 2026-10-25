import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
const base = dirname(fileURLToPath(import.meta.url));
const inventory = JSON.parse(readFileSync(join(base, 'inventory.json'), 'utf8'));
assert.match(inventory.verifiedOn, /^\d{4}-\d{2}-\d{2}$/);
const hosts = new Set(inventory.hosts.map(h => h.name));
assert.equal(hosts.size, inventory.hosts.length, 'duplicate hosts');
const ids = new Set();
for (const g of inventory.guests) {
  assert(hosts.has(g.host), 'unknown host');
  assert(!ids.has(g.id), 'duplicate guest ID'); ids.add(g.id);
  assert(g.slot[0] >= 596 && g.slot[0] + g.slot[1] <= 1106, 'guest outside host');
  for (const other of inventory.guests) {
    if (other !== g && other.host === g.host) {
      assert(g.slot[0] >= other.slot[0] + other.slot[1] || other.slot[0] >= g.slot[0] + g.slot[1], 'overlapping guest rows');
    }
  }
}
for (const name of ['homelab', 'flows']) {
  const svg = readFileSync(join(base, name + '.svg'), 'utf8');
  assert(svg.includes('<title') && svg.includes('<desc'), 'missing accessibility labels');
  assert(!/<script|<foreignObject|https?:\/\//i.test(svg.replace('http://www.w3.org/2000/svg', '')), 'unexpected external content');
  assert(!/\b(?:\d{1,3}\.){3}\d{1,3}\b|Bearer\s|api[_-]?key\s*[:=]/i.test(svg), 'private address / credential marker in public SVG');
  if (name === 'homelab') for (const g of inventory.guests) assert(svg.includes(`${g.kind} ${g.id}`), `missing guest ${g.id}`);
}
console.log(`PASS: ${hosts.size} hosts, ${ids.size} guests, valid layout slots, public SVG privacy/accessibility checks.`);
