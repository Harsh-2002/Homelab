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

## Managed cluster status, 2026-10-22

Cluster `k8s` is imported and **unlocked** for Omni management. All three
machines are connected and Ready; the control-plane load balancer is healthy.
The owner completed CLI authorization through Pocket ID. This supersedes the
old pending-import record from 2026-10-18.

- Talos `1.14.1`, Kubernetes `1.37.0`, unchanged by enrollment.
- `k8s-201`: `716f2a61-bd9a-4352-8a14-c500139c5964`
- `k8s-202`: `bc9ba4bc-8788-448a-9c0b-9c237019189e`
- `k8s-203`: `bed2656a-4098-4783-8246-cbd99dd9f223`

Both Kubernetes access through `omni-kube.l3b.cc.cd` and Talos access through
Omni were exercised successfully. Existing VIP access remains valid. All nine
Argo applications were Synced/Healthy, all non-completed pods Ready, Cilium
healthy, and all six Longhorn volumes attached/healthy after handover.

Unlocking refreshed control-plane static pods and temporarily interrupted API
access. The load balancer initially returned proxy errors, then recovered after
the API servers and health checks settled. The cluster was briefly locked during
inspection and subsequently unlocked after successful proxy checks. No node
reboot, reset, version upgrade or certificate rotation was requested. This was
**not a zero-downtime handover**.

Before unlocking, every original configuration document was compared against
the import backup and found unchanged; only the three Omni connection/logging
documents had been added. After reconciliation, exact equality of resolver,
static links, hostname, VIP, Longhorn UserVolume, pod/service networks and
disabled kube-proxy was verified. All original extensions remain detected:
`iscsi-tools`, `kata-containers-snp`, `qemu-guest-agent`.

The cluster endpoint becomes Omni's internal SideroLink load balancer. Omni also
updates API authentication defaults and removes the unattended-install document
from the applied configuration. Keep future Talos machine changes in Omni;
do not independently reapply historical machine configuration patches.

### Local access and recovery material

On dev, `/home/dev/.talos/omni/config` (0600) uses the existing administrator
identity and HTTPS Omni URL. Its signing key is protected under `.talos/keys`;
future expiration requires normal Pocket ID reauthentication, not disabling auth.
Separate generated client configs live under `/home/dev/.local/state/omni-import`
(0700), without replacing the existing kubeconfig or Talos configuration:

- `talosconfig`: Omni-proxied access; local context renamed `default` to reuse
  the already-authorized CLI signing-key context, avoiding a second login.
- `kubeconfig-oidc`: normal user OIDC access; requires `kubectl oidc-login` and
  browser authentication when first used. Generated, not interactively tested.
- `k8s-before-import-20261022.zip` (0600): original configurations for all three
  nodes. Contains credentials; **never commit, print, or ingest into memory**.

The successful Kubernetes proxy test used an isolated service-account kubeconfig
with a 10-minute token; its local file was removed after validation. It is not a
permanent agent credential. The original
Talos/Kubernetes CAs were deliberately retained so existing integrations continue
working. Consequently, Omni's imported-cluster warning (`tainted-by-importing`)
is expected: old direct client configurations still work. CA rotation is a
separate coordinated maintenance operation, not performed during enrollment.

```bash
omnictl get clusters
omnictl get machines
omnictl get loadbalancerstatuses
omnictl cluster status k8s --wait 30s
talosctl --talosconfig /home/dev/.local/state/omni-import/talosconfig \
  --nodes 716f2a61-bd9a-4352-8a14-c500139c5964 version --short
```

### Failure handling and ownership

If a subsequent machine-config change causes trouble, pause reconciliation with
`omnictl cluster lock k8s`, inspect the affected machine's current and pending
configuration, and use the retained direct Talos access if the Omni proxy is
unavailable. Locking prevents further reconciliation; it does not undo an
already-applied configuration. Do not delete the cluster or machines to resolve
a connectivity issue: deletion can reset machines.

The original ZIP is an enrollment rollback reference, not a current cluster-state
backup or database/PersistentVolume backup. After management handover, blindly
restoring it can discard newer configuration. Use the supported locked import
abort workflow only for an explicit decision to abandon the import, then choose
the restoration method appropriate to whether the cluster was ever unlocked.
See the official import guide below. Do not run abort during ordinary recovery.

Omni manages Talos machines and control-plane lifecycle. Argo CD continues to
manage Kubernetes applications, Helm settings and manifests. Longhorn continues
to own its volumes. Keep these ownership boundaries to avoid conflicting changes.

## Import procedure, reference only

Do not re-run import against the already managed cluster. For a future new
cluster, the owner must review/accept any presented EULA themselves. The agent
must not accept legal terms on the owner's behalf; no acceptance flags are set.

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
