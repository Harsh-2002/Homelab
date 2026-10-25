# Homelab architecture

Share-safe architecture snapshot verified on **25 October 2026**. The reference
image supplied by the owner informed the subject and completeness, not its
hardware inventory. These are technical diagrams, not generated illustrations.

- [Physical hosts and service placement](homelab.svg)
- [Traffic, identity and data flows](flows.svg)
- [Share-safe PDF](homelab-architecture.pdf)

The owner also requested an **internal IP edition**. Locally, `internal/` contains
the matching overview/flows and a third endpoint-reference sheet, plus PNGs and
a combined PDF. It is Git-ignored. Its optional address source is
`internal-addresses.local.json`, also ignored; credentials never belong there.
Run `node docs/architecture/build.mjs --internal` when that local source exists.
The public build never reads it.

Private IPs, public IPs, MACs, serial numbers, account identifiers, credentials
and operational tokens are deliberately absent from the diagrams. Host names,
software names and hardware models are retained. This is not a live health map.

## Rebuild

```bash
node docs/architecture/build.mjs
```

`inventory.json` owns hosts, placement, grouped services and cluster inventory.
The dependency-free generator owns relationships and layout. Change verified
inventory there, rebuild both SVGs and visually inspect them. SVGs contain
real text, accessible titles/descriptions and no remote images, fonts or scripts.
They can be opened in a browser, Inkscape, Figma or a vector editor. The optional
renderer exports PNG and a two-page PDF using Playwright; see render.mjs.

## Maintenance contract

This is a living part of the Homelab runbook. For a host/service addition,
removal, relocation, network/storage/identity change or significant integration:

1. Inspect authoritative live state; do not treat old memory as proof.
2. Update inventory.json and relevant connector/flow labels in build.mjs.
3. Update the verification date after actual checks; record limitations here.
4. Rebuild SVGs, run `node docs/architecture/check.mjs`, export PNG/PDF, and
   inspect text, connections and privacy. Rebuild the private edition separately.
5. Update affected service docs, Notion and OpenViking; commit/push scoped work.

The root AGENTS.md makes this part of the agent workflow. GitHub Actions checks
inventory consistency, public privacy rules and deterministic/stale SVG output.
It does not discover infrastructure automatically or prove runtime health. An
agent can still miss a required inventory edit; live review remains necessary.
PNG/PDF regeneration is explicit, not silently performed by public CI. The private
source is never uploaded to CI. Future changes should not require a new diagram
service, a paid editor or hand-editing binary files.

The initial build passed independent visual review (disposition: ship), both
editions passed out-of-canvas and node-text bounds checks, the design detector
reported no findings, and shared four-agent integration parity passed. PNGs are
deterministic browser exports of the SVG source, not generated imagery; embedded
provenance records that origin. Preserve/re-embed it when replacing PNG exports.

## Verified physical and guest placement

| Host | Physical hardware | Running guests |
| --- | --- | --- |
| px10 | Dell OptiPlex 5060, i5-8400T, 6 cores, 32 GB RAM | dev VM100; observability LXC104; store LXC109; Talos VM201 |
| px20 | Dell OptiPlex 5060, i5-8400T, 6 cores, 32 GB RAM | orva VM106; ctr VM204; Talos VM202 |
| px30 | Dell OptiPlex 7040, i5-6500TE, 4 cores, 32 GB RAM | proxy LXC101; dns LXC102; auth LXC103; s3 LXC105; haos VM107; Talos VM203 |

All three physical NICs reported 1000 Mb/s, full duplex, link detected. Each host
has separate rpool and data ZFS pools. No dedicated switch, router/AP model,
physical port map, upstream bandwidth, VLAN topology or UPS inventory was
verified, so none is invented. The LAN line is a logical network, not a claim
that every cable is plugged directly into the router. Guest placement can change
through HA or maintenance.

## Workload inventory

- **dev:** running Hermes gateway/dashboard and OpenCode services; Codex and
  Claude Code installed CLI agents; Herdr and shared tools/skills/MCP. Agents are
  not represented as four always-running daemons. A Nivra development service is
  also running; development workloads are grouped rather than individually drawn.
- **ctr:** running Docker inventory includes Portainer, Jellyfin, qBittorrent,
  Motrix, Immich server/ML/PostgreSQL/Valkey, Karakeep/Chrome/Meilisearch,
  OpenCloud, Paperless/Valkey, Forgejo, Registry, n8n/PostgreSQL, SearXNG,
  sandbox API/runner, Nivra and a separate friend instance, OpenViking/Ollama,
  Omni and the maintained Watchtower updater. Frigate uses the passed-through
  Intel iGPU. **gitea-mirror is present but restarting**, so it is shown as an
  installed mirror worker, not declared healthy. No repair is in scope here.
- **proxy:** Caddy. **dns:** AdGuard Home and Unbound. **auth:** Pocket ID and
  Tinyauth. **s3:** native Cairn and RustFS. Those services were checked active.
- **observability:** native Beszel, Grafana, VictoriaMetrics, Uptime Kuma,
  PVE exporter and node exporter were confirmed running. The unit name is
  `victoriametrics`, not `victoria-metrics`.
- **Store:** Samba and host binds for AV, BACKUP and ISO. All three px10 ext4
  mounts and the cluster BACKUP/ISO CIFS storages were active. Store's OS disk
  replication excludes USB-bound data. USB media is not magically replicated.
- **Orva:** independent serverless VM; Quick Share uses Cairn, not the RustFS
  Registry bucket. Detailed function behavior is sourced from its runbook,
  not exercised with uploads during this read-only inventory.
- **HAOS:** dedicated Home Assistant VM; Frigate and existing local Wipro/Samsung
  integrations as recorded in their accepted runbooks. No appliance commands,
  video captures, resets or WAN-disconnection tests were run for the diagram.
- **Kubernetes:** all three Talos nodes Ready. Argo CD, Cilium, CoreDNS, Longhorn,
  Headlamp, Homepage, metrics-server, kube-state-metrics, vmagent and
  CloudNativePG are included. Auxiliary controllers, CSI sidecars and test pods
  are grouped or omitted, not misrepresented as separate user-facing services.
- **Supabase:** existing suite deployments ready; CloudNativePG reports three
  ready instances. Kong, Studio, Auth, REST, Realtime, Storage, imgproxy,
  pooler, meta, functions and analytics are included/grouped. Storage is a
  **single replica** using a Longhorn block volume with recovery, not active-active
  shared NFS. Current Longhorn volumes each have **two** storage replicas.
- **slate:** external GCP VM with Caddy, ntfy and Uptime Kuma, sourced from its
  maintained runbook. Fresh SSH validation required a Tailscale re-auth check;
  it was cancelled rather than bypassed. This diagram does not claim a fresh
  external health check.

ARR, Readarr, Lidarr, PocketBase, Anchor, Coolify, ZimaOS, Termix and Warpgate are
retired and intentionally excluded. Old directories describe history, not live
services. No extra Proxmox node, Pi, radio hub or switch is inferred from the
example image or old brainstorming.

## Evidence and limitations

Read-only sources: Proxmox cluster resources/nodes/HA/replication/storage APIs;
per-host DMI/CPU/ZFS/ethtool; Docker names/status; Kubernetes nodes,
Deployments/StatefulSets, CloudNativePG and Longhorn CRs; selected native service
states; tracked proxy, DNS, registry, storage, agents and Home Assistant runbooks.
No expanded configurations or credentials were dumped or copied into assets.

Proxmox HA currently lists all ten non-Kubernetes guests; their configured
local-ZFS replication jobs run every five minutes. This is restart/relocation
HA, with asynchronous replication and application downtime, not active-active
services or a zero-data-loss guarantee. Store additionally requires the actual
USB disks. DNS and proxy remain single instances with dependencies. Longhorn
replication is separate from PostgreSQL streaming replication and from backups.

The diagram is an overview, not a firewall audit, security certification, wire
capture, complete database dependency model or failover test. See the individual
runbooks for exact private addresses, native authentication and recovery steps.
