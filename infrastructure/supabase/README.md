# Supabase: prepared, not deployed

Owner-approved design: dedicated Debian VM on PX30, direct Docker Compose over SSH, full self-hosted suite including Logflare/Vector. No Portainer registration/agent or remote Docker API. Existing Caddy on `10.1.1.3` terminates HTTPS and proxies to Envoy on the VM's LAN port 8000. No additional proxy container, database or object-storage dependency is added.

The VM, ID, address, hostnames, application redirect URLs, SMTP account and public/private API exposure are **not assigned yet**. Do not reuse deleted ZimaOS VM 108 or its address without checking allocation. No service, DNS, Caddy, firewall, HA or backup configuration was applied during preparation. Container startup and end-to-end validation await the owner's ready VM.

## Reproducible inputs

- Upstream release `self-hosted/v0.8.3`, verified commit `bc27d2661edd09a5d0b8d76ce33da6d4071a756e`. `prepare.sh` fetches this immutable revision, checks HEAD, retains upstream source and copies its complete `docker/` tree, including initialization SQL, Envoy, logs and functions configuration. It refuses an existing destination and never pulls/starts images or generates secrets.
- `compose.homelab.yaml` layers over upstream base **and** `docker-compose.logs.yml`; the wrapper always includes all three, with project name `supabase`.
- `compose.images.yml` locks all 13 upstream image references to registry SHA-256 digests, resolved and reviewed during preparation. `prepare.sh` copies this lock; the wrapper refuses to start without it. Verify architecture compatibility on the new VM before pulling. Source pinning alone does not make mutable image tags immutable. Change the lock only as an intentional reviewed upgrade.
- `homelab.env.example` contains only unset site inputs and deliberate policy defaults. Actual `.env` and `homelab.env` are root-owned mode 0600, outside Git. Store all generated credentials/signing/encryption keys in one canonical HomeLab 1Password item at deployment. Rebuilding an existing installation must **restore** those keys, not generate replacements.

Full suite: PostgreSQL 17, Studio, Envoy, Auth, PostgREST, Realtime, Storage, imgproxy, postgres-meta, Edge Runtime, Supavisor, Logflare and Vector. Logflare uses the included PostgreSQL backend; no BigQuery account is needed. Studio's Logs feature is enabled by the official logs override.

## VM and networking

Recommended starting allocation: 4 vCPU, 8 GiB RAM and 80 GiB SSD-backed local-ZFS storage, subject to cluster/failover capacity checks. Two vCPU is a smaller starting option, not an equivalent production capacity guarantee. Do not rely on ballooning to recover memory already consumed by the full suite. OS and containers use the internal DNS resolver; no public DNS fallback. Enable guest agent, time sync, Docker boot startup, host monitoring and firewall rules during VM provisioning.

Persist the deployment at `/data/apps/supabase`. Upstream relative mounts keep PostgreSQL data, Storage files, database configuration/key material, functions and snippets under that directory or the documented Compose volumes. Back up all of these, including named volumes `db-config` and `deno-cache` as appropriate; the latter is a regenerable cache. Container recreation is not a database restore. Keep live data off USB/CIFS/ISO storage.

Only Envoy is published, bound to `SUPABASE_BIND_IP:8000`. Firewall access to that port to Caddy and explicitly approved test clients; Docker publishing requires checking Docker-aware host rules and Proxmox firewall, not assuming UFW blocks it. PostgreSQL/pooler ports are deliberately not published. Add narrowly bound database access later only if a documented client needs it. Vector has the official Docker-socket mount: even read-only socket mounting does not make Docker API access read-only; keep this trusted collector private.

Caddy forwards HTTPS to `http://<VM-IP>:8000` with normal forwarded headers and WebSocket support. Configure final `SUPABASE_PUBLIC_URL`, `API_EXTERNAL_URL=<base>/auth/v1`, `SITE_URL=<frontend URL>` and exact redirect allowlist. Keep Studio/admin/MCP private and protected; do not put interactive Tinyauth redirects in front of application API routes. Public API exposure requires explicit owner approval, DNS and path-policy review. Do not deploy a broad public root route assuming Studio's default Basic auth is the complete production security boundary.

## Preparation and first deployment

Prerequisites on the new VM: supported Debian, Git, OpenSSL, jq, Docker Engine and Compose supporting `!override` (Compose 2.24.4+). Docker requires no public TCP socket; manage via SSH and its local Unix socket. Review upstream scripts before running them.

```bash
# Run on the new VM from this cloned repository, only when ready.
sudo sh infrastructure/supabase/prepare.sh /data/apps/supabase
cd /data/apps/supabase
sudo cp .env.example .env
sudo cp homelab.env.example homelab.env
sudo chmod 600 .env homelab.env
```

Before starting:

1. Set a strong unique PostgreSQL password and dashboard password, meaningful pooler tenant ID and real SMTP configuration in `.env`. Do not retain sample mail credentials or the fake SMTP host. SMTP credentials stay in the protected runtime file/vault, never Git.
2. For a **fresh installation only**, use upstream `utils/generate-keys.sh --update-env` and `utils/add-new-auth-keys.sh` according to their pinned help/source. They print secrets, so redirect their output into a protected temporary location, do not capture it in agent logs, and save the final material to the vault. Verify asymmetric keys are wired into all relevant services as upstream requires. Never regenerate encryption/JWT secrets against an existing data directory.
3. Populate `homelab.env` with VM IP and final HTTPS/frontend URLs. Defaults disable public sign-up, anonymous/phone login and email auto-confirm. Enable only the application features explicitly needed. JWT verification defaults on for Edge Functions; test the actual chosen API-key/JWT flow, rather than assuming every key type is interchangeable.
4. Verify URLs, password/key strength, SMTP, disk ownership/space and no sample credentials. Do not print the rendered Compose configuration: it contains secrets. Configure log database retention/size monitoring before production; Docker's 10 MiB × 3 rotation bounds container logs, **not** PostgreSQL analytics table growth.
5. Review the included digest lock and validate final configuration, then pull/start:

```bash
sudo sh compose.sh config --quiet
sudo sh compose.sh config --images
sudo sh compose.sh pull
sudo sh compose.sh up -d --wait
sudo sh compose.sh ps
```

The wrapper's startup checks are guardrails, not comprehensive production certification. Do not use upstream `run.sh start` to bypass the homelab override. Use `sh compose.sh logs --tail=100 SERVICE` for bounded inspection; logs can still contain private user data.

## Acceptance before calling it usable

- All 13 services start and their defined health checks pass; no restart loop, OOM or migration errors.
- Caddy HTTPS and WebSocket forwarding work, raw published ports are inaccessible from unauthorized networks, and Studio/admin/MCP do not leak publicly.
- Authenticate a disposable user with configured mail delivery; test session refresh/logout, denial without credentials and RLS isolation between two users. Revoke/remove test accounts afterward.
- Create/read/update/delete a test table row through the SDK/REST API with appropriate RLS; never use a secret/service-role key in frontend code.
- Upload/download/delete a private test object and verify unauthorized access fails, including signed URL expiry.
- Subscribe to and observe an authorized Realtime change; test denied subscriptions.
- Invoke an authenticated test Edge Function and verify unauthenticated rejection under its intended policy.
- Generate requests/errors and confirm their events are visible through Logflare/Vector in Studio Logs, with intended retention. Health checks alone do not prove ingestion.
- Restart/recreate containers and reboot the VM; verify database rows, uploaded files, functions and authentication material persist.
- Restore a consistent database + files/config backup into an isolated temporary deployment and validate it before declaring production readiness.

This is the complete self-hosted suite, not Supabase Cloud's multi-project platform, managed PITR or branching. Separate production and development stacks/data/keys/hostnames. A single Compose stack is one project.

## Backup, upgrade and recovery

Before production, configure VM-level backups plus an independent PostgreSQL backup strategy, uploaded-file backup and protected configuration/key backup. Plan retention, off-site copy, recovery point/time targets and an actual restore test. PostgreSQL logical backup must include required roles/globals and all relevant databases (including `_supabase` for platform/log data), not only the application schema; validate extension/role restore instructions for this exact version. Do not archive a live PostgreSQL data directory and call it a consistent backup.

For file/database consistency, quiesce writes for a coordinated backup or use a tested database-aware backup procedure. Proxmox replication is asynchronous and is neither a backup nor database-native HA. HA requires eligible nodes with a recoverable disk and enough RAM/CPU; do not claim zero downtime or zero lost writes.

Upgrade deliberately: preserve a verified data/config backup, review the new upstream release/migrations, update the tracked commit in `prepare.sh`, stage it into a **new** directory, review differences and overlay compatibility, resolve/review new image digests, test an isolated restore and migration, then apply during a maintenance window. Never copy template data directories over live ones. Upstream `update.sh` backs up configuration but explicitly excludes database/storage data; that is not rollback protection. A migrated database may need full restore rather than an older container image.

Preparation validation: pinned-source fetch/HEAD verification succeeded; Compose rendered 13 services with Studio Logs enabled, only Envoy LAN port 8000 published, persistent database/storage mounts and bounded local logging for every service. All 13 registry image digests resolved. ShellCheck, shell syntax, Compose validation, existing-destination refusal and example-credential startup refusal passed. No Docker containers were started. The VM and all runtime acceptance checks remain pending.

Sources: [official Docker guide](https://supabase.com/docs/guides/self-hosting/docker), [HTTPS/reverse proxy](https://supabase.com/docs/guides/self-hosting/self-hosted-proxy-https), [pinned upstream tree](https://github.com/supabase/supabase/tree/bc27d2661edd09a5d0b8d76ce33da6d4071a756e/docker).
