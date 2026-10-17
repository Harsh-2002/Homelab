# Supabase

## Current endpoint split (October18 IST)

Studio stays **https://supabase.l3b.cc.cd** behind existing Pocket ID/Tinyauth. Canonical application API **https://sb.l3b.cc.cd** and MCP **https://sb.l3b.cc.cd/mcp**. Studio's runtime project settings and database-connect metadata were checked: endpoint/db_host `sb.l3b.cc.cd`, db_port5432, db_user `postgres`, database `postgres`, REST URL `https://sb.l3b.cc.cd/rest/v1/`. Internal POSTGRES_HOST remains `db`. The old Supabase-domain API/MCP routes remain authenticated compatibility aliases; no duplicate stack. On `sb`, unrelated dashboard/admin paths return404, not an unprotected Studio. Existing agents on dev now use `sb` with their unchanged dedicated Bearer key; all3 configs authenticate and discover11tools. Hermes graceful gateway reload requested; new Codex/Claude sessions load the new URL.

PostgreSQL: **sb.l3b.cc.cd:5432**, DB **postgres**, user **postgres**, password from the concealed deployment-env POSTGRES_PASSWORD field in HomeLab→Supabase. Use **sslmode=verify-full** and your system CA bundle. `sb` resolves to Caddy10.1.1.3, not directly to the VM. Existing caddy-l4 v0.1.2 negotiates PostgreSQL SSLRequest, requires TLS (ALPNpostgresql), and forwards to10.1.1.14:5432. Source allowlist LAN/Tailscale, listener bound only10.1.1.3. VM firewall allows backend5432 only from Caddy. Caddy→database hop is plaintext on the trusted LAN, like existing HTTP upstreams; this is client-to-Caddy TLS, not end-to-end DB TLS. No router/public-port exposure added. Plaintext startup does not match the TLS-only route. Supavisor remains internal and its tenant-suffixed session username is NOT used on this direct-database endpoint. Transaction pooler6543 remains unpublished.

`SUPABASE_PUBLIC_URL` and `API_EXTERNAL_URL` changed in protected `.env` and homelab.env via `set-endpoints.py`, with pre-change backups. Current Auth issuer is `https://sb.l3b.cc.cd/auth/v1`; previously issued sessions may need fresh sign-in after this issuer change. Database/user data and signing/API/MCP keys were not regenerated. Compose recreated only affected services; publishing the direct DB port required a brief DB-container restart, not a VM reboot. TLS hostname/certificate plus real password SQL and invalid-password rejection passed; `validate-postgres.py` reproduces the checks. The explicit endpoint/port statements here supersede older no-published-DB and Supabase-domain API statements below.

Same VM also hosts independent [PocketBase](../pocketbase/README.md), with separate `/srv/pocketbase` project/data/credentials and private `pocketbase.l3b.cc.cd`. Do not treat Supabase SQL dumps as PocketBase backups.

Dedicated Debian VM **108**, `supabase`, **PX30**, `10.1.1.14`. Direct Docker Compose over SSH, not Portainer. Main file: **`/srv/supabase/docker-compose.yaml`**. Existing Caddy proxies **https://supabase.l3b.cc.cd** to Envoy on `10.1.1.14:8000`. LAN/Tailscale only; no public DNS exception. Retired ZimaOS no longer owns this address or Caddy route. Its old orphaned ISO disk was not touched.

## Access and ownership

- `ssh supabase` uses the password-locked `supabase` OS administrator with key authentication and passwordless sudo. Root key-only access remains break-glass. The administrator is not in the Docker group; Docker management is root-equivalent.
- Stack/config/data: `/srv/supabase`, root-owned, mode0700. Protected `.env` and `homelab.env`:0600. Upstream non-secret bind assets must be readable by container UIDs; the initial staging umask issue is fixed in `prepare.sh`.
- Credentials/signing/encryption keys: canonical **HomeLab → Supabase** 1Password item, including concealed `deployment-env`, dashboard login and new publishable/secret API keys. Never print the rendered Compose config or reuse backend secret/service-role keys in browsers.
- **Studio login is Pocket ID through existing Tinyauth**, not the browser Basic-auth popup. Exact owner email plus `infrastructure-admins` group required. Dashboard credentials in the vault are now backend-only; Caddy supplies them after SSO. Application Auth is separate. Public sign-up/anonymous/phone login and email auto-confirm are disabled. Google SMTP inputs were configured, but Gmail rejects the existing vault password with534/5.7.9. A valid Google app password is required; email delivery is deferred by owner. Store it as concealed `app-password` in HomeLab→Google SMTP, then run `configure.py`, update the canonical deployment credential and recreate Auth. Do not mark email or production readiness complete until delivery is tested.
- VM:2vCPU,4GiB balloon minimum/8GiB maximum,50GB local-ZFS disk. Debian13, Docker29.9.1, Compose5.6.0, guest agent and NTP. Host/Docker use internal DNS10.1.1.2 only. Docker/containerd retain standard `/var/lib/docker` and `/var/lib/containerd` on the same persistent VM disk.

## Matched full suite

Initial upstream release **self-hosted/v0.8.3**, commit **bc27d2661edd09a5d0b8d76ce33da6d4071a756e**. Includes all13 services: PostgreSQL17, Studio, Envoy, Auth, PostgREST, Realtime, Storage, imgproxy, postgres-meta, Edge Runtime, Supavisor, Logflare and Vector. Analytics uses included PostgreSQL, not BigQuery. Watchtower is the14th maintenance container.

Only Envoy publishes LAN port8000. Proxmox VM firewall permits that port only from Caddy10.1.1.3; SSH permits LAN/Tailscale. PostgreSQL/pooler/analytics/Studio are not directly published. Vector and Watchtower have trusted Docker-socket access; a read-only socket mount is not a read-only Docker API.

Signing uses ES256 for user sessions plus legacy HS256 compatibility. The override supplies private signing JWKs only to Auth, public JWKS/legacy verification material to validators. `initialize.mjs` implements the pinned upstream key formats, including `key_ops`; it refuses existing secrets/database state. `repair-key-metadata.py` records the one-time metadata-only initialization repair without changing keys.

## Daily operation

### Agent MCP access

Native Streamable HTTP endpoint **`https://supabase.l3b.cc.cd/mcp`**, LAN/Tailscale only. Agents send **`Authorization: Bearer <dedicated-key>`**. Retrieve the concealed **`mcp-api-key`** field from the existing HomeLab **Supabase** item; `mcp-url` stores the endpoint. This is a separately generated256-bit key, not a publishable/secret/service-role key and not a Supabase Cloud personal token. No browser/OAuth exchange required for MCP. Authentication is enforced by existing Caddy, not natively by self-hosted Studio.

This key permits powerful single-project administrative tools, including SQL and migrations; do not give it to frontend code or untrusted agents. The optional `?read_only=true` server mode can reduce accidental writes, but a caller holding this unrestricted key can omit that option: it is not a separate read-only credential boundary. Scope narrower credentials/routes separately if needed. Current toolset:11tools for docs, tables/extensions/migrations, SQL, logs/advisors, project URL/publishable keys and TypeScript types. Self-hosted MCP is not Supabase Cloud's entire multi-project management API.

`enable-mcp.py /srv/supabase` generates the key once into protected `.env`, backs up the pinned Envoy template and allows `/mcp` only from direct peer **10.1.1.3/32**. It preserves the separate `/api/mcp` deny and refuses unknown upstream template changes. Restart only `supabase-envoy` to render the template; no database/container-data recreation. Other LAN hosts are blocked from raw8000 by the VM firewall, and internal Docker peers are not allowlisted by this MCP RBAC rule.

Run `sync-mcp-auth.py` on dev to copy the key via SSH stdin into protected proxy `/etc/caddy/cloudflare.env`; restart Caddy after adding/changing env, then test normal reload. Save the updated deployment environment using `save-vault.py`; it preserves unrelated existing vault fields and adds MCP metadata. Restore/rotation must keep both copies synchronized. Missing/incorrect keys return401 Bearer, never redirect to Pocket ID. SSO cookies or app API keys do not authorize this route. Caddy strips the dedicated key and cookies before forwarding to Studio, avoiding leakage into downstream handlers. `Cache-Control: no-store` is set. `/api/mcp` remains denied independently; do not open it as a shortcut.

Validation: `python3 infrastructure/supabase/validate-mcp.py` from dev reads the key securely without printing it and checks missing/invalid keys, initialize,11-tool discovery, read-only health SQL, temporary-table write and alternate-route denial. MCP protocol2025-03-26 verified. Native server is stateless POST/JSON Streamable HTTP; GET returning405 is not failed authentication.

### Local agent clients on dev

At owner's request, server **supabase** is configured globally for the dev account in Codex `/home/dev/.codex/config.toml`, Claude Code `/home/dev/.claude.json` (user-scope `mcpServers`) and Hermes `/home/dev/.hermes/config.yaml` (`mcp_servers`). Each uses the native HTTP endpoint and a direct Authorization Bearer header. No shell export or browser login needed. Real credentials stay only in protected live configs, never repository templates. These files are mode0600; private pre-change backups are under `/home/dev/.local/state/supabase-mcp-config-backups/` (0700).

The public server entries were added using apply_patch; `inject-agent-mcp-key.py` then mechanically injected only the unique header values from the canonical vault item without exposing them in command arguments/output. It also supports rotation of existing Supabase header values after the server/proxy/vault key is updated. It intentionally refuses absent/ambiguous entries or an unrelated current credential. It preserves file text, other settings and server entries; parse-and-compare checks confirmed all unrelated settings unchanged.

Verification: each parsed client config authenticated and discovered11tools; Codex native config parser recognized the server; Claude's native `mcp get supabase` reported Connected and Hermes `mcp test supabase` connected/discovered11tools. Hermes gateway completed its existing graceful SIGUSR1/systemctl user reload, with a new active process at22:39:15UTC. Existing Codex/Claude processes need a new session/restart to load the server. The current Codex chat cannot acquire new MCP tools merely by writing its config.

Reproduction order: initialize/restore protected env, run enable helper, save vault/sync key, validate/apply Caddy route with protected env loaded, restart Caddy for env, restart Envoy, run validation. Existing backup.sh includes the modified gateway templates and `.env`; Supabase VM backup also preserves them. Do not expose this upstream MCP directly to the Internet: native OAuth/PAT protection is absent. Keep the source-network boundary even with the proxy key.

### Studio SSO reproduction and credential rotation

`tinyauth.rules` installs as `/etc/tinyauth/supabase.env` on auth, with `tinyauth.conf` at `/etc/systemd/system/tinyauth.service.d/supabase.conf`. It adds the exact Supabase domain, owner email whitelist and required admin group without replacing other application rules or OAuth secrets. Restart Tinyauth after changing its rules.

Run `python3 infrastructure/supabase/sync-studio-auth.py` from dev to derive the backend Basic credential from the protected Supabase environment and securely sync `SUPABASE_STUDIO_AUTH` to proxy's `/etc/caddy/cloudflare.env`. It sends the secret via SSH stdin, never argv/stdout. No secret is tracked in Git. After adding/changing that environment variable, validate with the protected env loaded and restart Caddy once so normal systemd reloads inherit the updated environment. Existing Caddy systemd EnvironmentFile already loads it. On a restored proxy, sync this value **before** applying the Caddy route. Rotate dashboard credentials only with this sync step; mismatches fail closed with401. Caddy strips the backend dashboard challenge header so even a credential mismatch cannot restore the browser popup.

Caddy allows standard Auth/REST/GraphQL/Realtime/Storage/Functions API paths through without interactive SSO, preserving API keys and JWTs. Realtime administrative `/realtime/v1/api*`, `/pg`, Studio `/api/*`, MCP and all other dashboard paths pass through SSO first; Envoy's existing RBAC still applies. Backend Envoy Basic authentication remains defense-in-depth, but browsers never enter those credentials. Missing SSO fails closed. No image patches, new proxy, new ports, or changes to application Auth users. Browser navigation reaches Pocket ID; programmatic requests may get401 with `X-Tinyauth-Location`, never `WWW-Authenticate: Basic` from the normal frontend. Confirmed root old-Basic/spoofed-identity bypass attempts fail; final passkey-authenticated dashboard check requires the owner.

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
