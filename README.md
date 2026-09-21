# Homelab

This repository is the reproducible configuration brain for the homelab. The Notion runbook is the operational brain: topology, decisions, access procedures, validation results, and recovery instructions.

## Administrator identity

Use `iam.anuragvishwakarma@gmail.com` for personal logins when a service accepts an email address or OIDC identity. Use `iam-anuragvishwakarma` when a conventional username is required. Do not create new personal accounts with dotted or underscored username variants. Keep operating-system accounts, Kubernetes service accounts, and application service users distinct because they are machine identities.

## Repository layout

- `talos-k8s/` — safe Talos patches and Cilium networking configuration.
- `gitops/` — Argo CD bootstrap, cluster applications, and workload manifests.
- `infrastructure/` — reproducible proxy configuration and sanitized service runbooks.
  - `infrastructure/proxmox/` — Proxmox host resolver baseline.
  - `infrastructure/pocket-id/` — Pocket ID systemd service, pinned upgrade helper, and runbook.
  - `infrastructure/onepassword/` — scoped 1Password service-account and secret-handling runbook.
  - `infrastructure/pulse/` — archived Pulse evaluation and rebuild guide.
  - `infrastructure/beszel/` — Beszel hub and agent services, public key, HA, and operations runbook.
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
| Headlamp service | `10.1.1.173` |
| Headlamp UI | `https://headlamp.l3b.cc.cd` |
| Homepage portal | `https://l3b.cc.cd` |
| Pocket ID service | `10.1.1.6:1411` |
| Pocket ID UI | `https://auth.l3b.cc.cd` |
| Tinyauth service | `10.1.1.6:3000` |
| Tinyauth UI | `https://login.l3b.cc.cd` |
| Beszel service | `10.1.1.7:8090` |
| Beszel UI | `https://beszel.l3b.cc.cd` |
| Komodo UI | `https://komodo.l3b.cc.cd` |
| Proxmox cluster | `https://px.l3b.cc.cd` |
| Proxmox px10 | `https://px10.l3b.cc.cd` |
| Proxmox px20 | `https://px20.l3b.cc.cd` |
| Proxmox px30 | `https://px30.l3b.cc.cd` |

See [`talos-k8s/README.md`](talos-k8s/README.md) and [`gitops/README.md`](gitops/README.md) for operating procedures.

The identity layer is deployed. Pocket ID provides passkey authentication with the primary passkey synchronized through 1Password. Headlamp, Argo CD, and Proxmox use native OIDC; Komodo's native OIDC configuration is staged for its post-recovery startup. Tinyauth provides Caddy `forward_auth` for services without native OIDC; AdGuard Home and Longhorn are protected this way. Identity endpoints and applications remain restricted to the LAN and Tailscale networks.
