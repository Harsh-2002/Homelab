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
| `AdGuard Home + Unbound: my DNS setup` | `3e5d3ccf-b520-818b-8546-c4dbca0ecdce` | Sanitized, shareable DNS architecture guide; mirrors `infrastructure/dns/SHAREABLE-SETUP.md` |

Other Notion search results are unrelated articles or personal notes and are not Homelab sources of truth.

Use the CLI without disturbing existing page content:

```bash
NOTION_KEYRING=0 ntn whoami
NOTION_KEYRING=0 ntn pages get 3e0d3ccf-b520-81d1-83b8-cb1465f4935a
NOTION_KEYRING=0 ntn pages get 3e2d3ccf-b520-81d8-853e-ecadd7aaaaeb
NOTION_KEYRING=0 ntn pages get 3e3d3ccf-b520-813d-91a2-d18185fb8b14
NOTION_KEYRING=0 ntn pages get 3e5d3ccf-b520-818b-8546-c4dbca0ecdce
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
- Monitoring: `infrastructure/beszel/`, `infrastructure/uptime-kuma/`, `infrastructure/metrics/`
- Applications: the matching directory under `infrastructure/`, including `infrastructure/n8n/` for the unified n8n application group

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
- Cairn S3/API is deliberately public at `cairn-s3.l3b.cc.cd` with native S3 authentication/policies; its console `cairn.l3b.cc.cd` remains private. The temporary `share` hostname and RustFS public bucket were removed. The sanitized DNS guide is a separate [Notion page](https://app.notion.com/p/AdGuard-Home-Unbound-my-DNS-setup-3e5d3ccfb520818b8546c4dbca0ecdce) and `infrastructure/dns/SHAREABLE-SETUP.md`, not an S3 object. Current Unbound files have listener/cache configuration drift (running 5335, on-disk default 53/4 MiB); reconcile before relying on restart.
- Public `store.l3b.cc.cd` is a static Astro storefront from `git@github.com:Harsh-2002/store.git`, built with `npm ci && npm run build` and served by Caddy from `/srv/store` on `proxy`. Cloudflare's explicit DNS-only A record targets `150.129.31.154`; internal Unbound resolves the name to `10.1.1.3`. This web name is distinct from the `store` SSH alias and SMB CT at `10.1.1.12`. See `infrastructure/proxy/README.md`.
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
- Private Grafana and VictoriaMetrics in Beszel CT 104, with Pocket ID OIDC, 30-day metrics retention, Proxmox and Kubernetes exporters, and three linked provisioned dashboards: Infrastructure Overview (home), Compute & Guests, and Storage & Backups. A 15-minute textfile timer on store CT 109 exports PX backup freshness; PBS metrics are retired. See `infrastructure/metrics/README.md`. Kubernetes vmagent is GitOps-managed, but its remote-write Secret is created separately from the HomeLab 1Password vault.
- Portainer-managed Docker workloads including restored applications
- Portainer Stack 85 `n8n` on `ctr` now owns n8n 2.40.7, PostgreSQL, SearXNG, and Sandbox Service 1.4.0. SearXNG is internal at `http://searxng:8080`, with JSON search enabled; the sandbox API is internal at `http://sandbox-api:8080`. The privileged mTLS runner stays on a private control bridge and neither backend publishes a host port. JSON search and authenticated sandbox create/execute/delete were verified. Former separate Stack 150 was deleted after consolidation without deleting its persistent API state or TLS volume. Secrets remain in the existing `N8N` and `n8n Sandbox` HomeLab vault items; see `infrastructure/n8n/README.md`.
- The 4 TB Crucial X9 Pro was reformatted on 2026-09-23; the former whole-system tar and recovery tree were erased at the owner's request. Its two existing ext4 LVs are mounted on px10 and bound into unprivileged Debian CT 109 `store` (`10.1.1.12`): ~1.64 TiB `AV` and 2 TiB `PX`. A separate 256 GB USB SSD on px10 (serial ending `1716`) is mounted/bound as `ISO`; do not confuse it with px20's spare 256 GB SSD (serial ending `1741`). CT 109 has 1 vCPU, 1 GiB RAM, and an 8 GiB local-zfs OS disk; that OS disk replicates to px20 every five minutes, with HA restricted to px10/px20. The external USB data does **not** replicate: move **both SSDs** physically to px20 and mount all three filesystems there before relying on the shares after px10 failure. See `infrastructure/store/README.md`.
- Samba 4.22.11 exposes three separate SMB3-encrypted shares with the same `Store SMB` vault credential: `smb://smb.l3b.cc.cd/AV` for general files, `smb://smb.l3b.cc.cd/PX` for native Proxmox backups, and `smb://smb.l3b.cc.cd/ISO` for shared installers/templates. They are direct LAN SMB, not HTTPS/Caddy. Disk-marker checks prevent serving empty mount directories. Beszel agent and Node Exporter run in CT 109.
- VM 204 `ctr` mounts the encrypted SMB3 share persistently at `/mnt/AV` using a systemd automount; Motrix defaults to `/mnt/AV/downloads` and can also save under `/mnt/AV/media`, while Jellyfin indexes `/mnt/AV/media/movies` and `/mnt/AV/media/shows`. The root-only CIFS credential comes from the existing `Store SMB` vault item. Application databases/config stay on local `/data/apps`. Motrix is private at `https://downloads.l3b.cc.cd`; see `infrastructure/ctr/README.md` and `infrastructure/motrix/README.md`.
- Cluster-wide PVE storage `PX` is CIFS/SMB on CT 109 and shows backups directly in each Proxmox UI. Job `critical-to-px` backs up VM 100, CT 101–105, and VM 204 daily at 02:00 Asia/Kolkata with snapshot mode, zstd, and `keep-last=1`. These are **full file archives**, not PBS incremental backups. K8s/Longhorn, orva, and store itself are excluded. The initial 2026-09-26 backup succeeded for all seven guests, and CT 102 was test-restored to temporary CT 110 and then purged. The old PBS VM 107, its datastore, storage/job objects, OIDC client, Homepage card, Caddy route, and three PBS-only vault items were removed.
- Cluster-wide PVE storage `ISO` is CIFS/SMB on CT 109 with `iso,vztmpl` content. The former px10-only `iso-store` was removed after verifying no guest configuration referenced it. The existing Omarchy ISO and Debian 13 LXC template remain on the same ext4 SSD; the obsolete PBS installer ISO was removed. All three nodes list and can write to `ISO`. Existing installed guests do not depend on source install media unless an ISO remains attached as a configured CD-ROM.
- px20's separate 256 GB USB SSD is an unmounted, unregistered spare: the empty `backup-store` storage entry and its `/etc/fstab` mount were removed without formatting or wiping the disk. See `infrastructure/proxmox/README.md`.
- Samba is SMB3-only, signing-required, and bound to `10.1.1.12`; log in to either share as `iam.anuragvishwakarma@gmail.com` using the `Store SMB` vault credential (mapped to local `iam.anuragvishwakarma`, not PAM/OIDC). The `PX` Proxmox storage uses a cluster-private copy of the same password at `/etc/pve/priv/storage/PX.pw`.
- n8n's existing owner email was updated to `iam.anuragvishwakarma@gmail.com`, and native password + existing MFA login was verified.
- Fresh native Cairn service on the `s3` LXC beside RustFS, using separate ports and `/data/cairn`
- Native RustFS and migrated S3 workloads
- Three-node Tailscale subnet routing and Keepalived gateway VIP
- Persistent Intel I219 conservative NIC settings on px10, px20, and px30: TSO/GSO/GRO/EEE disabled by `e1000e-stability.service`; px10/px20 had transmit hangs, while px30's I219-LM has no recorded hangs and was aligned for consistency. An 8 GiB cross-node test sustained about 115 MB/s with zero NIC errors
- Paperless-ngx `3.2.1` runs as Portainer-owned Stack ID 149 on `ctr`, with SQLite/media under `/data/apps/paperless` and Valkey as broker. `https://docs.l3b.cc.cd` is private through Caddy with native Pocket ID OIDC; local login was tested as break-glass, while the passkey-protected OIDC return still needs owner verification. Homepage has a GitOps card. Secrets live in the two distinct `HomeLab` vault items `Paperless-ngx` and `Pocket ID OIDC - paperless` plus Portainer Stack Env; temporary plaintext files were removed. Use `scripts/op-sa` on `dev`: plain `op` does not load the existing service-account token file automatically. See `infrastructure/paperless/README.md`.

Planned but **not yet applied** at the time of this handoff:

- Extend independent backup coverage for application data, especially both OpenCloud metadata and its RustFS bucket. The current `PX` backups and `AV` files share one physical SSD and are not an off-site backup; the former whole-system recovery tar no longer exists.
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
