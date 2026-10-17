# PocketBase on Supabase VM108

Private **https://pocketbase.l3b.cc.cd/_/** dashboard, API base **https://pocketbase.l3b.cc.cd**. Same Debian VM108, PX30,10.1.1.14 as Supabase. Separate Docker Compose project `pocketbase`, container `pocketbase`, persistent state **`/srv/pocketbase/pb_data`**. No shared database or Supabase credentials, no extra proxy/database.

Homepage lists PocketBase beside Supabase in Applications, using the project's official logo and `/api/health` status check. No PocketBase credentials are added to Homepage. Configuration remains in the existing Homepage Helm chart, deployed through Argo CD.

## Access and security

- Credentials: **HomeLab → PocketBase - VM108**, item `lbfxefhqh4mohpisoavspfuqem`. Older differently capitalized `Pocketbase` item belongs to previous context and was not modified. Use the exact new title/ID to avoid ambiguous CLI lookups.
- Caddy reuses existing wildcard TLS, permits LAN10.1.1.0/24 and Tailscale100.64/10 only. VM firewall permits raw8090 only from Caddy10.1.1.3; it is not a public endpoint. DNS already resolves through the existing wildcard to10.1.1.3.
- Native PocketBase superuser email/password authentication, not Pocket ID SSO. No unverified OIDC plugin added. New collections keep default locked API rules until deliberately configured. Do not distribute superuser tokens to frontends.
- Root-protected `/srv/pocketbase/.env` supplies initial superuser credentials; migration reads environment, so no password in argv, image or Git. The migration only runs once. Changing `.env` later does not rotate the existing account password.
- Nonroot UID/GID10001, read-only root filesystem, dropped capabilities, no-new-privileges, tmpfs,512MiB memory limit/384MiB Go soft limit,0.75CPU, log rotation. Rate limiter enabled; trusted X-Forwarded-For only safe because raw backend access is restricted to Caddy, which sanitizes it.

## Reproduce

Official **v0.40.5**, published2026-10-08, linux-amd64 ZIP SHA256 `1dbea1b01eb3dfe64953513859d01e759c96650c4e3264fa4eecd54b769382e4`. Official project does not publish an official Docker image; this minimal two-stage Dockerfile packages the official checksum-verified binary. Alpine3.23 base digest is pinned. CA package is installed from Alpine's repository at build time, so this is not a fully bit-for-bit reproducible package dependency lock.

1. Install files from this directory to `/srv/pocketbase`, root directory0700; migrations/hooks directories0755, files0644. Create `pb_data`0700 owned10001:10001 and an empty `pb_hooks` directory. Never replace an existing data directory.
2. On dev run `python3 infrastructure/pocketbase/bootstrap.py` for a fresh deployment. It reuses the exact canonical vault item if present, refuses to overwrite `.env`, and transfers secrets only through SSH stdin. Recovery must restore original data and credentials instead of creating a new admin against old state.
3. `ssh supabase 'sudo docker compose -f /srv/pocketbase/docker-compose.yaml up -d --build --wait'`.
4. Apply tracked VM108 firewall and Caddy route, validate Caddy with its protected environment loaded before reload. Existing proxy/VM infrastructure remains authoritative.
5. `python3 infrastructure/pocketbase/validate.py` from dev. Tests real superuser auth, unauthenticated denial, locked collection CRUD, built-in backup and persistence after force-recreating the container; deletes its temporary collection afterward.

## Backups, upgrades and limits

Built-in SQLite-safe local ZIP backup daily **22:00UTC /03:30IST**, keep3 cron-generated archives under `pb_data/backups`. Initial `homelab-initial-acceptance.zip` was created and verified listed across recreation; it is a manual archive outside cron retention. Whole VM108 backup job includes `/srv/pocketbase` and its local backups; existing VM HA/replication applies to the whole VM. Supabase's logical dump script does NOT back up PocketBase separately. Keep the off-host VM backup working; local ZIPs alone are not independent protection.

Do not copy a live SQLite data directory as an application-consistent backup. Use the built-in backup API/UI, or stop PocketBase before copying. Restore has not yet been drilled. Startup/restart persistence, backup creation and API CRUD are tested, not complete disaster recovery or HA failover.

PocketBase is pre1.0: review release/migration notes and take a backup before upgrading. This local image is deliberately not enrolled in registry-based Watchtower; rebuilding/upgrading this image is controlled, not a misleading auto-update claim. Preserve `pb_data`, migrations, hooks, `.env` and Compose configuration. Hooks can execute code; install only trusted hooks.

SMTP was not configured. Email verification/reset and email-based superuser MFA require a valid mail setup; Supabase's deferred Gmail app-password issue is not bypassed here.

Official references: [deployment](https://pocketbase.io/docs/going-to-production/), [migrations](https://pocketbase.io/docs/js-migrations/), [settings API](https://pocketbase.io/docs/api-settings/), [backups API](https://pocketbase.io/docs/api-backups/).
