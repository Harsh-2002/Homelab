# MinIO

MinIO is a Komodo-managed Docker Compose Stack on VM 204 `ctr`. Its preserved object data and MinIO metadata are restored into `/data/minio`; Komodo owns the runtime Compose file and its local `.env` in the configured Stack directory.

## Endpoints

| Purpose | Address | Upstream |
| --- | --- | --- |
| S3 API | `https://minio.l3b.cc.cd` | `10.1.1.4:9000` |
| MinIO Console | `https://minio-console.l3b.cc.cd` | `10.1.1.4:9001` |

Both endpoints are private to LAN and Tailscale at Caddy. MinIO has native authentication, so it does not use Tinyauth. The console redirect URL is fixed to its external Caddy hostname so console WebSocket origin checks succeed.

## Komodo Stack

Create a Stack named `minio` on the existing `ctr` server, sourced from Git: repository `Harsh-2002/Homelab`, branch `main`, and file path `infrastructure/minio/compose.yaml`. Enable normal Compose health checks, keep automatic image updates disabled, and use the default Stack project name `minio`. This keeps Git as the Compose source of truth instead of maintaining a second editable UI copy.

In **Stack → Config → Environment**, create these four values. They are written only to Komodo's Stack `.env`, are not stored in Git, and should also be saved in the existing HomeLab 1Password item.

| Variable | Guidance |
| --- | --- |
| `MINIO_ROOT_USER` | Unique random root access key; do not use `minioadmin`. |
| `MINIO_ROOT_PASSWORD` | Long random root secret. |
| `CONSOLE_PBKDF_PASSPHRASE` | At least 32 random characters; retain indefinitely. |
| `CONSOLE_PBKDF_SALT` | At least 48 random characters; retain indefinitely. |

The last two values are required by the bundled console image and must not rotate between restarts. After the Stack reports healthy, use the root account only to create limited MinIO users or service accounts for applications.

## Recovery contract

The recovery source is `/EX/RECOVERY/2026-09-15/SSD/Minio`. `/EX` is mounted read-only; only `/data/minio` is a working copy. The original requested image tag was resolved on 2026-09-21 and pinned in `compose.yaml` to digest `sha256:94c7aba0dbacd0ad6ddd2d50a86a4bab3c86b2e29926234359fb42c1429e35a6`. Do not change it automatically: validate a data backup and release compatibility before a deliberate MinIO upgrade.
