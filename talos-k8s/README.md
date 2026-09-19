# Talos Kubernetes

The cluster consists of three Talos control-plane nodes:

| Node | Address |
| --- | --- |
| `k8s-201` | `10.1.1.201` |
| `k8s-202` | `10.1.1.202` |
| `k8s-203` | `10.1.1.203` |

The Kubernetes API uses the layer-2 VIP `10.1.1.200`. Cilium provides kube-proxy replacement, Kubernetes IPAM, and L2-announced LoadBalancer addresses from `10.1.1.170-10.1.1.190`.

## Tracked configuration

- `cluster-name.patch.yaml` — cluster name.
- `vip.patch.yaml` — Kubernetes API VIP.
- `k8s-20x.patch.yaml` — hostname, static address, gateway, and resolver configuration per node.
- `cilium-talos.patch.yaml` — disables kube-proxy and Flannel for Cilium.
- `cilium-values.yaml` — currently deployed Cilium Helm values.
- `lb-pool.yaml` — Cilium LoadBalancer IP pool.
- `l2-policy.yaml` — Cilium L2 announcement policy.

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
