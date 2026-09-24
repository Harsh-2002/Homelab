# Homelab agent handoff

This is the reusable entry point for a new agent or a new chat. Clone this repository, open this file first, read the relevant service runbooks, and inspect the live systems before making changes. The repository and Notion are the Homelab's operational memory; neither should be treated as disposable notes.

## Ready-to-paste prompt

```text
Work from the cloned Homelab repository and read HANDOFF.md completely before acting. You have SSH aliases for the infrastructure, authenticated 1Password CLI access through scripts/op-sa, and authenticated Notion CLI access through `NOTION_KEYRING=0 ntn`. Read the relevant repository runbooks and both Notion runbooks, inspect live state, preserve existing configuration, and continue from the documented deployed/planned status. Do not print or commit secrets. After every material change, validate the actual endpoint or data path, update both Git and the main Notion runbook, and commit the repository changes with a clear message.

My current task is: <describe the task here>
```

## Sources of truth

Use these in order:

1. This repository for reproducible configuration, sanitized commands, manifests, service topology, and recovery procedures.
2. The main Notion runbook for chronological decisions, incidents, validation results, and operational context.
3. The BIOS/firmware Notion runbook for the px10 firmware incident and hardware-specific recovery guidance.
4. The live hosts and APIs for current truth. Documentation can become stale, so verify before mutation.

There are **three relevant Notion documents**:

| Document | Page ID | Purpose |
| --- | --- | --- |
| `Homelab — Proxmox Cluster Build & Runbook` | `3e0d3ccf-b520-81d1-83b8-cb1465f4935a` | Main Homelab topology, decisions, deployments, tests, incidents, and next actions |
| `Proxmox BIOS & Firmware Upgrade — px10 Incident, Recovery & Runbook` | `3e2d3ccf-b520-81d8-853e-ecadd7aaaaeb` | px10 BIOS/firmware incident, recovery, and future firmware procedure |
| `Proxmox — Intel I219-V NIC Stability` | `3e3d3ccf-b520-813d-91a2-d18185fb8b14` | Repeated px10/px20 e1000e transmit-hang incident, persistent mitigation, validation, and escalation path |

Other Notion search results are unrelated articles or personal notes and are not Homelab sources of truth.

Use the CLI without disturbing existing page content:

```bash
NOTION_KEYRING=0 ntn whoami
NOTION_KEYRING=0 ntn pages get 3e0d3ccf-b520-81d1-83b8-cb1465f4935a
NOTION_KEYRING=0 ntn pages get 3e2d3ccf-b520-81d8-853e-ecadd7aaaaeb
NOTION_KEYRING=0 ntn pages get 3e3d3ccf-b520-813d-91a2-d18185fb8b14
```

Prefer appending a concise dated section through the block-children API. Do not replace the entire large main page merely to add an update.

## Initial orientation checklist

Before changing anything:

```bash
git status --short
git log -5 --oneline
sed -n '1,240p' HANDOFF.md
sed -n '1,220p' README.md
NOTION_KEYRING=0 ntn whoami
scripts/op-sa whoami
```

Then read only the runbooks related to the task. Examples:

- Proxmox and guest placement: `infrastructure/proxmox/`, `infrastructure/docker/`
- DNS: `infrastructure/dns/`
- Proxy and exposure policy: `infrastructure/proxy/`
- Tailscale routing: `infrastructure/tailscale/`
- Talos/Kubernetes: `talos-k8s/`, `gitops/`
- Identity: `infrastructure/pocket-id/`
- Monitoring: `infrastructure/beszel/`, `infrastructure/uptime-kuma/`
- Applications: the matching directory under `infrastructure/`

Never assume an untracked or dirty file belongs to the agent. Preserve user changes and inspect the diff before editing.

## Access

Available SSH aliases:

```text
px10  px20  px30  dns  proxy  auth  s3  ctr  dev  orva  pc  pi
```

Important roles:

| Alias | Role |
| --- | --- |
| `px10`, `px20`, `px30` | Proxmox cluster nodes |
| `dns` | AdGuard Home and Unbound |
| `proxy` | Caddy reverse proxy |
| `auth` | Pocket ID and Tinyauth identity services |
| `s3` | Native RustFS object storage |
| `ctr` | Docker application VM managed through Portainer |
| `dev` | Administrative and build VM; this repository normally lives here |
| `orva` | Outbound-isolated serverless VM 106 at `10.1.1.11` |

`slate` is a GCP free-tier VM in the US with Tailscale IP `100.122.33.37`. It is online and offers an exit node, but there was no working regular SSH path from `dev` at the last review. Do not assume `ssh slate` works merely because MagicDNS lists the node.

## Secret handling

The existing Homelab 1Password service account is loaded only through:

```bash
scripts/op-sa <op arguments>
```

The vault is named `HomeLab`. Inspect field metadata without revealing values whenever possible. Retrieve a secret only into a short-lived shell variable or a protected file in `/run`, never echo it, never put it in a command line visible to other processes, and never commit it.

The Tailscale item is currently named `Tailscale Subnet Router Enrollment`. Its enrollment auth key was revoked and removed. It retains the admin URL, actual Google identity `av7312002@gmail.com`, and a short-lived API key. Tailscale has no independent password. The API key recorded on 2026-09-22 expires on 2026-09-23 and should be replaced with a narrowly scoped trust credential or OAuth client for long-lived automation.

Personal identity conventions:

- Prefer `iam.anuragvishwakarma@gmail.com` when a service accepts the newer email.
- Prefer `iam-anuragvishwakarma` when a conventional username is required.
- Do not change an existing external account to a false identity merely for naming consistency.
- The existing Tailscale personal tailnet is owned by `av7312002@gmail.com`. A Gmail/shared-domain tailnet cannot transfer ownership to another Gmail identity; the newer identity can be invited as Admin, but the old identity remains Owner unless the tailnet is rebuilt.
- Do not create duplicate 1Password items. Update the canonical item and use a site-specific URL.

## Current architecture snapshot

Read the main README for the full endpoint table. Key infrastructure facts:

- LAN: `10.1.1.0/24`
- Router: `10.1.1.1`
- DNS: `10.1.1.2`
- Caddy proxy: `10.1.1.3`
- Orva serverless VM: `10.1.1.11` (VM 106; outbound-isolated by Proxmox firewall)
- Kubernetes API VIP: `10.1.1.200`
- Cilium LoadBalancer pool: `10.1.1.170-10.1.1.190`
- Tailscale/Keepalived gateway VIP: `10.1.1.9`
- Primary internal domain: `l3b.cc.cd`
- DNS is private by default; internet exposure requires an explicit Cloudflare record and corresponding Caddy policy.
- Pocket ID is the OIDC provider. Tinyauth protects services without native OIDC support.
- Portainer is the current Docker management interface. Komodo and Pulse are removed from live infrastructure; their repository directories are historical/rebuild documentation only.
- RustFS replaced MinIO. Do not redeploy MinIO unless specifically requested for recovery.

## Tailscale HA gateway

The Tailscale gateway runs directly on all three Proxmox hosts. There is no gateway VM or LXC.

| Host | LAN | Tailscale | Keepalived priority |
| --- | --- | --- | ---: |
| px10 | `10.1.1.10` | `100.100.202.88` | 150 |
| px20 | `10.1.1.20` | `100.115.39.43` | 120 |
| px30 | `10.1.1.30` | `100.101.22.38` | 90 |

All three advertise and have approval for `10.1.1.0/24`, use `tag:subnet-router`, and have device-key expiry disabled. They use:

```text
accept-dns=false
accept-routes=false
snat-subnet-routes=true
netfilter-mode=on
Tailscale SSH disabled
exit-node advertisement disabled
Tailscale native auto-update enabled
```

Persistent services on every Proxmox host:

```text
tailscaled.service
tailscale-gro.service
tailscale-gateway.service
keepalived.service
```

The VIP normally belongs to px10, fails to px20 and then px30, and automatically fails back. Host reboot, Keepalived failure, and `tailscaled` failure were tested. LAN guests that need to initiate tailnet traffic use one persistent route:

```text
100.64.0.0/10 via 10.1.1.9
```

Do not add three weighted routes or guest-side polling. A scoped nftables masquerade rule on the active Proxmox host makes outbound failover independent of Tailscale's separate inbound subnet-router election.

Authoritative detail is in `infrastructure/tailscale/README.md`.

## Deployed versus planned

Do not present a documented design as an applied change.

Deployed and verified:

- Three-node Proxmox cluster and HA/replication described in the service runbooks
- AdGuard Home plus Unbound
- Caddy wildcard TLS and private/public access policy
- Talos Kubernetes, Argo CD, Cilium, Longhorn, Headlamp, Homepage, and metrics-server
- Pocket ID/Tinyauth authentication
- Beszel and internal Uptime Kuma
- Portainer-managed Docker workloads including restored applications
- Restored `n8n` workload on `ctr`; Nextcloud was retired after byte-for-byte verification of its 706 live files in OpenCloud
- The 4 TB Crucial X9 Pro was reformatted on 2026-09-23; the former whole-system tar and recovery tree were erased at the owner's request. It is now an LVM disk passed to `store` VM 107 on px10, with separate 1 TiB PBS and 1 TiB SMB volumes and about 1.64 TiB unallocated. See `infrastructure/store/README.md` before moving or resizing it.
- PBS 4.2 and Samba run in `store` (`10.1.1.12`). The PBS UI is private at `pbs.l3b.cc.cd`; direct-LAN SMB is `smb://smb.l3b.cc.cd/AV` with SMB3 encryption required, not HTTPS/TLS. VM 107 replicates its OS disk to px20 and has HA affinity only to px10/px20. The USB data does not replicate, so physical disk movement is required after host failure.
- VM 204 `ctr` mounts the encrypted SMB3 share persistently at `/mnt/AV` using a systemd automount; Motrix defaults to `/mnt/AV/downloads` and can also save under `/mnt/AV/media`, while Jellyfin indexes `/mnt/AV/media/movies` and `/mnt/AV/media/shows`. The root-only CIFS credential comes from the existing `Store SMB` vault item. Application databases/config stay on local `/data/apps`. Motrix is private at `https://downloads.l3b.cc.cd`; see `infrastructure/ctr/README.md` and `infrastructure/motrix/README.md`.
- PVE storage `external` is connected to PBS. Job `critical-to-pbs` backs up VM 100, CT 101–105, and VM 204 hourly, retaining only the latest snapshot per guest. The `pve@pbs!cluster` token and backing user have `DatastorePowerUser` only on this datastore to permit immediate pruning of owned snapshots; PBS has a matching daily fallback prune job. K8s/Longhorn, orva, and PBS itself are excluded. On 2026-09-24, a manual incremental CT 102 backup and prune completed `TASK OK` and verified; confirm the next full scheduled cycle. See `infrastructure/store/README.md`.
- PBS has native Pocket ID OIDC with an explicitly authorized email-named administrator; owner browser passkey verification is pending. PVE and PBS use separate RBAC, while PVE storage `external` exposes backup browsing/restores in the PVE UI. Samba is SMB3-only, signing-required, and bound to `10.1.1.12`; log in as `iam.anuragvishwakarma@gmail.com` using the separate `Store SMB` vault credential (mapped to local `iam.anuragvishwakarma`, not PAM/OIDC).
- n8n's existing owner email was updated to `iam.anuragvishwakarma@gmail.com`, and native password + existing MFA login was verified.
- Fresh native Cairn service on the `s3` LXC beside RustFS, using separate ports and `/data/cairn`
- Native RustFS and migrated S3 workloads
- Three-node Tailscale subnet routing and Keepalived gateway VIP
- Persistent Intel I219 conservative NIC settings on px10, px20, and px30: TSO/GSO/GRO/EEE disabled by `e1000e-stability.service`; px10/px20 had transmit hangs, while px30's I219-LM has no recorded hangs and was aligned for consistency. An 8 GiB cross-node test sustained about 115 MB/s with zero NIC errors
- Paperless-ngx `3.2.1` runs as Portainer-owned Stack ID 149 on `ctr`, with SQLite/media under `/data/apps/paperless` and Valkey as broker. `https://docs.l3b.cc.cd` is private through Caddy with native Pocket ID OIDC; local login was tested as break-glass, while the passkey-protected OIDC return still needs owner verification. Homepage has a GitOps card. Secrets live in the two distinct `HomeLab` vault items `Paperless-ngx` and `Pocket ID OIDC - paperless` plus Portainer Stack Env; temporary plaintext files were removed. Use `scripts/op-sa` on `dev`: plain `op` does not load the existing service-account token file automatically. See `infrastructure/paperless/README.md`.

Planned but **not yet applied** at the time of this handoff:

- Verify a full restore and extend independent backup coverage for application data, especially both OpenCloud metadata and its RustFS bucket. The initial PBS job is not a complete backup strategy; the former whole-system recovery tar no longer exists.
- Change tailnet DNS from global `10.1.1.2` to split DNS: `l3b.cc.cd` only through `10.1.1.2`, while public DNS remains local to each client.
- Keep MagicDNS enabled and keep `accept-dns=true` on `slate`; do not override its GCP resolver for ordinary public names.
- Deploy a second Uptime Kuma on `slate` for the external viewpoint and use ntfy there. It should monitor home internet, Tailscale/subnet routing, AdGuard, public services, and selected private services without duplicating every internal alert.
- Optionally invite `iam.anuragvishwakarma@gmail.com` to Tailscale as Admin. The current Gmail owner cannot be replaced through the API.

## Working rules

- Inspect first; mutate second.
- Use official documentation for software behavior that can change.
- Use the simplest established component that satisfies the requirement.
- Keep configuration readable and minimally split. The owner strongly prefers concise files and dislikes comment or backup-file clutter.
- Do not create repeated timestamped backups. If a risky edit genuinely requires one rollback copy, create one clearly named copy and remove it after verification.
- Do not expose a service publicly merely to make testing easier.
- Preserve private-by-default DNS and Caddy access controls.
- Verify actual UI/API/data-path behavior after every material change; a healthy process alone is insufficient.
- For HA, test both failover and recovery. For storage, verify the data, permissions, health, and application-level visibility before deleting old data.
- Keep credentials out of Git, output, logs, and chat.
- Do not silently broaden the task into account migration, destructive cleanup, public exposure, or cluster-wide changes.

## Documentation and completion workflow

After a material change:

1. Update the relevant repository runbook and tracked configuration.
2. Update the main README if endpoints, topology, or repository layout changed.
3. Append a concise dated section to the main Notion runbook. Update the BIOS runbook only for firmware/hardware work.
4. State clearly what was deployed, what was tested, and what remains planned.
5. Run appropriate validation and `git diff --check`.
6. Scan the changed files for tokens, passwords, private keys, and environment files.
7. Commit with a clear imperative message.
8. Push the completed commit to `origin/main`; do not leave finished Homelab work only in the local repository.
9. Verify that local `main` and `origin/main` point to the same commit.
10. End with a clean working tree unless pre-existing user changes prevent it.

Useful checks:

```bash
git status --short
git diff --check
git log -5 --oneline
git status -sb
rg -n 'tskey-|BEGIN .*PRIVATE KEY|password\s*=' --glob '!**/.git/**'
```

Never claim that Notion or GitHub is current unless Notion was updated, the commit was pushed, and the remote branch was verified.
