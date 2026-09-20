# Talos Kubernetes

The cluster consists of three Talos control-plane nodes:

| Node | Address |
| --- | --- |
| `k8s-201` | `10.1.1.201` |
| `k8s-202` | `10.1.1.202` |
| `k8s-203` | `10.1.1.203` |

The Kubernetes API uses the layer-2 VIP `10.1.1.200`. Cilium provides kube-proxy replacement, Kubernetes IPAM, and L2-announced LoadBalancer addresses from `10.1.1.170-10.1.1.190`.

Talos nodes use AdGuard Home `10.1.1.2` as their primary resolver and Cloudflare `1.1.1.1` as the availability fallback. Kubernetes Service discovery remains on CoreDNS; CoreDNS forwards external lookups through the node resolver configuration.

## Tracked configuration

- `cluster-name.patch.yaml` — cluster name.
- `vip.patch.yaml` — Kubernetes API VIP.
- `k8s-20x.patch.yaml` — hostname, static address, gateway, and resolver configuration per node.
- `cilium-talos.patch.yaml` — disables kube-proxy and Flannel for Cilium.
- `cilium-values.yaml` — currently deployed Cilium Helm values.
- `lb-pool.yaml` — Cilium LoadBalancer IP pool.
- `l2-policy.yaml` — Cilium L2 announcement policy.
- `longhorn-volume.patch.yaml` — provisions the dedicated non-system disk as XFS at `/var/mnt/longhorn`.

Generated Talos machine configurations, `talosconfig`, kubeconfigs, and backups are local secrets and are intentionally ignored by Git.

## Validation

```bash
talosctl --talosconfig talos-k8s/talosconfig health
kubectl --context k8s get nodes -o wide
cilium status --context k8s --wait
kubectl --context k8s get ciliumloadbalancerippools,ciliuml2announcementpolicies
```

## Cilium upgrade pattern

Review the release notes and render the change before applying it. Reuse the pinned values file:

```bash
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --version 1.20.2 \
  --values talos-k8s/cilium-values.yaml
```

## Longhorn node storage

Each Talos VM has a dedicated 500 GiB VirtIO SCSI disk backed by its Proxmox host's node-local `data` ZFS pool. Talos owns the partition and XFS filesystem through `UserVolumeConfig`; do not format or mount these disks manually.

```bash
for node in 10.1.1.201 10.1.1.202 10.1.1.203; do
  talosctl --talosconfig talos-k8s/talosconfig \
    --nodes "$node" --endpoints "$node" \
    get volumestatus u-longhorn
  talosctl --talosconfig talos-k8s/talosconfig \
    --nodes "$node" --endpoints "$node" \
    get mountstatus u-longhorn
done
```

The required `iscsi-tools` extension and `ext-iscsid` service must remain present for the Longhorn V1 data engine.

## Kubernetes VM resources

Each Kubernetes VM is configured in Proxmox with:

- 4 vCPUs;
- 16 GiB maximum RAM and an 8 GiB balloon minimum;
- a 200 GiB system disk on `local-zfs`;
- a separate 500 GiB Longhorn disk on the node-local `data` pool.

Talos automatically grows the `EPHEMERAL` partition after the system disk is enlarged. The Longhorn disk must remain separate and unchanged during system-disk maintenance.
