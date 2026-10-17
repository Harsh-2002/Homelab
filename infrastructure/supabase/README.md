# Supabase

Dedicated Debian VM **108**, `supabase`, **PX30**, `10.1.1.14`. Direct Docker Compose over SSH, not Portainer. Main file: **`/srv/supabase/docker-compose.yaml`**. Existing Caddy proxies **https://supabase.l3b.cc.cd** to Envoy on `10.1.1.14:8000`. LAN/Tailscale only; no public DNS exception. Retired ZimaOS no longer owns this address or Caddy route. Its old orphaned ISO disk was not touched.

## Access and ownership

- `ssh supabase` uses the password-locked `supabase` OS administrator with key authentication and passwordless sudo. Root key-only access remains break-glass. The administrator is not in the Docker group; Docker management is root-equivalent.
- Stack/config/data: `/srv/supabase`, root-owned, mode0700. Protected `.env` and `homelab.env`:0600. Upstream non-secret bind assets must be readable by container UIDs; the initial staging umask issue is fixed in `prepare.sh`.
- Credentials/signing/encryption keys: canonical **HomeLab → Supabase** 1Password item, including concealed `deployment-env`, dashboard login and new publishable/secret API keys. Never print the rendered Compose config or reuse backend secret/service-role keys in browsers.
- Studio username: `supabase`; retrieve its password from the vault. Studio uses Envoy Basic authentication. Application Auth is separate. Public sign-up/anonymous/phone login and email auto-confirm are disabled. Google SMTP inputs were configured, but Gmail rejects the existing vault password with534/5.7.9. A valid Google app password is required; email delivery is not working/verified yet. Store it as concealed `app-password` in HomeLab→Google SMTP, then run `configure.py`, update the canonical deployment credential and recreate Auth. Do not mark email or production readiness complete until delivery is tested.
- VM:2vCPU,4GiB balloon minimum/8GiB maximum,50GB local-ZFS disk. Debian13, Docker29.9.1, Compose5.6.0, guest agent and NTP. Host/Docker use internal DNS10.1.1.2 only. Docker/containerd retain standard `/var/lib/docker` and `/var/lib/containerd` on the same persistent VM disk.

## Matched full suite

Initial upstream release **self-hosted/v0.8.3**, commit **bc27d2661edd09a5d0b8d76ce33da6d4071a756e**. Includes all13 services: PostgreSQL17, Studio, Envoy, Auth, PostgREST, Realtime, Storage, imgproxy, postgres-meta, Edge Runtime, Supavisor, Logflare and Vector. Analytics uses included PostgreSQL, not BigQuery. Watchtower is the14th maintenance container.

Only Envoy publishes LAN port8000. Proxmox VM firewall permits that port only from Caddy10.1.1.3; SSH permits LAN/Tailscale. PostgreSQL/pooler/analytics/Studio are not directly published. Vector and Watchtower have trusted Docker-socket access; a read-only socket mount is not a read-only Docker API.

Signing uses ES256 for user sessions plus legacy HS256 compatibility. The override supplies private signing JWKs only to Auth, public JWKS/legacy verification material to validators. `initialize.mjs` implements the pinned upstream key formats, including `key_ops`; it refuses existing secrets/database state. `repair-key-metadata.py` records the one-time metadata-only initialization repair without changing keys.

## Daily operation

The wrapper supplies the explicit project name, both protected env files, and every required override. Do not use upstream `run.sh` or bare `docker compose up` to bypass logs/security/update settings.

```bash
ssh supabase
sudo sh -c 'cd /srv/supabase && sh compose.sh ps'
sudo sh -c 'cd /srv/supabase && sh compose.sh logs --tail=80 auth'
sudo sh -c 'cd /srv/supabase && sh compose.sh config --quiet'
sudo sh -c 'cd /srv/supabase && sh compose.sh up -d --wait'
```

Layer order: `docker-compose.yaml`, upstream `docker-compose.logs.yml`, `compose.homelab.yaml`, initial `compose.images.yml` digest baseline, owner-approved `compose.auto-update.yaml` version tags, then `compose.watchtower.yaml`. Immutable upstream checkout stays in `.upstream`.

## Automatic updates: owner-approved override

Owner explicitly chose automatic replacement and image cleanup on October18 IST, superseding monitor-only. Maintained **nickfedor/watchtower:latest**, upstream **nicholas-fedor/watchtower**, currently1.23.1. Original containrrr image is not used.

- Schedule **04:00 IST daily**. `WATCHTOWER_MONITOR_ONLY=false`, `WATCHTOWER_CLEANUP=true`, `WATCHTOWER_LABEL_ENABLE=true`.
- All13 Supabase services and Watchtower are explicitly opted in. No volume removal, broad image prune, or exposed Docker API.
- Supabase follows its matched **current version tags**, not unrelated `latest` versions. Watchtower replaces an image when that tag's registry digest changes. It does **not** discover/bump newer version tags or run coordinated Supabase configuration/migration upgrades.
- `compose.images.yml` preserves the initial exact image set for investigation/rebuild. The later auto-update overlay intentionally removes digest pinning at runtime. Exact reproduction after automatic updates requires capturing deployed image digests, not assuming the initial lock describes the current deployment.
- Automatic per-image replacement can interrupt service or introduce an incompatible rebuild. Watchtower is not a database backup, rollback system or multi-service upgrade orchestrator. Changed image cleanup may require repulling a prior digest for recovery. No external update notifications are configured; inspect Watchtower logs.

## Persistence, HA and backups

Database: `volumes/db/data`; files:`volumes/storage`; functions:`volumes/functions`; snippets:`volumes/snippets`. Named volumes:`supabase_db-config` (includes PostgreSQL encryption/root-key configuration) and `supabase_deno-cache` (regenerable). Preserve keys and both databases, including platform/log database `_supabase`.

HA resource `vm:108`: primaryPX30, replica/recoveryPX10, strict affinity `vm108-replica-nodes`, failback/auto-rebalance off,2local restarts/1relocation. Replication **108-0**, PX30→PX10, every5minutes,20MB/s. Initial and post-install replication succeeded; the large image-download delta took longer than5minutes. Replication is asynchronous, may lose writes after the last completed sync and is not a backup. No destructive failover/fencing drill has been performed; target capacity still matters.

Backups:

- `supabase-backup.timer`: **03:50 IST**, keeps3complete sets under `/srv/supabase/backups`. `backup.sh` briefly stops application writers, takes globals plus both custom-format database dumps, Storage/functions/config and named db-config archive, then starts and waits for the full suite. This scheduled maintenance causes downtime. Failed sets remain for inspection. These local dumps alone are not independent off-host protection.
- Proxmox job **supabase-to-backup**: **04:30**, VM108, snapshot+zstd, storage **BACKUP**, keep-last3, follows VM across eligible nodes. Includes whole VM disk and local logical backups; guest-agent filesystem freeze is available.
- `supabase-log-retention.timer`: **03:15 IST**, removes analytics events older than7days, only `_analytics.log_events_<uuid>` tables. Docker logs independently use local10MiB×3 rotation. SQL deletion does not immediately shrink allocated PostgreSQL files; monitor space and autovacuum. It never deletes application tables or Storage files.

Both timers are enabled persistently. Inspect `systemctl list-timers 'supabase-*'`. Logical backups contain secrets and private files; keep mode0700/0600 and the existing BACKUP access controls. Reboot/VM restart is not a backup test. Database dump restore was tested in isolated databases; a complete replacement-VM disaster-recovery drill remains pending.

## Reproduction and recovery

1. Provision Debian, root public key and internal DNS; verify SSH host fingerprint through the trusted Proxmox guest console/agent. `bootstrap-vm.sh` uses the official Docker installer pinned to commit ada7a567e59b3935bd601bb21e422da50e80e376, creates the administrator, key-only SSH, Docker logging/DNS and guest agent. It refuses an existing Docker daemon configuration.
2. Run `sudo sh infrastructure/supabase/prepare.sh /srv/supabase` from this repo. It fetches/verifies the pinned upstream commit and refuses an existing destination. Main upstream file is renamed to `docker-compose.yaml`; upstream assets stay unmodified otherwise.
3. For a **fresh** project only, `sudo node infrastructure/supabase/initialize.mjs /srv/supabase`. For recovery, **restore existing `.env` and encryption keys instead**. Never regenerate keys against data.
4. Copy `site.env.example` to protected `homelab.env`. Configure site/SMTP with `configure.py` and a protected vault-item JSON input; delete that temporary input afterward. Save final env using `save-vault.py` without printing values. Reuse the canonical Supabase vault item, not duplicate items.
5. Copy/install `backup.sh`, `log-retention.sql`, corresponding systemd units/timers, VM firewall108.fw, HA/replication and Caddy route. `bootstrap-vm.sh` is a provisioning tool, not an idempotent full rebuild orchestrator. Restore DB roles, both databases, data/files/config and named db-config before admitting traffic. Docker pull/start does not restore user data.
6. Use wrapper `config --quiet`, `pull`, `up -d --wait`. Validate with `validate.py --keep` (Debian package `python3-websocket` is a test dependency) and `validate-logs.py`. Scripts never print API keys. Acceptance fixtures live in protected `.acceptance.json`; `validate.py --cleanup` removes only those fixtures.

For a new Supabase release, review upstream release/migrations; update source pin, matched image versions and initial locks, test a restored isolated stack, then deploy the matched set in a maintenance window. An old image may not understand migrated data; rollback may require restoring a consistent backup. Do not copy upstream example data directories over live data. Restore the initial locks only deliberately, not as an automatic downgrade.

## Acceptance record

On October18 IST all13 Supabase services and Watchtower reached healthy. HTTPS, dashboard Basic auth, missing/invalid API auth denial, ES256 sessions, refresh, two-user REST RLS CRUD/isolation, private Storage upload/read and signed expiry, Edge Function auth/execution, Realtime update delivery/RLS/invalid-token denial passed. Tests passed again after complete container recreation. Logflare query returned real Auth events ingested through Vector. Reboot issued and VM boot verified at03:34IST; final post-reboot validation is recorded in CURRENT-STATE.md.

First coordinated backup completed; PostgreSQL application dump restored into isolated `acceptance_restore` and contained2test rows/1Storage metadata object; platform dump restored into isolated `acceptance_platform_restore`. This is not a full replacement-VM restore or proven mail delivery. Temporary fixtures/restore databases are removed after final validation.

An exploratory Logflare `/api/sources` management request hit upstream1.50.15's nil BigQuery-project formatting path on this PostgreSQL-only installation. Studio's actual SQL query API and ingestion passed; no dummy Google project/cloud service was introduced to mask that unrelated endpoint limitation. Initial first-boot seed cache error disappeared after seeding/restart.

Sources: [official Docker deployment](https://supabase.com/docs/guides/self-hosting/docker), [reverse proxy](https://supabase.com/docs/guides/self-hosting/self-hosted-proxy-https), [pinned source](https://github.com/supabase/supabase/tree/bc27d2661edd09a5d0b8d76ce33da6d4071a756e/docker), [maintained Watchtower](https://github.com/nicholas-fedor/watchtower).
