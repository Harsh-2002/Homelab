# Homelab

This repository is the reproducible configuration brain for the homelab. The Notion runbook is the operational brain: topology, decisions, access procedures, validation results, and recovery instructions.

## Repository layout

- `talos-k8s/` — safe Talos patches and Cilium networking configuration.
- `gitops/` — Argo CD bootstrap, cluster applications, and workload manifests.
- `infrastructure/` — reproducible proxy configuration and sanitized service runbooks.
  - `infrastructure/proxmox/` — Proxmox host resolver baseline.
- `scripts/` — administrative helper scripts.

## Safety rules

- Never commit kubeconfigs, Talos machine configurations, Talos secrets, private keys, tokens, or environment files.
- Put declarative, non-secret cluster state in Git before applying it.
- Encrypt future Kubernetes secrets with SOPS and age before committing them.
- Pin Helm chart versions and review upgrades through Git.
- Validate recovery instructions in the Notion runbook after material infrastructure changes.

## Cluster endpoints

| Component | Address |
| --- | --- |
| Kubernetes API VIP | `10.1.1.200` |
| Cilium LoadBalancer pool | `10.1.1.170-10.1.1.190` |
| Argo CD service | `10.1.1.171` |
| Argo CD UI | `https://argocd.l3b.cc.cd` |
| Longhorn service | `10.1.1.172` |
| Longhorn UI | `https://longhorn.l3b.cc.cd` |
| Komodo UI | `https://komodo.l3b.cc.cd` |
| Proxmox cluster | `https://px.l3b.cc.cd` |
| Proxmox px10 | `https://px10.l3b.cc.cd` |
| Proxmox px20 | `https://px20.l3b.cc.cd` |
| Proxmox px30 | `https://px30.l3b.cc.cd` |

See [`talos-k8s/README.md`](talos-k8s/README.md) and [`gitops/README.md`](gitops/README.md) for operating procedures.
