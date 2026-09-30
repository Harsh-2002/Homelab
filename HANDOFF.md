# Homelab agent handoff

This is the reusable entry point for a new agent or a new chat. Clone this repository, open this file first, read the relevant service runbooks, and inspect the live systems before making changes. The repository and Notion are the Homelab's operational memory; neither should be treated as disposable notes.

## Ready-to-paste prompt

```text
Work from the cloned Homelab repository and read HANDOFF.md completely before acting. You have SSH aliases for the infrastructure, authenticated 1Password CLI access through scripts/op-sa, and authenticated Notion CLI access through `NOTION_KEYRING=0 ntn`. Read the relevant repository runbooks and all four relevant Notion pages, inspect live state, preserve existing configuration, and continue from the documented deployed/planned status. Do not print or commit secrets. After every material change, validate the actual endpoint or data path, update both Git and the main Notion runbook, and commit and push the repository changes with a clear message.

My current task is: <describe the task here>
```

## Sources of truth

Use these in order:

1. This repository for reproducible configuration, sanitized commands, manifests, service topology, and recovery procedures.
2. The main Notion runbook for chronological decisions, incidents, validation results, and operational context.
3. The BIOS/firmware Notion runbook for the px10 firmware incident and hardware-specific recovery guidance.
4. The live hosts and APIs for current truth. Documentation can become stale, so verify before mutation.

There are **four relevant Notion documents**:

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
- Media automation: `infrastructure/arr/` for the Portainer stack, SMB paths, application links, and the fixed-memory/no-swap decision on `ctr`

Never assume an untracked or dirty file belongs to the agent. Preserve user changes and inspect the diff before editing.

## Access

Available SSH aliases:

```text
px10  px20  px30  dns  proxy  auth  s3  ctr  dev  orva  pc  pi
coolify
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
| `coolify` | Owner-created Debian VM 108 on px10, root SSH at `10.1.1.14`; QEMU agent verified after restart to kernel 6.12.111. Cloud-init drive and empty CD-ROM removed, cloud-init disabled, static networking preserved, existing HA registration retained. Owner-installed app is private at `https://coolify.l3b.cc.cd` via Caddy to port 8000; login page browser-verified, authenticated app operation not tested. See `infrastructure/coolify/README.md`. |

`slate` is a GCP free-tier VM in the US with Tailscale IP `100.122.33.37` and public IP `8.235.70.28`. It is online and offers an exit node. `dev` has a direct Tailscale client and verified `ssh slate` alias for `root@100.122.33.37`; this does not depend on MagicDNS. Native ntfy, a second Uptime Kuma, and custom Caddy now run there as systemd services with public HTTPS at `ntfy.l3b.cc.cd` and `watch.l3b.cc.cd`. Credentials are in separate `ntfy` and `Uptime Kuma - Slate` HomeLab vault items. Docker/Portainer Agent was fully removed, and `ctr` was not enrolled in Tailscale. See `infrastructure/slate/README.md`.

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

VM 204 `ctr` now uses fixed 16 GiB (`memory: 16384`, `balloon: 16384`), owner-approved and live-applied on 2026-09-30 without reboot. Full Intel iGPU PCI passthrough kept its 16 GiB locked on PX20 even when ballooning restricted the guest to 8 GiB. Do not restore the earlier 8–16 GiB dynamic policy for this passthrough VM. The balloon device stays enabled for statistics. See `infrastructure/ctr/README.md`; other guests' policies remain unchanged. Anchor v0.17.2 is Portainer stack 154 at private `https://notes.l3b.cc.cd`, with native Pocket ID, a same-email recovery account, local persistent `/data/apps/anchor`, and a Homepage Applications card. Native login and note/image persistence across restart were tested. Read `infrastructure/anchor/README.md` before upgrades or recovery; credentials are in the single HomeLab item `Anchor`.

Read the main README for the full endpoint table. Key infrastructure facts:

- LAN: `10.1.1.0/24`
- Router: `10.1.1.1`
- DNS: `10.1.1.2`
- Caddy proxy: `10.1.1.3`
- Cairn S3/API is deliberately public at `cairn-s3.l3b.cc.cd` with native S3 authentication/policies; its console `cairn.l3b.cc.cd` remains private. The temporary `share` hostname and RustFS public bucket were removed. The sanitized DNS guide is a separate [Notion page](https://app.notion.com/p/AdGuard-Home-Unbound-my-DNS-setup-3e5d3ccfb520818b8546c4dbca0ecdce) and `infrastructure/dns/SHAREABLE-SETUP.md`, not an S3 object. The historical Unbound listener/cache drift was corrected with persistent `recursive.conf` on 2026-09-27; see the later DNS runbook correction and verify live state before a restart.
- Public `store.l3b.cc.cd` is a static Astro storefront from `git@github.com:Harsh-2002/store.git`, built with `npm ci && npm run build` and served by Caddy from `/srv/store` on `proxy`. Cloudflare's explicit DNS-only A record targets `150.129.31.154`; internal Unbound resolves the name to `10.1.1.3`. This web name is distinct from the `store` SSH alias and SMB CT at `10.1.1.12`. See `infrastructure/proxy/README.md`.
- Orva serverless VM: `10.1.1.11` (VM 106; outbound-isolated by Proxmox firewall)
- Kubernetes API VIP: `10.1.1.200`
- Cilium LoadBalancer pool: `10.1.1.170-10.1.1.190`
- Tailscale: px10/px20/px30 are approved subnet routers for `10.1.1.0/24`; `dev` is a direct tailnet client. The former `10.1.1.9` gateway VIP was removed.
- Primary internal domain: `l3b.cc.cd`
- DNS is private by default; internet exposure requires an explicit Cloudflare record and corresponding Caddy policy.
- Pocket ID is the OIDC provider. Tinyauth protects services without native OIDC support.
- Portainer is the current Docker management interface. Komodo and Pulse are removed from live infrastructure; their repository directories are historical/rebuild documentation only.
- RustFS replaced MinIO. Do not redeploy MinIO unless specifically requested for recovery.

## Tailscale subnet routing and direct clients

Tailscale runs directly on all three Proxmox hosts. All three advertise and have approval for `10.1.1.0/24`, use `tag:subnet-router`, and have device-key expiry disabled. Tailscale's native subnet-router failover handles inbound tailnet-to-LAN access. The only persistent host services are `tailscaled.service` and `tailscale-gro.service`. Hosts have `accept-dns=false`, `accept-routes=false`, Tailscale SSH disabled, and native auto-update enabled.

On 2026-09-28 the owner retired the separate outbound gateway: `10.1.1.9`, Keepalived, the custom nft NAT table/service, and the health script were removed from all three Proxmox hosts. A Proxmox VM firewall bridge caused the old gateway NAT rule to miss same-host guest traffic. No router static route to the former VIP should be added. Guests that need outbound tailnet access run their own Tailscale client instead; `dev` now uses direct Tailscale `100.70.45.76`, with `accept-dns=false`, `accept-routes=false`, auto-update enabled, and no advertised routes. Its obsolete route through `10.1.1.9` was removed. `ssh slate` reaches `root@100.122.33.37` using a pinned SSH host key. Full verification and recovery instructions are in `infrastructure/tailscale/README.md`.

## Deployed versus planned

Music follow-up on 2026-09-30 supersedes the initial Lidarr integration-only test: public torrent searches found no source for the owner's single. Metadata now includes singles/EPs/soundtracks; Soularr 1.2.2 and slskd 0.26.0 were added to the existing Portainer `arr` stack with internal-only ports, no shared library files, one Soulseek vault item, and persistent config/download paths. The actual `Angels for Each Other` FLAC downloaded and imported automatically. A missing Jellyfin Music folder and obsolete `/mediabrowser` import-notification endpoint were corrected; Lidarr now uses a tested direct Music-library refresh webhook. Jellyfin lists and serves the track, and full-track FFmpeg decode passed. See `infrastructure/arr/README.md` for runtime template rendering, limits, metadata monitoring and validation boundaries. No source guarantees, inbound peer port forwarding or public music-file sharing are implied.

Lidarr and owner-approved Faustvii Readarr 0.10.0 were added to Portainer `arr` stack 153 on 2026-09-30. Both connect to Prowlarr, qBittorrent, Cleanuparr and Unpackerr; Lidarr updates Jellyfin's new Music library. Private URLs are `lidarr.l3b.cc.cd` and `readarr.l3b.cc.cd`, credentials are in canonical vault items, and music/books have separate AV directories/categories. Lookup and connection tests passed; no actual music/book download was initiated. Do not restore retired original Readarr, whose qBittorrent HTTP 204 handling and Goodreads lookup failed. See `infrastructure/arr/README.md` for versions, profiles and limitations.

Do not present a documented design as an applied change.

Deployed and verified:

- Three-node Proxmox cluster and HA/replication described in the service runbooks
- AdGuard Home plus Unbound
- Caddy wildcard TLS and private/public access policy
- Talos Kubernetes, Argo CD, Cilium, Longhorn, Headlamp, Homepage, and metrics-server
- Pocket ID/Tinyauth authentication
- Beszel and internal Uptime Kuma
- External native ntfy and Uptime Kuma on `slate`, behind Cloudflare DNS-01 Caddy; all six external monitors were UP and their restricted ntfy test notification succeeded on 2026-09-28. The owner still needs to subscribe the iOS ntfy client and verify background push.
- Private Grafana and VictoriaMetrics in Beszel CT 104, with Pocket ID OIDC, 30-day metrics retention, Proxmox and Kubernetes exporters, and three linked provisioned dashboards: Infrastructure Overview (home), Compute & Guests, and Storage & Backups. A 15-minute textfile timer on store CT 109 exports BACKUP archive freshness; PBS metrics are retired. See `infrastructure/metrics/README.md`. Kubernetes vmagent is GitOps-managed, but its remote-write Secret is created separately from the HomeLab 1Password vault.
- Portainer-managed Docker workloads including restored applications
- Portainer stack 153 `arr` connects Seerr, Prowlarr, Radarr, Sonarr, Bazarr and qBittorrent to Jellyfin. The 2026-09-29 audit fixed a CIFS hardlink-open playback failure with persistent `nolease` on `ctr`'s AV mount, enabled native Jellyfin update connections and Seerr libraries, and verified browser QSV playback plus seek. All six ARR containers have health checks. Read `infrastructure/arr/README.md` and `infrastructure/arr/RCA-2026-09-29.md`; a library listing alone does not prove playback.
- Portainer Stack 85 `n8n` on `ctr` now owns n8n 2.40.7, PostgreSQL, SearXNG, and Sandbox Service 1.4.0. SearXNG is internal at `http://searxng:8080`, with JSON search enabled; the sandbox API is internal at `http://sandbox-api:8080`. The privileged mTLS runner stays on a private control bridge and neither backend publishes a host port. JSON search and authenticated sandbox create/execute/delete were verified. Former separate Stack 150 was deleted after consolidation without deleting its persistent API state or TLS volume. Secrets remain in the existing `N8N` and `n8n Sandbox` HomeLab vault items; see `infrastructure/n8n/README.md`.
- The 4 TB Crucial X9 Pro was reformatted on 2026-09-23; the former whole-system tar and recovery tree were erased at the owner's request. Its two existing ext4 LVs are mounted on px10 and bound into unprivileged Debian CT 109 `store` (`10.1.1.12`): ~1.64 TiB `AV` and 2 TiB `BACKUP`. A separate 256 GB USB SSD on px10 (serial ending `1716`) is mounted/bound as `ISO`; do not confuse it with px20's spare 256 GB SSD (serial ending `1741`). CT 109 has 1 vCPU, 4 GiB RAM, 1 GiB swap, and an 8 GiB local-zfs OS disk; that OS disk replicates to px20 every five minutes, with HA restricted to px10/px20. The external USB data does **not** replicate: move **both SSDs** physically to px20 and mount all three filesystems there before relying on the shares after px10 failure. A Proxmox pre-start hook checks real UUID-mounted filesystems and markers, so HA will fail safe without the disks. See `infrastructure/store/README.md`.
- Samba 4.22.11 exposes three separate SMB3-encrypted shares with the same `Store SMB` vault credential: `smb://smb.l3b.cc.cd/AV` for general files, `smb://smb.l3b.cc.cd/BACKUP` for native Proxmox backups, and `smb://smb.l3b.cc.cd/ISO` for shared installers/templates. They are direct LAN SMB, not HTTPS/Caddy. Disk-marker checks prevent serving empty mount directories. Beszel agent and Node Exporter run in CT 109.
- VM 204 `ctr` mounts the encrypted SMB3 share persistently at `/mnt/AV` using a systemd automount; Motrix defaults to `/mnt/AV/downloads` and can also save under `/mnt/AV/media`, while Jellyfin indexes `/mnt/AV/media/movies` and `/mnt/AV/media/shows`. The root-only CIFS credential comes from the existing `Store SMB` vault item. Application databases/config stay on local `/data/apps`. Motrix is Portainer stack `motrix` (ID 152), private at `https://downloads.l3b.cc.cd`; see `infrastructure/ctr/README.md` and `infrastructure/motrix/README.md`.
- Cluster-wide PVE storage `BACKUP` is CIFS/SMB on CT 109 and shows backups directly in each Proxmox UI. Job `critical-to-backup` backs up VM 100 and CT 101–105 daily at 02:00 Asia/Kolkata; job `ctr-to-backup` backs up VM 204 at 03:00. Both use snapshot mode, zstd, one worker, and `keep-last=1`. These are **full file archives**, not PBS incremental backups. K8s/Longhorn, orva, and store itself are excluded. The latest successful archives for all seven guests were visible on all nodes on 2026-09-29; the VM 204 archive passed independent `zstd -t` validation before two invalid partials were permanently removed. CT 102 was previously test-restored to temporary CT 110 and then purged. The old PBS VM 107, its datastore, storage/job objects, OIDC client, Homepage card, Caddy route, and three PBS-only vault items were removed.
- Cluster-wide PVE storage `ISO` is CIFS/SMB on CT 109 with `iso,vztmpl,images` content for installer media, LXC templates, and staging VM disk images. The former px10-only `iso-store` was removed after verifying no guest configuration referenced it. The existing Omarchy ISO and Debian 13 LXC template remain on the same ext4 SSD; the obsolete PBS installer ISO was removed. All three nodes list and can write to `ISO`. Existing installed guests do not depend on source install media unless an ISO remains attached as a configured CD-ROM.
- px20's separate 256 GB USB SSD is an unmounted, unregistered spare: the empty `backup-store` storage entry and its `/etc/fstab` mount were removed without formatting or wiping the disk. See `infrastructure/proxmox/README.md`.
- Samba is SMB3-only, signing-required, and bound to `10.1.1.12`; log in to any share as `iam.anuragvishwakarma@gmail.com` using the `Store SMB` vault credential (mapped to local `iam.anuragvishwakarma`, not PAM/OIDC). The `BACKUP` Proxmox storage uses a cluster-private copy of the same password at `/etc/pve/priv/storage/BACKUP.pw`.
- OpenViking v0.4.22 is Portainer stack `openviking` on `ctr`, private via Caddy at `https://memory.l3b.cc.cd`, MCP at `/mcp`, with bot mode for Web Studio Agent chat. Pocket ID OIDC through Tinyauth protects `/studio*`; the backend stays in API-key mode because v0.4.22 Studio does not support native OIDC, and agents need their user key. Local Ollama `all-minilm` handles embeddings; the VLM uses the official `openai-codex` provider and `gpt-6-luna` through persisted Codex OAuth, not Groq/Cerebras API keys. Data/config and protected `codex_auth.json` persist under `/data/apps/openviking/state`, Ollama model under `/data/apps/openviking/ollama`. Portainer holds only the root key from the HomeLab vault; that vault item also holds the account-scoped `agent-key`. Dev Codex has the official `openviking-memory@openviking` plugin with its own MCP proxy and lifecycle hooks; a 0600 `ovcli.conf` is generated from the HomeLab vault via the tracked template. The old standalone MCP helper was removed. All six plugin hooks were reviewed/trusted on 2026-09-29, and the doctor check passed; review changed hooks again after updates. Post-restart VLM, embedding, and memory search checks passed. See `infrastructure/openviking/README.md`.
- The OpenViking shared `agents` account contains a 2026-09-28 MCP-imported snapshot of the tracked runbooks, sanitized active configuration, all four relevant Notion pages, and the owner's working standards, refreshed for changed runbooks on 2026-09-29. Start with `viking://resources/homelab/START-HERE.md` and `viking://resources/homelab/OPERATING-STANDARDS.md`. It is a retrieval copy, not automatic Git/Notion sync or live truth. The Codex memory plugin hooks are trusted and can automatically capture transcripts, so avoid printing secrets into Codex sessions.
- Hermes Agent on `dev` runs under the existing `dev` account with default model `openai-codex/gpt-6-luna` at medium reasoning, Groq Whisper for incoming Telegram voice, and the built-in OpenViking provider using the same account-scoped agent key. Telegram bot `@heyhermesai_bot` is restricted to the owner's numeric ID through the HomeLab `Hermes Telegram Bot` vault item; `hermes-gateway.service` is a user systemd service with linger enabled and uses Telegram polling, no inbound proxy. At the owner's explicit request `approvals.mode: off` gives Hermes full command-approval bypass under the `dev` account; the non-bypassable hardline blocklist remains. The bot token was originally pasted into chat and must be rotated in BotFather, then updated in the vault and the live Hermes `.env`. The 0600 `.env` also holds a verified copy of the current `gh auth token` as `GITHUB_TOKEN`, plus existing Photon/iMessage and Home Assistant settings. Do not overwrite it with the smaller bootstrap template. Photon is configured, but its shared/free line rejects startup notifications to a new target until the allowed number texts the assigned line once. Web search uses Codex's `openai-native` backend. See `infrastructure/hermes/README.md`.
- Hermes' private dashboard is `https://hermes.l3b.cc.cd`, protected by the Pocket ID `hermes-dashboard` OIDC client and the existing Caddy private policy; a user browser sign-in test is still needed. Telegram is the configured proactive home channel, while Photon/iMessage can receive after the owner sends the first message to its assigned line. The durable shared user profile is `viking://user/iam-anuragvishwakarma/memories/anurag-profile.md`; read it for personalization, but live runbooks and the user's newest instructions take precedence. Hermes' short local copies are in `~/.hermes/SOUL.md` and `~/.hermes/memories/{USER,MEMORY}.md`.
- VM 107 is now `haos` (the old PBS VM with that ID was deleted earlier), running Home Assistant OS 18.3 on px30 at `10.1.1.13`, private via `https://home.l3b.cc.cd`. It has px30→px20 ZFS replication, restricted HA affinity, and a daily native backup job. The Buildroot-based HAOS image already runs `qemu-ga`; no guest-agent installation is needed. The official Terminal & SSH app is key-only on port 22 and starts on boot; `ssh haos` from dev opens that app container, not the HAOS host. Its reboot, SSH, Core API, and Caddy path were verified on 2026-09-29. Hermes and Homepage both use the owner-provided Home Assistant long-lived token, concealed in the existing HomeLab `Home Assistant` vault item and their respective protected runtime stores; no token is in Git. Homepage now shows Home Assistant live counts and healthy OpenViking/Hermes cards. Native HAOS has no generic OIDC provider; Pocket ID SSO would require a third-party auth integration, which was not installed. See `infrastructure/homeassistant/README.md` and `gitops/apps/homepage/README.md`.
- For a dated live-status check, read `infrastructure/openviking/CURRENT-STATE.md` and its OpenViking mirror. Its 2026-09-28 ISO/backup failures were resolved in the 2026-09-29 follow-up; independent off-site backup coverage remains absent. Verify current state again before troubleshooting.
- On 2026-09-28, `store` Samba was OOM-killed and did not restart, leaving the scheduled VM 204 backup hung and `ctr` I/O stalled. On 2026-09-29, live Samba credential drift was corrected, stale CIFS mounts cleared, CT 109 raised to 4 GiB RAM/1 GiB swap, and `smbd` restart-on-failure deployed. A new VM 204 backup was validated. Monitor the next scheduled cycles; see `infrastructure/store/README.md`.
- n8n's existing owner email was updated to `iam.anuragvishwakarma@gmail.com`, and native password + existing MFA login was verified.
- Fresh native Cairn service on the `s3` LXC beside RustFS, using separate ports and `/data/cairn`
- Native RustFS and migrated S3 workloads
- Three-node Tailscale subnet routing and direct Tailscale access from `dev`; the former gateway VIP was retired
- Persistent Intel I219 conservative NIC settings on px10, px20, and px30: TSO/GSO/GRO/EEE disabled by `e1000e-stability.service`; px10/px20 had transmit hangs, while px30's I219-LM has no recorded hangs and was aligned for consistency. An 8 GiB cross-node test sustained about 115 MB/s with zero NIC errors
- Paperless-ngx `3.2.1` runs as Portainer-owned Stack ID 149 on `ctr`, with SQLite/media under `/data/apps/paperless` and Valkey as broker. `https://docs.l3b.cc.cd` is private through Caddy with native Pocket ID OIDC; local login was tested as break-glass, while the passkey-protected OIDC return still needs owner verification. Homepage has a GitOps card. Secrets live in the two distinct `HomeLab` vault items `Paperless-ngx` and `Pocket ID OIDC - paperless` plus Portainer Stack Env; temporary plaintext files were removed. Use `scripts/op-sa` on `dev`: plain `op` does not load the existing service-account token file automatically. See `infrastructure/paperless/README.md`.

Planned but **not yet applied** at the time of this handoff:

- Extend independent backup coverage for application data, especially both OpenCloud metadata and its RustFS bucket. The current `BACKUP` archives and `AV` files share one physical SSD and are not an off-site backup; the former whole-system recovery tar no longer exists.
- Test ntfy iOS background delivery after subscribing to the self-hosted `infra` topic; server-side upstream push and restricted publishing are configured, but mobile delivery cannot be verified without the owner's device.
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
