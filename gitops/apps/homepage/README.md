# Homepage

Homepage is the stateless, Git-managed portal served at `https://l3b.cc.cd`.

- Argo CD deploys this Helm chart into the `homepage` namespace.
- `homepage-config` is the source of truth for the visible page: `services.yaml`, `settings.yaml`, `widgets.yaml`, and `kubernetes.yaml` are ConfigMap entries rendered from Git.
- It uses a read-only Kubernetes service account solely for cluster and resource widgets.
- Cilium advertises `10.1.1.174:80`; Caddy terminates TLS, applies private LAN/Tailscale access control, and uses Tinyauth/Pocket ID for authentication.
- Widget credentials are held only in the live `homepage-widgets` Kubernetes Secret, sourced from the authoritative 1Password items. The chart contains `HOMEPAGE_VAR_*` placeholders only; never commit a secret value.

## Live metrics

The header identifies its source explicitly: **K8s** is aggregate Kubernetes CPU and memory, with memory displayed in decimal GB. Per-node Kubernetes figures are intentionally omitted to keep the overview concise; use Headlamp when node-level detail is needed. The timestamp is a local browser utility widget.

Native service widgets provide live DNS statistics from AdGuard Home, Beszel system counts, Portainer Docker container counts, Argo CD application state, and Proxmox cluster and node CPU/memory state. Longhorn contributes one labelled aggregate storage-capacity widget in the header, expressed as **Total** first and **Used** beneath it; its full per-node detail remains one click away in Longhorn. Frigate and Docker Registry are direct cards: their private/protected API endpoints do not receive a misleading unauthenticated monitor check.

Homepage's native Longhorn widget presents Free before Total, and its Kubernetes widget presents memory in binary units. The small `custom.js` adapter changes only the aggregate Longhorn card into the clearer Total/Used order and converts the K8s memory display to decimal GB; it performs no network requests. Keep this adapter when upgrading Homepage unless upstream adds equivalent display options; browser-verify the cards after every Homepage upgrade.

The header ends with a keyless Open-Meteo weather widget for Bilalpada, visually separated from the preceding date/time. It refreshes at most every 15 minutes, uses metric units and India Standard Time, and has no credential or new in-cluster dependency.

`Headlamp` is deliberately a Kubernetes management link rather than a duplicate metric source: its authoritative data is the Kubernetes API already represented by the labelled cluster and node cards. `RustFS` and the native Cairn development deployment have separate Platform cards and separate S3 endpoints as documented in their infrastructure runbooks. The Cairn card uses the project's own console favicon rather than the unrelated icon-catalog entry with the same name. The Applications row contains Jellyfin, Motrix, Immich, Karakeep, OpenCloud, Paperless-ngx, and n8n. Motrix uses its own favicon and `/healthz` status check; its private route and storage paths are documented in `infrastructure/motrix/README.md`. Live applications use status checks. `Pocket ID` shows live user and OIDC-client totals from the counts-only adapter on `auth`; no Pocket ID API key, user profile, or OIDC credential reaches Homepage.

Grafana has a Monitoring card linking to its private Pocket ID-protected UI. Homepage checks Grafana's `/api/health`; detailed Proxmox, guest, Kubernetes, and Longhorn metrics stay in Grafana rather than duplicating dashboards in the portal.

The Control row links to the three Proxmox nodes. Native backups appear in each node's Proxmox UI under the cluster-wide `PX` CIFS storage; there is no separate backup-server UI.

Each non-human metric integration has its own least-privilege identity:

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
