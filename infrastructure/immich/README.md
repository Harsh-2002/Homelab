# Immich

Immich runs as a pinned Docker Compose deployment on VM 204 `ctr` and is available at `https://photos.l3b.cc.cd`.

## Storage and access

| Purpose | Path |
| --- | --- |
| Compose and live environment | `/data/apps/immich` |
| Uploaded assets, thumbnails, encoded video, profiles, and backups | `/data/immich/media` |
| Machine-learning models | `/data/immich/model` |
| PostgreSQL 14 data | `/data/immich/postgres` |

The service binds only to VM 204's LAN address at `10.1.1.4:2283`. Caddy provides the TLS endpoint and restricts it to the LAN and Tailscale networks. Immich retains its own native authentication so web and mobile clients work normally; Tinyauth is deliberately not placed in front of its API.

`immich-server` uses the passed-through Intel UHD 630 render device and Quick Sync (`qsv`) for video transcoding. Machine learning uses OpenVINO on CPU, matching the preserved deployment.

## Recovery contract

The recovered database was created by Immich `v3.1.0` with PostgreSQL 14 and the pinned VectorChord image in `compose.yaml`. Restore and validate that exact version before considering an upgrade. Immich does not support downgrades; read release notes and take a fresh backup before changing `IMMICH_VERSION`.

The live `.env` is copied from the preserved source only during recovery, owned by `root`, and mode `0600`. It contains the preserved database password and is never committed. `.env.example` is illustrative only.

## Operations

```bash
cd /data/apps/immich
sudo docker compose config --quiet
sudo docker compose pull
sudo docker compose up -d
sudo docker compose ps
```

Validate the server locally and through Caddy:

```bash
curl --fail --silent --show-error http://10.1.1.4:2283/api/server/ping
curl --resolve photos.l3b.cc.cd:443:10.1.1.3 https://photos.l3b.cc.cd/api/server/ping
```

Do not use automatic image-updaters for Immich. Upgrades are deliberate, reviewed operations because they can include database migrations.
