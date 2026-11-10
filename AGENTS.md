# Homelab operating instructions

Preserve credentials, private state and unrelated work. Never print expanded
credential-bearing agent configurations. Keep shared tooling synchronized across
Codex, Claude Code, Hermes and OpenCode, preserving native memory integrations.
Run `python3 infrastructure/agents/check-integrations.py` after agent changes.

## Living architecture

Current deployment is one Debian Docker host. WireGuard is the chosen VPN;
the owner retired Tailscale on 2 November 2026. Do not install/re-enroll it or
restore historical tailnet routing. Docker publishes only 53/UDP and 443/TCP+UDP;
keep container communication on service names and management ports internal.
Owner's network plan: LAN 10.1.1.0/24, WireGuard peers 10.1.2.0/24,
Docker custom bridge `l3b` 10.1.3.0/24 with gateway 10.1.3.1. Do not restore
the superseded 172.17.0.0/16 bridge or old native-host gateway aliases.
Let Docker manage its bridge/NAT/publication firewall rules, and the existing
WireGuard manager own VPN forwarding. Do not add manual iptables rules for
application routing. Caddy owns HTTP source/auth gates.

Browser automation uses Playwright CLI plus the owner-approved Docker Browser Use
runtime (10 November 2026) for OpenCode and Hermes. Browser Use runs through the
`browser-use` launcher with separate agent sessions; see `infrastructure/browser`.
Keep the official `playwright-cli` skill under `~/.agents/skills/playwright-cli`.
Use it for navigation, form filling, UI/UX review, responsive checks,
screenshots, console/network inspection and E2E work. Reuse the named CLI
session; close it when done. Do not add or use Playwright MCP, Chrome DevTools
MCP, `agent-browser`, Puppeteer-based agent tools or another browser MCP.
DNS: internal AdGuard may use wildcard rewrites. Public Cloudflare must have no
wildcard DNS; add exact DNS-only private mappings for deployed private services.
Only explicitly approved public services get exact public-IP records and a
matching public Caddy policy. Owner-approved public app origins are `notes`,
`pin`, `photos` and `drive`; Orva and all core services stay private. Wildcard
TLS certificates are independent of DNS.
Host networking uses native systemd-networkd only for eno1; keep Docker/WireGuard
links unmanaged by it. DNS belongs in the same .network file and flows through
systemd-resolved's generated uplink file, with stub/public fallback disabled.
Do not restore ifupdown/resolvconf or add Netplan as another configuration layer.
Use generic single-word stack names and actual single-word service/container
names. The owner has now authorized OpenViking memory restoration/integration
for OpenCode and the native OpenCode HTTPS remote UI; keep existing identities
and do not restore Codex/Claude client configuration or run a second OpenCode.
Supabase is retired: do not deploy it or restore its MCP/skills.
The owner explicitly chose automatic memory transcript capture with redaction
filters, and the previous OpenCode vault password for remote access (invalidates
current logins, never session history). Follow the native handover runbook.

Primary artifact is now the owner's internal Excalidraw topology tree/flow board,
not the rejected presentation sheets. Update `excalidraw-build.mjs`, rebuild and
render with the official CLI after material changes; see docs/architecture.
Keep IP-bearing native scenes, address sources and exports Git-ignored.

Material changes to hosts, VM/LXC placement, services, network access, storage,
identity, HA or integrations must update `docs/architecture/inventory.json` and
the affected relationships in `docs/architecture/build.mjs`, alongside service
runbooks. Rebuild with `node docs/architecture/build.mjs` **and**
`node docs/architecture/excalidraw-build.mjs`; the second one refreshes
`topology-manifest.json` and is required after any inventory or layout change,
or CI fails with `stale topology: source changed`. Validate with
`node docs/architecture/check.mjs` and `node docs/architecture/check-topology.mjs`,
and visually inspect the changed diagrams.
Refresh exported PNG/PDF files when publishing a new architecture snapshot.

Keep the public SVGs and inventory share-safe. The optional private address
source and internal exports are Git-ignored; never force-add them. Do not infer
hardware, cabling, health, failover guarantees or service existence from old
runbooks or example diagrams. Check actual current state where relevant.

Record meaningful changes in the Homelab Notion runbook and OpenViking, then
commit and push the completed scoped work. Do not leave those steps for the
owner to request again. Follow the owner's requested branch workflow and
preserve concurrent changes. Verify remote HEAD before claiming a push.
