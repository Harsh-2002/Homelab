# Homelab

This repository is the reproducible configuration brain for the homelab. The Notion runbook is the operational brain: topology, decisions, access procedures, validation results, and recovery instructions.

Start a new agent or chat with [`HANDOFF.md`](HANDOFF.md). It lists the authoritative Notion pages, access conventions, deployed architecture, pending work, safety rules, and the ready-to-paste continuation prompt.

## Administrator identity

Use `iam.anuragvishwakarma@gmail.com` for personal logins when a service accepts an email address or OIDC identity. Use `iam-anuragvishwakarma` when a conventional username is required. Do not create new personal accounts with dotted or underscored username variants. Keep operating-system accounts, Kubernetes service accounts, and application service users distinct because they are machine identities.

## Repository layout

- `talos-k8s/` — safe Talos patches and Cilium networking configuration.
- `gitops/` — Argo CD bootstrap, cluster applications, and workload manifests.
- `infrastructure/` — reproducible proxy configuration and sanitized service runbooks.
  - `infrastructure/proxmox/` — Proxmox host resolver baseline.
  - `infrastructure/tailscale/` — three-node Tailscale subnet routing, Keepalived gateway VIP, and recovery runbook.
  - `infrastructure/pocket-id/` — Pocket ID systemd service, pinned upgrade helper, and runbook.
  - `infrastructure/onepassword/` — scoped 1Password service-account and secret-handling runbook.
  - `infrastructure/pulse/` — archived Pulse evaluation and rebuild guide.
  - `infrastructure/beszel/` — Beszel hub and agent services, public key, HA, and operations runbook.
  - `infrastructure/uptime-kuma/` — native Uptime Kuma service, private proxy authentication, and recovery runbook.
  - `infrastructure/immich/` — Immich Compose deployment and safe restore procedure.
  - `infrastructure/portainer/` — Portainer EE Compose deployment and safe restore procedure.
  - `infrastructure/registry/` — public Docker Registry and its RustFS-backed restore procedure.
  - `infrastructure/frigate/` — private Frigate NVR, OIDC proxy integration, and retention policy.
  - `infrastructure/minio/` — historical MinIO-to-RustFS migration record.
  - `infrastructure/rustfs/` — native RustFS S3 service, OIDC, HA, and upgrade runbook.
  - `infrastructure/cairn/` — fresh native Cairn S3 service on the `s3` LXC and its operations runbook.
  - `infrastructure/orva/` — Orva serverless VM, Proxmox firewall, HA, and replication runbook.
  - `infrastructure/restored-services/` — recovered Portainer workloads, storage paths, and validation state.
- `scripts/` — administrative helper scripts.
  - `scripts/cf` — minimal POSIX Cloudflare DNS CLI; token and zone remain in the environment or the non-Git Cloudflare environment file.

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
| Tailscale gateway VIP | `10.1.1.9` |
| Cilium LoadBalancer pool | `10.1.1.170-10.1.1.190` |
| Argo CD service | `10.1.1.171` |
| Argo CD UI | `https://argocd.l3b.cc.cd` |
| Longhorn service | `10.1.1.172` |
| Longhorn UI | `https://longhorn.l3b.cc.cd` |
| Headlamp service | `10.1.1.173` |
| Headlamp UI | `https://headlamp.l3b.cc.cd` |
| Homepage portal | `https://l3b.cc.cd` |
| Pocket ID service | `10.1.1.6:1411` |
| Pocket ID counts (private) | `10.1.1.6:1412` |
| Pocket ID UI | `https://auth.l3b.cc.cd` |
| Tinyauth service | `10.1.1.6:3000` |
| Tinyauth UI | `https://login.l3b.cc.cd` |
| Beszel service | `10.1.1.7:8090` |
| Beszel UI | `https://beszel.l3b.cc.cd` |
| Uptime Kuma UI | `https://status.l3b.cc.cd` |
| Immich UI | `https://photos.l3b.cc.cd` |
| Portainer UI | `https://portainer.l3b.cc.cd` |
| Docker Registry | `https://registry.l3b.cc.cd` |
| Frigate UI | `https://frigate.l3b.cc.cd` |
| RustFS S3 API | `https://s3.l3b.cc.cd` |
| RustFS Console | `https://rustfs.l3b.cc.cd` |
| Cairn S3 API | `https://cairn-s3.l3b.cc.cd` |
| Cairn Console | `https://cairn.l3b.cc.cd` |
| n8n UI | `https://n8n.l3b.cc.cd` |
| OpenCloud files | `https://drive.l3b.cc.cd` |
| Orva serverless | `https://orva.l3b.cc.cd` (`10.1.1.11:8443`) |
| Proxmox cluster | `https://px.l3b.cc.cd` |
| Proxmox px10 | `https://px10.l3b.cc.cd` |
| Proxmox px20 | `https://px20.l3b.cc.cd` |
| Proxmox px30 | `https://px30.l3b.cc.cd` |

## Public DNS policy

Cloudflare DNS is private by default: the apex record resolves to proxy `10.1.1.3` and the wildcard CNAME follows it. Explicit public DNS-only records are exceptions, not the default. Current public application records are `photos`, `pin`, `registry`, and `orva`; `argocd` is public solely for GitHub's signed Argo CD webhook. Caddy still limits public Argo CD access to `POST /api/webhook`.

See [`talos-k8s/README.md`](talos-k8s/README.md) and [`gitops/README.md`](gitops/README.md) for operating procedures.

The identity layer is deployed. Pocket ID provides passkey authentication with the primary passkey synchronized through 1Password. Headlamp, Argo CD, Proxmox, Portainer, and OpenCloud use native OIDC. Tinyauth provides Caddy `forward_auth` for services without native OIDC; AdGuard Home, Longhorn, Homepage, Frigate, and Uptime Kuma are protected this way. Identity endpoints and applications remain restricted to the LAN and Tailscale networks.
