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
