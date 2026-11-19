# Immich

Immich runs on VM 204 `ctr` as the Portainer Stack `immich` (ID `147`) on the `Aether` endpoint. It is available at `https://photos.l3b.cc.cd`.

## Storage and access

| Purpose | Path |
| --- | --- |
| Portainer Stack state and runtime environment | `/data/portainer/compose/147/` |
| Preserved recovery environment source | `/data/apps/immich/.env` |
| Uploaded assets, thumbnails, encoded video, profiles, and backups | `/data/immich/media` |
| Machine-learning models | `/data/immich/model` |
| PostgreSQL 14 data | `/data/immich/postgres` |

The service binds only to VM 204's LAN address at `10.1.1.4:2283`. Caddy provides the TLS endpoint. `photos.l3b.cc.cd` is an intentional public, DNS-only exception with native Immich authentication; Tinyauth is deliberately not placed in front of its API so browser and mobile clients work normally.

`immich-server` uses the passed-through Intel UHD 630 render device and Quick Sync (`qsv`) for video transcoding. Machine learning uses OpenVINO on CPU, matching the preserved deployment.

## Recovery contract

The recovered database was created by Immich `v3.1.0` and was upgraded to `v3.2.2` after a protected pre-upgrade PostgreSQL dump at `/data/immich/backups/immich-pre-v3.2.2-20260921T173432Z.sql.gz` (mode `0600`). It uses PostgreSQL 14 with the pinned VectorChord image and Valkey 9 cache image in `compose.yaml`. The upgrade completed with all containers healthy, Caddy returning the native login page, and a real Quick Sync encode passing. Immich does not support downgrades; read release notes and take a fresh backup before changing `IMMICH_VERSION`.

The preserved `.env` is owned by `root`, mode `0600`, and contains the recovered database password. Its values are entered into the Portainer Stack environment during recovery and are never committed. Portainer owns the running Stack; do not run a separate `docker compose up` from `/data/apps/immich`. `.env.example` is illustrative only.

## Operations

Use Portainer to inspect, redeploy, or stop the `immich` Stack. Update the tracked `compose.yaml` first, then redeploy that same definition through the Stack; do not edit an independent Compose file on `ctr`.

For a read-only host check:

```bash
ssh ctr 'sudo docker ps --filter name=immich --format "table {{.Names}}\t{{.Status}}"'
```

Validate the server locally and through Caddy:

```bash
curl --fail --silent --show-error http://10.1.1.4:2283/api/server/ping
curl --resolve photos.l3b.cc.cd:443:10.1.1.3 https://photos.l3b.cc.cd/api/server/ping
```

Do not use automatic image-updaters for Immich. Upgrades are deliberate, reviewed operations because they can include database migrations.

## Identity

Immich uses native Pocket ID OIDC. The dedicated confidential `immich` client is restricted to the `infrastructure-admins` group and uses issuer `https://auth.l3b.cc.cd`, scope `openid email profile`, `RS256` ID tokens, and `client_secret_post` token authentication. It permits exactly these redirect URIs:

- `https://photos.l3b.cc.cd/auth/login`
- `https://photos.l3b.cc.cd/user-settings`
- `app.immich:///oauth-callback`

The mobile callback is required for the official iOS and Android applications. Pocket ID's backchannel-logout callback is `https://photos.l3b.cc.cd/api/oauth/backchannel-logout`.

The existing Immich account was explicitly linked through **User Settings → OAuth** before normal OIDC use. It matches Pocket ID's verified email `iam.anuragvishwakarma@gmail.com`, so the library remains under the same user rather than a new account. Auto-registration and auto-launch are both disabled. Native password login remains enabled as a deliberate break-glass path. The current OIDC client ID and secret are fields in the existing `HomeLab` → `Immich Photos` 1Password item; no separate or duplicate vault item exists.

## 2026-11-03 backups marker

Redeploying the stack (to add Watchtower labels) recreated `immich` and exposed
a latent gap: `/data/apps/immich/media/backups` did not exist, so the server's
system-integrity check failed with

```text
Failed to read (/data/backups/.immich): ENOENT
microservices worker exited with code 1
```

and the container entered a restart loop while `photos.l3b.cc.cd` returned 502.
Immich requires a `.immich` marker file in every media subfolder. The five other
folders already had one; `backups` had never been created. Fixed with:

```sh
sudo install -d -o 1000 -g 1000 -m 755 /data/apps/immich/media/backups
sudo install -o 1000 -g 1000 -m 644 /dev/null /data/apps/immich/media/backups/.immich
```

The container then started healthy and the site returned 200. Keep the folder in
any future restore; it is not created automatically on an existing media tree.

## 2026-11-04 ONNX Runtime telemetry disabled

Immich Machine Learning runs ONNX Runtime, whose **telemetry is on by default**
in the upstream Docker build and reports to
`mobile.events.data.microsoft.com`. AdGuard's query log proved it here: 46
resolutions of that host from `10.1.3.1` (the Docker gateway) in one day, plus
older entries for `v10.events.data.microsoft.com`.

Two independent controls were applied:

1. `ORT_DISABLE_TELEMETRY: "1"` in the `immich-ml` service environment
   (Portainer stack 147 and the tracked Compose file).
2. AdGuard user rules, so the endpoint fails even if a future image forgets the
   variable:

   ```text
   ||mobile.events.data.microsoft.com^
   ||v10.events.data.microsoft.com^
   ||self.events.data.microsoft.com^
   ```

Verified after the change: `dig mobile.events.data.microsoft.com @10.1.1.10`
returns `0.0.0.0`, a container resolves it to `::`, and the container reports
`ORT_DISABLE_TELEMETRY=1`. Note that `10.1.1.1` is the **router**, not AdGuard —
testing against it bypasses the homelab filters entirely; the resolver is
`10.1.1.10`.

## Upgrade to v3.4.2, 19 November 2026

Upgraded v3.3.6 -> v3.4.2 (crossing 3.4.0). Release notes: 3.4.0 adds workflow filters and
triggers, JPEG XL, many security fixes and a CSP change (no `unsafe-inline`); 3.4.1 and 3.4.2
are bug fixes (3.4.1 also bundles FUTO Backups 1.16.0). No manual migration steps were listed.

Procedure used (Immich cannot be downgraded): `pg_dump` of the `immich` database
(`docker exec immich-postgres pg_dump -U postgres -d immich`, gzip, root-only mode 0600,
integrity-checked, 73 tables), pre-pulled both images, then
`infrastructure/portainer/stack-update.py 147 --sub 'immich-server:v3.3.6=immich-server:v3.4.2'
--sub 'immich-machine-learning:v3.3.6=immich-machine-learning:v3.4.2'
--env L3B_IMMICH_IMMICH_VERSION=v3.4.2`.

Verified: all four containers healthy, server and `photos.l3b.cc.cd` report 3.4.2 and return
200, migrations ran with no error, row counts equal the pre-upgrade dump (9,594 assets, 2 users),
media folders and the `backups/.immich` marker intact, `/dev/dri/renderD128` still mapped. The new
FUTO Backups ("Yucca") state generated a master key under `/data/backups/yucca` on first start;
it is a log WARN, not an error. Not tested: an actual upload, a video encode with Quick Sync,
OIDC login, or the mobile app.

**The live Portainer stack pins the image tags in its compose text** and has the `L3B_IMMICH_*`
variables, so it differs from the tracked `compose.yaml` (which uses `${IMMICH_VERSION}`). Bump
the tags in the live stack. The paths in the older sections above (`/data/immich/...`, VM 204)
are from the retired layout; the host paths are `/data/apps/immich/{media,postgres}`.
