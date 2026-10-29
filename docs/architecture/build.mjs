import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// Deterministic, dependency-free source for the share-safe architecture sheets.
const out = dirname(fileURLToPath(import.meta.url));
const inventory = JSON.parse(readFileSync(join(out, 'inventory.json'), 'utf8'));
const internal = process.argv.includes('--internal');
const addresses = internal ? JSON.parse(readFileSync(join(out, 'internal-addresses.local.json'), 'utf8')) : {};
const output = internal ? join(out, 'internal') : out;
mkdirSync(output, { recursive: true });
const labelDate = new Date(inventory.verifiedOn + 'T00:00:00Z').toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});
const C = { ink: '#18252c', muted: '#52636d', line: '#c7d2d7', paper: '#f8fafb',
  white: '#ffffff', blue: '#225d82', blueBg: '#edf4f8', teal: '#25675d', tealBg: '#edf5f1' };
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
let shapes;
function text(x, y, value, size = 23, color = C.ink, weight = 400, extra = '') {
  shapes.push(`<text x="${x}" y="${y}" font-size="${size}" fill="${color}" font-weight="${weight}" ${extra}>${esc(value)}</text>`);
}
function box(x, y, w, h, fill = C.white, stroke = C.line, r = 12) {
  shapes.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>`);
}
function path(d, color = C.line, dashed = false, arrow = false, width = 2) {
  shapes.push(`<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linejoin="round" ${dashed ? 'stroke-dasharray="7 7"' : ''} ${arrow ? `marker-end="url(#${color === C.teal ? 'tealArrow' : 'arrow'})"` : ''}/>`);
}
function lines(x, y, values, size = 22, leading = 31, color = C.muted) {
  values.forEach((s, i) => text(x, y + i * leading, s, size, color));
}
function node(x, y, w, h, title, body = [], fill = C.white) {
  shapes.push('<g data-node="true">');
  box(x, y, w, h, fill);
  const compact = h < 90;
  const dense = h <= 60;
  text(x + 22, y + (compact ? 27 : 34), title, compact ? 23 : 25, C.ink, 600);
  lines(x + 22, y + (dense ? 48 : compact ? 52 : 65), body, dense ? 17 : compact ? 20 : 21, 29);
  shapes.push('</g>');
}
function begin(title, subtitle, page) {
  shapes = [];
  shapes.push(`<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="1820" viewBox="0 0 2400 1820" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(subtitle)}. Architecture snapshot verified ${labelDate}. ${internal ? 'Internal LAN addresses included. Credentials omitted.' : 'Share-safe. IP addresses and credentials omitted.'}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="${C.muted}"/></marker><marker id="tealArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="${C.teal}"/></marker></defs><rect width="2400" height="1820" fill="${C.paper}"/><g font-family="Arial, Liberation Sans, sans-serif">`);
  text(64, 82, title, 46, C.ink, 600);
  text(64, 122, subtitle, 23, C.muted);
  text(2336, 77, `l3b / ${labelDate}`, 23, C.muted, 400, 'text-anchor="end"');
  text(2336, 113, `${page} / ${internal ? 3 : 2}`, 21, C.muted, 400, 'text-anchor="end"');
}
function end(name, footer) {
  path('M64 1732H2336');
  text(64, 1771, footer, 20, C.muted);
  text(2336, 1771, internal ? 'INTERNAL · LAN addresses included' : 'Share-safe · editable SVG', 20, C.muted, 400, 'text-anchor="end"');
  shapes.push('</g></svg>');
  writeFileSync(join(output, name + '.svg'), shapes.join('\n') + '\n');
}

begin('Homelab architecture', 'Physical hosts, service placement and the shared platform.', 1);
node(64, 166, 392, 150, 'People & devices', ['Browser · phone · workstation', 'Home LAN or remote Tailscale']);
node(512, 166, 868, 150, 'Two access paths', [
  'Public: Internet → router → Caddy → selected services',
  'Private: LAN / Tailscale → Caddy or native LAN protocols',
  'Tailscale subnet routing runs on all three Proxmox hosts.'
], C.blueBg);
node(1436, 166, 396, 150, 'Cloudflare', ['DNS-only records · DNS-01 TLS', 'Private defaults; public exceptions', 'DNS is not a traffic tunnel.']);
node(1888, 166, 448, 150, 'slate · external GCP VM', ['Caddy · Uptime Kuma · ntfy', 'Independent monitoring & alerts', 'Checks home over Tailscale']);
path('M456 241H510', C.muted, false, true);
path('M1436 241H1382', C.muted, true, true);
path('M946 316V362', C.muted, false, true);
box(64, 366, 2272, 64, C.white);
text(88, 406, 'Home router / LAN fabric', 25, C.ink, 600);
text(660, 406, 'Ethernet: 1 Gb/s full duplex verified at px10, px20 and px30', 23, C.muted);
text(2312, 406, 'Wi-Fi → bulb & AC', 23, C.muted, 400, 'text-anchor="end"');
for (const x of [424, 1200, 1976]) path(`M${x} 430V478`, C.muted, false, true);

const hostY = 482, hostH = 650;
function host(x, name, model, cpu, ramGB) {
  box(x, hostY, 720, hostH, C.white, '#aebfc7', 16);
  text(x + 24, 523, name, 32, C.ink, 600);
  text(x + 696, 520, model, 24, C.muted, 400, 'text-anchor="end"');
  text(x + 24, 558, `${cpu} · ${ramGB} GB RAM · ZFS OS + data pools`, 22, C.muted);
  path(`M${x + 24} 578H${x + 696}`);
}
for (const [i, h] of inventory.hosts.entries()) {
  const x = 64 + i * 776;
  host(x, h.name + (inventory.maintenance?.node === h.name ? " · maintenance" : ""), h.model, h.cpu, h.ramGB);
  if (internal) text(x + 190, 523, addresses[h.name] || '', 20, C.blue);
}
for (const g of inventory.guests) {
  const x = 88 + inventory.hosts.findIndex(h => h.name === g.host) * 776;
  node(x, g.slot[0], 672, g.slot[1], `${g.name} · ${g.kind} ${g.id}${g.state ? " · stopped" : ""}${g.titleSuffix || ''}`, g.body.slice(0, g.slot[1] < 90 ? 1 : Math.max(1, Math.floor((g.slot[1] - 65) / 29) + 1)), g.kubernetes ? C.blueBg : C.white);
  if (internal) text(x + 650, g.slot[0] + (g.slot[1] < 90 ? 27 : 34), addresses[g.name] || '', 18, C.blue, 400, 'text-anchor="end"');
}
for (const x of [424, 1200, 1976]) path(`M${x} 1106V1176`, C.blue, true);
path('M424 1176H1976', C.blue, true);
path('M1200 1176V1212', C.muted, true, true);
text(64, 1160, 'Placement is a snapshot; managed guests can relocate.', 20, C.muted);

box(64, 1218, 2272, 282, C.blueBg, '#b5cbd8', 16);
text(88, 1258, inventory.maintenance ? 'Kubernetes: two active nodes; k8s-203 stopped for hardware swap' : 'One Kubernetes cluster across all three physical hosts', 29, C.ink, 600);
text(88, 1294, 'Talos management: Omni on ctr. Kubernetes desired state: GitHub → Argo CD.', 23, C.muted);
path('M812 1324V1474'); path('M1568 1324V1474');
text(88, 1348, 'Networking & operations', 25, C.blue, 600);
lines(88, 1384, inventory.kubernetes.network, 22, 32);
text(844, 1348, 'Persistent storage', 25, C.blue, 600);
lines(844, 1384, inventory.kubernetes.storage, 22, 32);
text(1600, 1348, 'Supabase', 25, C.blue, 600);
lines(1600, 1384, inventory.kubernetes.supabase, 22, 32);

text(64, 1560, 'Storage boundaries', 27, C.ink, 600);
text(840, 1560, 'Availability boundaries', 27, C.ink, 600);
text(1616, 1560, 'Smart home', 27, C.ink, 600);
lines(64, 1600, ['ZFS → VM/LXC disks and selected 5-minute replicas', 'USB on px10: 4 TB AV / BACKUP + 256 GB ISO', 'ctr local data → app state; S3 → Cairn / RustFS objects'], 22, 34);
lines(840, 1600, ['Proxmox HA manages the listed non-Kubernetes guests.', 'USB shares need physical-disk recovery after host loss.', 'DNS, Caddy and several apps remain single instances.'], 22, 34);
lines(1616, 1600, ['Home Assistant → Wipro bulb / Tuya LAN', 'Home Assistant → Samsung AC / local DTLS', 'Frigate → camera feeds; HA → viewing / automation'], 22, 34);
end('homelab', 'Logical LAN fabric shown; router, switch/AP models and exact cabling have not been audited.');

begin('How traffic and data move', 'The important connections, without drawing every packet or replica.', 2);

text(64, 188, 'Web access & identity', 28, C.ink, 600);
node(64, 214, 420, 114, 'Client', ['LAN / Tailscale for private apps', 'Internet for selected public apps']);
node(560, 214, 486, 114, 'Caddy · proxy LXC', ['HTTPS termination → backend routes', 'Source restrictions per service']);
node(1122, 214, 486, 114, 'Application', ['Native login / API credentials', 'No blanket public or SSO bypass']);
node(1684, 214, 652, 114, 'Pocket ID + Tinyauth · auth LXC', ['Native OIDC where supported', 'Caddy forward-auth for selected browser routes']);
path('M484 270H558', C.muted, false, true);
path('M1046 270H1120', C.muted, false, true);
path('M2010 328V358H804V330', C.teal, true, true);
text(1122, 389, 'Identity is a policy dependency; API/MCP routes retain their own authentication.', 21, C.muted);
text(64, 389, 'Name lookup: AdGuard → Unbound', 22, C.blue, 600);
path('M64 430H2336');

text(64, 481, 'GitOps & cluster operations', 28, C.ink, 600);
node(64, 507, 420, 112, 'GitHub · Homelab repository', ['Declarative non-secret configuration', 'Reviewed changes → desired state']);
node(560, 507, 486, 112, 'Argo CD · Kubernetes', ['Reconciles tracked applications', 'Signed public webhook; private UI']);
node(1122, 507, 486, 112, 'Talos / Kubernetes', ['Cilium network · Longhorn volumes', inventory.maintenance ? 'k8s-201 / 202 active; k8s-203 stopped' : 'Services scheduled across three VMs']);
node(1684, 507, 652, 112, 'Omni · ctr', ['Manages the three Talos machines', 'Runs on ctr, not inside Kubernetes']);
path('M484 563H558', C.muted, true, true);
path('M1046 563H1120', C.muted, true, true);
path('M1684 563H1610', C.teal, true, true);
text(64, 658, 'Longhorn: storage-level replicas. CloudNativePG: separate PostgreSQL streaming replicas and failover.', 22, C.muted);
path('M64 700H2336');

text(64, 751, 'Agents & shared memory', 28, C.ink, 600);
node(64, 777, 420, 122, 'dev · four agents', ['Codex · Claude Code', 'Hermes · OpenCode']);
node(560, 777, 486, 122, 'OpenViking · ctr', ['Shared account-scoped memory', 'Native plugins / provider and MCP']);
node(1122, 777, 486, 122, 'Ollama · ctr', ['Local embedding service', 'Not the agents’ primary chat model']);
node(1684, 777, 652, 122, 'Tools & integrations', ['Orva · Nivra · Supabase · browser / developer MCPs', 'Hermes → Karakeep CLI / Home Assistant API']);
path('M484 838H558', C.muted, false, true);
path('M1046 838H1120', C.muted, false, true);
path('M274 899V929H2010V901', C.teal, true, true);
text(560, 961, 'Hermes: Go / DeepSeek + Codex fallback. OpenCode: Claude Agent SDK. Telegram / iMessage → Hermes.', 22, C.muted);
path('M64 1003H2336');

text(64, 1054, 'Media & object storage', 28, C.ink, 600);
node(64, 1080, 690, 186, 'Media path', [], C.tealBg);
text(88, 1155, 'qBittorrent / Motrix → Store AV share → Jellyfin', 23, C.ink, 600);
lines(88, 1193, ['Encrypted SMB3 directly over the LAN; not through Caddy.', 'Media stays on Store’s USB SSD, not ctr’s OS disk.'], 21, 30);
node(832, 1080, 710, 186, 'Temporary sharing', [], C.tealBg);
text(856, 1155, 'Quick Share CLI → Orva function → Cairn S3', 23, C.ink, 600);
lines(856, 1193, ['Short Orva share URL → function proxy → object download.', 'Cairn is a separate native service on the s3 LXC.'], 21, 30);
node(1620, 1080, 716, 186, 'Container images', [], C.tealBg);
text(1644, 1155, 'Docker client → Registry → RustFS S3', 23, C.ink, 600);
lines(1644, 1193, ['Registry runs on ctr; image layers live in RustFS.', 'Cairn and RustFS share one LXC / host failure domain.'], 21, 30);
text(64, 1307, 'Proxmox nodes use Store BACKUP / ISO over SMB directly. App databases remain on their own local or block volumes.', 22, C.muted);
path('M64 1348H2336');

text(64, 1399, 'Home automation & visibility', 28, C.ink, 600);
node(64, 1425, 420, 124, 'Hermes / user', ['Home Assistant API / app', 'Existing authenticated access']);
node(560, 1425, 486, 124, 'Home Assistant · haos', ['Wipro bulb → Tuya LAN', 'Samsung AC → local DTLS / CoAP']);
node(1122, 1425, 486, 124, 'Frigate · ctr / Intel iGPU', ['Camera ingest / recording', 'RTSP restream + MQTT → HA']);
node(1684, 1425, 652, 124, 'Metrics · observability LXC', ['Exporters + Kubernetes vmagent → VictoriaMetrics', 'Grafana / HA node views; Beszel / Kuma monitoring']);
path('M484 1487H558', C.muted, false, true);
path('M1122 1487H1048', C.muted, false, true);
text(64, 1600, 'Local device protocols avoid cloud commands; a full WAN-outage acceptance test remains outstanding.', 22, C.muted);
text(64, 1650, 'Solid arrows: application / data path', 21, C.muted);
path('M475 1643H540', C.muted, false, true);
text(620, 1650, 'Dashed arrows: configuration / dependency', 21, C.muted);
path('M1152 1643H1217', C.teal, true, true);
text(1320, 1650, 'Not a live health map; see the inventory notes for verification limits.', 21, C.muted);
end('flows', 'Schemas are simplified; replicated storage and HA are not independent backups.');

if (internal) {
  begin('Internal connection reference', 'LAN endpoints; native protocols do not all pass through HTTPS.', 3);
  const entries = Object.entries(addresses);
  entries.forEach(([name, endpoint], i) => {
    const col = i % 3, row = Math.floor(i / 3), x = 64 + col * 776, y = 200 + row * 145;
    node(x, y, 720, 112, name, [endpoint]);
  });
  end('endpoints', 'Internal-only copy. Never publish this sheet, its address source or its exports to public Git.');
}
console.log(`Built ${internal ? 'internal' : 'share-safe'} SVGs from inventory.json.`);
