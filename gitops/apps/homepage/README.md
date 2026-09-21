# Homepage

Homepage is the stateless, Git-managed portal served at `https://l3b.cc.cd`.

- Argo CD deploys this Helm chart into the `homepage` namespace.
- `homepage-config` is the source of truth for the visible page: `services.yaml`, `settings.yaml`, `widgets.yaml`, and `kubernetes.yaml` are ConfigMap entries rendered from Git.
- It uses a read-only Kubernetes service account solely for cluster and resource widgets.
- Cilium advertises `10.1.1.174:80`; Caddy terminates TLS, applies private LAN/Tailscale access control, and uses Tinyauth/Pocket ID for authentication.
- Widget credentials are held only in the live `homepage-widgets` Kubernetes Secret, sourced from the authoritative 1Password items. The chart contains `HOMEPAGE_VAR_*` placeholders only; never commit a secret value.

## Live metrics

The header identifies its source explicitly: **Kubernetes Cluster** is aggregate Kubernetes CPU and memory, followed by individually labelled `k8s-201`, `k8s-202`, and `k8s-203` cards. The timestamp is a local browser utility widget.

Native service widgets provide live DNS statistics from AdGuard Home, Beszel system counts, Komodo server/stack/container counts, Argo CD application state, and Proxmox cluster and node CPU/memory state. Longhorn contributes one labelled aggregate storage-capacity widget in the header; its full per-node detail remains one click away in Longhorn.

`Headlamp` is deliberately a Kubernetes management link rather than a duplicate metric source: its authoritative data is the Kubernetes API already represented by the labelled cluster and node cards. `Pocket ID` remains an identity health/access link; no sensitive authentication internals are displayed.

Each non-human metric integration has its own least-privilege identity:

- Proxmox `homepage@pve!homepage` has only the `PVEAuditor` token ACL.
- Argo CD local `homepage` is API-key-only with `role:readonly`.
- Komodo service user `homepage` has read access only to Servers and Stacks; it has no execute, inspect, terminal, or configuration permission.

Beszel's own API requires a PocketBase superuser for this widget. Homepage therefore uses the pre-existing `Beszel PocketBase Superuser` credential from 1Password for that widget only; it is never stored in Git.

The internal Proxmox API uses the tracked cluster root CA at `files/pve-root-ca.crt`, mounted with `NODE_EXTRA_CA_CERTS`. This keeps TLS verification enabled for all three direct `:8006` widget requests. Replace that file only if the Proxmox cluster CA is intentionally rotated.

Validate after an Argo sync:

```bash
kubectl --context k8s -n homepage get deploy,pods,svc
curl -I https://l3b.cc.cd
```
