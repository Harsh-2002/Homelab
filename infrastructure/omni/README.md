# Omni

Omni runs outside its managed Kubernetes cluster on `ctr` (10.1.1.4), through
Portainer stack `omni` (ID 158, endpoint 2). This avoids a dependency on Kubernetes
or Longhorn for the management UI during cluster recovery. It is a single-instance
management service, not an HA deployment. An Omni outage does not stop existing
Kubernetes workloads, but blocks Omni management until restored.

## Endpoints and security

- UI/API: https://omni.l3b.cc.cd
- Machine API: https://omni-api.l3b.cc.cd
- Kubernetes proxy: https://omni-kube.l3b.cc.cd
- WireGuard: 10.1.1.4:50180/UDP (LAN only; no internet forwarding needed).
- Metrics: CTR loopback 127.0.0.1:9095, not publicly exposed.

Existing Caddy terminates HTTPS, forwards the UI and machine API over h2c, and
restricts all three HTTPS endpoints to LAN/Tailscale clients. Explicit unproxied
Cloudflare A records point to 10.1.1.3, matching private DNS. These are private
management endpoints, not internet-published services.

Pocket ID native OIDC client `omni` is restricted to `infrastructure-admins`.
Callback: `https://omni.l3b.cc.cd/oidc/consume`. Verified email is required. The
initial administrator uses the existing Pocket ID administrator email, not a new
SMTP identity. No Dex or additional proxy is deployed.

## Persistent state and reproduction

`/data/apps/omni` on CTR contains root-only configuration and recovery material:

- `docker-compose.yaml`: readable source tracked here; deployed through Portainer.
- `config.yaml`: generated configuration including OIDC secret and stable account UUID.
- `omni.asc`: GPG private key used to encrypt Omni etcd state.
- `state/etcd`: embedded etcd data.
- `state/sqlite`: SQLite database including audit, discovery and machine logs.

HomeLab vault item `Omni`, concealed `deployment-secrets`, preserves the account
UUID, administrator email, OIDC secret and GPG encryption key. Never regenerate
the UUID/key on an existing datastore. The vault item is recovery material, not a
backup of the actual datastore. Do not copy credentials into Git or memory.

Reconcile using `python3 infrastructure/omni/deploy.py`. It creates/updates only
the Omni Portainer stack, retains the stable vault material, and does **not**
accept legal terms or import/unlock/reboot Talos nodes.

Stable image: `ghcr.io/siderolabs/omni:v1.12.4`, reviewed 2026-10-18. Watchtower is
disabled for this management service. Review migrations and preserve consistent
state plus its encryption key before a deliberate upgrade. Limits: 2 CPUs, 3 GiB
memory. Initial idle sample was approximately 66 MiB; this is not a loaded sizing
guarantee. The embedded etcd is independent of the managed cluster's etcd.

## Acceptance and import gate

**Pending:** owner must open the UI and review/accept Sidero's EULA. The agent
must not accept it on the owner's behalf. No acceptance flags are configured.
The service is installed, but the three Talos nodes are **not yet imported**.

Use the matching `omnictl` v1.12.4 (GitHub SHA-256 verified) on dev. After owner
acceptance and CLI authentication, first preview:

```bash
omnictl --omniconfig ~/.talos/omni/config cluster import \
  --talosconfig talos-k8s/talosconfig \
  --nodes 10.1.1.201,10.1.1.202,10.1.1.203 \
  --dry-run
```

Confirm syntax with the installed CLI's `--help`. Inspect the preview, original
Talos/Kubernetes versions, generated patches and image schematics. Preserve the
existing Cilium configuration, VIP 10.1.1.200, DNS, node addresses, Longhorn user
volume and iscsi-tools extensions. Never add `--force` to bypass validation.
Protect the automatically exported machine-config ZIP as a secret. It is needed
for rollback and contains cluster credentials.

After a clean preview, run the supported import without `--dry-run`. It connects
the machines without resetting the cluster, captures existing configuration as
patches, and leaves the imported cluster **locked**. Verify all nodes, workloads,
networking and volumes before considering unlock. Do not trigger upgrades or
reboots as part of enrollment. Do not continue applying independent machine
configuration changes outside Omni once management is handed over.

## Sources

- https://docs.siderolabs.com/omni/self-hosted/run-omni-on-prem
- https://docs.siderolabs.com/omni/self-hosted/expose-omni-with-nginx-https
- https://docs.siderolabs.com/omni/cluster-management/importing-talos-clusters
- https://github.com/siderolabs/omni/releases/tag/v1.12.4

The v1.12.4 binary uses `--machine-api-*` flags. Some documentation examples still
use `--siderolink-api-*`; the deployed image's help/schema take precedence.
Self-hosted personal homelab use is permitted under BUSL; production use requires
a commercial agreement. The owner must review terms for their actual use.
