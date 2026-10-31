# Homelab architecture

## Current: px30 unavailable, 31 October afternoon

px30 is unreachable since15:45IST; the owner subsequently confirmed it is off and unplugged. DNS/identity/S3 run on px10; proxy and Home Assistant run on px20. Six HA node-affinity rules temporarily exclude px30 to prevent repeated failback. The offline maintenance request was rejected, so this is rule-based isolation, not active node maintenance. Kubernetes has two Ready nodes; the unavailable third host and degraded standby/storage state remain under investigation. See [afternoon incident](../../infrastructure/proxmox/INCIDENT-2026-10-31-AFTERNOON.md).

## Earlier recovery reverified, 31 October 2026

See the [31 October incident and recovery](../../infrastructure/proxmox/INCIDENT-2026-10-31.md). Normal ownership is restored again. HA capacity is limited: px10 OOM-killed Docker VM204 during failover. px20’s abrupt loss and px30’s unsolicited power-key events remain under investigation; no sleep entry was recorded.

All three physical hosts and Talos VMs are online. Proxy, DNS, identity, S3 and
Home Assistant are back on px30; px10 retains dev/observability/store and px20
retains Orva/Docker. HA maintenance, Kubernetes cordon/Longhorn eviction and
replication pauses are cleared. VM100's temporary memory settings are restored.
The verified replacement is OptiPlex5060, i5-9400T, six cores and32GiB RAM.
All hosts run kernel7.0.14-26-pve and manager9.2.24; obsolete kernels are removed.

See [return-to-service validation and cleanup](../../infrastructure/proxmox/RETURN-TO-SERVICE.md).
Earlier power/reset evidence remains documented; successful return does not
prove its original cause. The inventory and current exports show normal service
ownership rather than the historical evacuation. IP-bearing exports stay ignored.

## Current direction: internal Excalidraw topology

The owner rejected the original presentation sheets. The primary purpose is
**understanding the full internal tree and actual flows**, not public sharing.
Use the native `internal/homelab-topology.excalidraw` scene: a connected physical
→ host → VM/LXC → Docker/Kubernetes/service tree, plus focused flow frames on the
same editable canvas. IP:port labels are included. Open it in Excalidraw with
Open file; it is not a flattened image. The Netgear switch and host ports are verified; router/AP and remaining cabling unknowns are marked.

```bash
node docs/architecture/excalidraw-build.mjs --internal
node docs/architecture/excalidraw-render.mjs --internal
```

The official CLI is installed and requires no account for local rendering.
See [tool setup](../../infrastructure/agents/EXCALIDRAW.md). The tree layout uses
Graphviz as a helper, then writes editable native shapes/text/bound arrows.
The default build omits addresses; the internal build reads two Git-ignored
local address maps. Do not force-add those or upload the internal scene.

Host/guest placement is in inventory.json; individual service nodes, containment
and flow paths are in excalidraw-build.mjs. Update both when relevant. The source
hash check rejects stale generated scenes, including changes to local address
maps for the internal edition. Building regenerates the scene: preserve any
manual Excalidraw edits before rebuilding, or carry those edits into the source.
Rendering an existing scene does not regenerate its geometry.

### SVG and Mermaid exports

```bash
node docs/architecture/export-formats.mjs --internal
```

This exports the **existing** native scene, preserving its labels/connections
and any manual edits. It does not regenerate or restyle the scene.

- `internal/homelab-topology.svg`: native Excalidraw topology tree, true vector.
- `internal/homelab-complete.svg`: complete board, including all flow frames.
- `internal/homelab-topology.mmd`: Mermaid topology tree.
- `internal/homelab-complete.mmd`: all frames as Mermaid subgraphs.
- `internal/homelab-mermaid.md`: separate readable Mermaid blocks for all frames.
- `internal/homelab-mermaid.svg`: Mermaid-rendered topology (automatic layout,
  same graph, not identical Excalidraw positioning).
- Individual flow frames also receive `.svg` and `.mmd` exports.

These contain internal addresses and remain Git-ignored. The default command
without `--internal` exports only the existing address-free reference scene.
The helper reads neither private map during a public export.

SVG uses `exportToSvg` from the renderer bundled with official CLI 0.2.0, through
an ephemeral loopback-only asset server and the existing Chromium. The CLI's
`render` command itself supports PNG, not a pretend `--format svg` flag. No
cloud upload, account or API key is involved. Re-check that bundled API after
CLI upgrades; 0.2.0 uses the `data/config` wrapper.

Mermaid validation/rendering uses an installed Mermaid package. Set
`MERMAID_DIR` to its package directory when the existing local developer-tool
copy is unavailable. `EXCALIDRAW_CLI_DIR` and `EXCALIDRAW_BROWSER_PATH` can also
override the discovered tool paths. The helper checks native SVGs are vector,
validates every Mermaid diagram and the combined source, renders the tree, and
checks the topology node/edge counts against the current native scene.

Camera address verified from the configured Frigate camera endpoint; native
Docker published ports and Kubernetes service addresses were checked live.
Internal-only containers use Docker DNS labels, not invented stable IPs.
ClusterIP values are snapshots, not externally routable LAN endpoints.
The tree shows ownership/network attachment, while the separate frames show
data/request paths. This avoids pretending, for example, that a camera video
stream flows through MQTT or Grafana sits between Home Assistant and metrics.

## Previous presentation sheets

These remain in Git history/current files for reference, but are **not the
owner-approved primary layout**. Their earlier review did not establish that
they met the owner's needs. Prefer the current Excalidraw tree above.

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
| px10 | Dell OptiPlex 5060, i5-8400T, 6 cores, 32 GB RAM | dev VM100; dns LXC102; auth LXC103; observability LXC104; s3 LXC105; haos VM107; store LXC109; Talos VM201 |
| px20 | Dell OptiPlex 5060, i5-8400T, 6 cores, 32 GB RAM | proxy LXC101; orva VM106; ctr VM204; Talos VM202 |
| px30 | Dell OptiPlex 5060, i5-9400T, 6 cores, 32 GiB RAM | None; Talos VM203 remains stopped during swap preparation |

All three physical NICs reported 1000 Mb/s, full duplex, link detected. Each host
has separate rpool and data ZFS pools. The Netgear GS110TPv3 and partial port map
are verified in the switch runbook; router/AP model, upstream bandwidth, VLAN
topology and UPS inventory remain unverified. The LAN line does not claim every
cable is plugged directly into the router. Guest placement can change
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

## CI validation repair — 31 October 2026

The Architecture diagrams workflow failed because check-topology.mjs required
the obsolete text “LAN switching” after the verified Netgear node was renamed.
The validator now checks the stable lan node, its verified switch label and
native arrow bindings to all three hosts. Required scene coverage, privacy,
source hashes and generated-SVG freshness checks remain enforced. Public and
internal local checks passed; [GitHub Actions run41172121640](https://github.com/Harsh-2002/Homelab/actions/runs/41172121640) passed on commit991459c.
