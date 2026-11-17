# Cairn

Cairn runs as the Docker container `cairn` from the Portainer stack `cairn` (ID 176, [stack file](../l3b/cairn.compose.yaml)) on the single Debian Docker host. It is a pinned CalVer image, `ghcr.io/harsh-2002/cairn:v2026.11.16`, on the `l3b` bridge network, running as `1000:1000`. It publishes no host ports. (It was a native LXC install on the retired `s3` host before the move to Docker; that layout no longer exists.)

## Topology

| Service | Listener (on `l3b`) | URL | Exposure |
| --- | --- | --- | --- |
| Cairn S3/API | `cairn:7373` | `https://cairn-s3.l3b.cc.cd` | Public through Caddy (`import public`); S3 auth and bucket policies apply |
| Cairn console | `cairn:7374` | `https://cairn.l3b.cc.cd` | Caddy without the public route; keep it LAN/Tailscale only |
| RustFS (separate container, 1.0.4) | `rustfs` | `https://s3.l3b.cc.cd` | LAN/Tailscale only |

Caddy terminates TLS. Cairn trusts only the Docker network (`CAIRN_TRUSTED_PROXIES=10.1.3.0/24`) as its reverse proxy, which is what makes it treat forwarded requests as HTTPS (cookie `Secure`, HSTS).

Public API clients must use valid S3 credentials. A new bucket has no anonymous-read policy (an unauthenticated GET returned 403 on 2026-11-16); add one deliberately if an object must be public.

## State and secrets

- Data, staging tree and SQLite database: `/data/apps/cairn` (bind-mounted at `/data/cairn`), database `cairn.db`. The database, staging tree and object blobs must stay on the same filesystem because the durability protocol relies on atomic rename.
- Environment file: `/data/apps/cairn/runtime.env` (mode `0600`): `CAIRN_ROOT_ACCESS_KEY`, `CAIRN_ROOT_SECRET_KEY`, `CAIRN_MASTER_KEY`, plus addresses, public URLs, `CAIRN_TRUSTED_PROXIES` and `CAIRN_LOG_FORMAT=json`. Never print it.
- The canonical `Cairn S3` item in the `HomeLab` 1Password vault holds the root keys and master key. Do not change or lose the master key once data or sealed credentials exist.
- Content today: one bucket, `artifact` (used by Quick Share), and two users.

## Validation

```bash
docker ps --filter name=^cairn$                      # healthy, expected image tag
docker exec cairn /usr/local/bin/cairn --version
IP=$(docker inspect cairn --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
curl -fsS http://$IP:7373/healthz; curl -fsS http://$IP:7373/readyz
curl -fsS https://cairn-s3.l3b.cc.cd/readyz           # through Caddy
docker logs cairn 2>&1 | grep -i 'migration\|error'   # migration complete, no errors
```

An authenticated S3 round trip (create a temporary bucket, upload, download, compare, delete everything including versions and delete markers) reads the keys from `runtime.env` inside a subshell and exports them only for the AWS CLI; never echo them. Also check the console sign-in with the public console origin and a Quick Share (`qs`) upload and download.

## Upgrade

Releases are calendar-versioned and the release workflow retires older releases, so the image is pinned and upgrades are manual (Watchtower only refreshes the same tag). Read the release notes and the upgrade/rollback guide first. **Schema migrations are one-way**: a newer database is refused by the older binary, so keep a cold copy first.

1. Stop the container and copy the whole data directory (root-only destination; `/data/apps` is not writable by `dev`):
   `docker stop cairn && sudo cp -a /data/apps/cairn /BACKUP/cairn-preupgrade-YYYYMMDD && sudo chmod 700 /BACKUP/cairn-preupgrade-YYYYMMDD`, then compare checksums of the two trees. The copy contains `runtime.env`, so it is secret material.
2. Redeploy the stack through Portainer with the helper (needs the temporary API key from 1Password; delete `~/.cache/ptn` afterwards):
   `python3 infrastructure/portainer/stack-update.py 176 --sub "cairn:OLD=cairn:NEW"`, and set the same tag in `infrastructure/l3b/cairn.compose.yaml`.
3. Confirm the migration log, `/readyz`, the S3 round trip, console sign-in and Quick Share, then remove the temporary helper files.

### History

- **2026-11-16: `v2026.09.13` to `v2026.11.16`.** A cold copy of the data directory was taken first and removed on 2026-11-17 at the owner's request after 13 hours of clean running, so there is no rollback path to `v2026.09.13`: its binary refuses the migrated database. Schema 39 to 45 applied in 9 ms on a 557 KB database; integrity check ok, no foreign-key violations, protocol 3, bucket and both users unchanged. Verified: byte-exact PUT/GET and 12 MiB multipart, `?partNumber`, tagging, versioning with delete markers and listing counts, presigned URL, anonymous GET denied (403), public `healthz`/`readyz`, console sign-in with `Secure; HttpOnly; SameSite=Strict` cookie and foreign-origin refusal, the new security headers, and a Quick Share upload and download. The previous image `v2026.09.13` was still present locally and in GHCR at that time.
- **2026-11-02: restored `v2026.09.13`** into this container from the former deployment, with its bucket and users (verified by a Quick Share round trip).

References: [Cairn documentation](https://harsh-2002.github.io/Cairn/), [operations guide](https://github.com/Harsh-2002/Cairn/blob/main/docs/operations.md), [upgrade/rollback guide](https://github.com/Harsh-2002/Cairn/blob/main/docs/upgrade-rollback.md).
