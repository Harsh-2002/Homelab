# Homepage

Homepage is the stateless, Git-managed portal served at `https://l3b.cc.cd`.

- Argo CD deploys this Helm chart into the `homepage` namespace.
- `homepage-config` is the source of truth for the visible page: `services.yaml`, `settings.yaml`, `widgets.yaml`, and `kubernetes.yaml` are ConfigMap entries rendered from Git.
- It uses a read-only Kubernetes service account solely for cluster and resource widgets.
- Cilium advertises `10.1.1.174:80`; Caddy terminates TLS, applies private LAN/Tailscale access control, and uses Tinyauth/Pocket ID for authentication.
- Widget credentials are held only in the live `homepage-widgets` Kubernetes Secret, sourced from the authoritative 1Password items. The chart contains `HOMEPAGE_VAR_*` placeholders only; never commit a secret value.

## Live metrics

Anchor is an Applications card at private `https://notes.l3b.cc.cd`, with its own official served icon and `/api/health` check. It has native Pocket ID login and no invented statistics widget. See `infrastructure/anchor/README.md`.

The Control row groups Pocket ID, Portainer, and Home Assistant in three equal-height statistics cards. Hermes and Warpgate sit with the general Applications. Warpgate has no native Homepage service widget; its authenticated session-management API is not a ready-made monitoring widget. Keep its official icon, URL and availability check without adding an administrative token or custom adapter just for layout consistency. This placement was explicitly requested on 2026-10-01. Media services have their own four-column row so downloads and automation are discoverable together without crowding Applications.

Home Assistant has a native widget for people, lights and switches, authenticated by `HOMEPAGE_VAR_HOMEASSISTANT_TOKEN` in the live `homepage-widgets` Secret. The API token is held in the existing `Home Assistant` HomeLab 1Password item, never in Git. OpenViking and Hermes have health-checked cards; neither has a native Homepage statistics widget, so the portal does not invent counts from unrelated endpoints.

The header identifies its source explicitly: **K8s** is aggregate Kubernetes CPU and memory, with memory displayed in decimal GB. Per-node Kubernetes figures are intentionally omitted to keep the overview concise; use Headlamp when node-level detail is needed. The timestamp is a local browser utility widget.

Native service widgets provide live DNS statistics from AdGuard Home, Beszel system counts, Portainer Docker container counts, Argo CD application state, and Proxmox cluster and node CPU/memory state. Following the owner's 2026-10-01 card-first preference, Longhorn shows **Total, Used and Free** directly on its Platform card using Homepage's supported `prometheusmetric` service widget. It queries the existing VictoriaMetrics instance every 60 seconds. The duplicate Longhorn header widget/provider and its obsolete JavaScript transformation were removed. Full per-node detail remains one click away in Longhorn. Frigate and Docker Registry are direct cards: their private/protected API endpoints do not receive a misleading unauthenticated monitor check.

Homepage's Kubernetes header widget presents memory in binary units. The small `custom.js` adapter now only converts that K8s memory display to decimal GB; it performs no network requests. Keep this conversion when upgrading Homepage unless upstream adds equivalent display options; browser-verify the cards after every Homepage upgrade.

The header ends with a keyless Open-Meteo weather widget for Bilalpada, visually separated from the preceding date/time. It refreshes at most every 15 minutes, uses metric units and India Standard Time, and has no credential or new in-cluster dependency.

`Headlamp` remains the Kubernetes management link, with cluster status now displayed directly on its card using the existing monitoring data. `RustFS` and the native Cairn development deployment have separate Platform cards and separate S3 endpoints as documented in their infrastructure runbooks. The Cairn card uses the project's own console favicon rather than the unrelated icon-catalog entry with the same name. Orva uses its own served SVG favicon and links to the public serverless console; the Homepage card carries no Orva API credential. The Applications row contains Immich, Karakeep, OpenCloud, Paperless-ngx, n8n, and Hermes. The Media row contains Jellyfin, Seerr, Sonarr, Radarr, Prowlarr, Bazarr, qBittorrent, and Motrix. Motrix uses its own favicon and `/healthz` status check; its private route and storage paths are documented in `infrastructure/motrix/README.md`. The Arr stack is documented in `infrastructure/arr/README.md`. Live applications use status checks. `Pocket ID` shows live user and OIDC-client totals from the counts-only adapter on `auth`; no Pocket ID API key, user profile, or OIDC credential reaches Homepage.

Grafana has a Monitoring card linking to its private Pocket ID-protected UI. Homepage checks Grafana's `/api/health`; detailed Proxmox, guest, Kubernetes, and Longhorn metrics stay in Grafana rather than duplicating dashboards in the portal.

The Control row links to the three Proxmox nodes. Native backups appear in each node's Proxmox UI under the cluster-wide `PX` CIFS storage; there is no separate backup-server UI.

Headlamp's Platform card now shows **Nodes, Ready and Running Pods**, sourced from kube-state-metrics through VictoriaMetrics, not from Headlamp itself. The CPU/RAM header remains a separate compute summary. Argo CD retains its native Apps/Synced/Out of Sync/Degraded widget. Platform uses equal-height rows to keep these three primary cards consistent.

The Longhorn and Headlamp card queries reuse the existing HomeLab `VictoriaMetrics API` credential. It is injected into `homepage-widgets` as `HOMEPAGE_VAR_VICTORIA_USERNAME` and `HOMEPAGE_VAR_VICTORIA_PASSWORD`; Git contains placeholders only. The current shared VictoriaMetrics Basic-auth identity can also write metrics and is not a read-only identity. These cards perform only GET queries; no proxy, service or new backend account was added. If stronger separation is required later, use a query-only authorization gateway rather than claiming the existing credential is read-only. Longhorn uses a sum of per-node maxima to avoid duplicate scrape-series double counting. Used means physical node storage usage, including replicas, not logical document/file sizes. Missing time series must not be silently presented as healthy zero values.

The following non-human metric integrations have their own least-privilege identities:

- Proxmox `homepage@pve!homepage` has only the `PVEAuditor` token ACL.
- Argo CD local `homepage` is API-key-only with `role:readonly`.
- Portainer local service user `homepage` has Portainer's **Helpdesk User** role for the `Aether` Docker environment only. This is the least Portainer role that can read host-wide container counts; its API key cannot alter Docker resources.

Pocket ID is the exception: its API keys have full administrator access. With the owner's approval, the adapter on `auth` reads the existing `Pocket ID Automation API` key locally and returns only two integer totals. Homepage never holds that key or receives the raw Pocket ID API response. See `infrastructure/pocket-id/README.md` for the endpoint and service recovery procedure.

Beszel's own API requires a PocketBase superuser for this widget. Homepage therefore uses the pre-existing `Beszel PocketBase Superuser` credential from 1Password for that widget only; it is never stored in Git.

The internal Proxmox API uses the tracked certificate at `files/pve-root-ca.crt`, mounted as `NODE_EXTRA_CA_CERTS`. This keeps TLS verification enabled for direct widget requests. Replace it only when the cluster CA is intentionally rotated.

Validate after an Argo sync:

```bash
kubectl --context k8s -n homepage get deploy,pods,svc
curl -I https://l3b.cc.cd
```

For every visual or widget configuration change, completion additionally requires a fresh browser reload of `https://l3b.cc.cd`: confirm the intended cards render, no Homepage error panel is visible, and the browser console has no errors. A successful Helm render or a healthy Kubernetes Deployment alone is not sufficient UI verification.
