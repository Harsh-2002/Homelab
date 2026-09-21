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

The service binds only to VM 204's LAN address at `10.1.1.4:2283`. Caddy provides the TLS endpoint and restricts it to the LAN and Tailscale networks. Immich retains its own native authentication so web and mobile clients work normally; Tinyauth is deliberately not placed in front of its API.

`immich-server` uses the passed-through Intel UHD 630 render device and Quick Sync (`qsv`) for video transcoding. Machine learning uses OpenVINO on CPU, matching the preserved deployment.

## Recovery contract

The recovered database was created by Immich `v3.1.0` and was upgraded to `v3.2.2` after a protected pre-upgrade PostgreSQL dump. It uses PostgreSQL 14 with the pinned VectorChord image in `compose.yaml`. Immich does not support downgrades; read release notes and take a fresh backup before changing `IMMICH_VERSION`.

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
