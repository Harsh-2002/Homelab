# MinIO

MinIO is a Docker Compose workload on VM 204 `ctr`, managed through Portainer when it is restored. Its preserved object data and MinIO metadata are restored into `/data/minio`; the Compose definition in this repository remains the source of truth.

## Endpoints

| Purpose | Address | Upstream |
| --- | --- | --- |
| S3 API | `https://minio.l3b.cc.cd` | `10.1.1.4:9000` |
| MinIO Console | `https://minio-console.l3b.cc.cd` | `10.1.1.4:9001` |

Both endpoints are private to LAN and Tailscale at Caddy. MinIO has native authentication, so it does not use Tinyauth. The console redirect URL is fixed to its external Caddy hostname so console WebSocket origin checks succeed.

## Portainer stack

Create a Stack named `minio` on the existing `ctr` server from the tracked `infrastructure/minio/compose.yaml` definition. Use the default Stack project name `minio`, enable its normal Compose health checks, and keep automatic image updates disabled. Keep the repository definition authoritative instead of maintaining a second editable UI copy.

In the stack environment, create these four values. They are written only to the runtime `.env`, are not stored in Git, and should also be saved in the existing HomeLab 1Password item.

| Variable | Guidance |
| --- | --- |
| `MINIO_ROOT_USER` | Unique random root access key; do not use `minioadmin`. |
| `MINIO_ROOT_PASSWORD` | Long random root secret. |
| `CONSOLE_PBKDF_PASSPHRASE` | At least 32 random characters; retain indefinitely. |
| `CONSOLE_PBKDF_SALT` | At least 48 random characters; retain indefinitely. |

The last two values are required by the bundled console image and must not rotate between restarts. After the Stack reports healthy, use the root account only to create limited MinIO users or service accounts for applications.

## Recovery contract

The recovery source is `/EX/RECOVERY/2026-09-15/SSD/Minio`. `/EX` is mounted read-only; only `/data/minio` is a working copy. The original requested image tag was resolved on 2026-09-21 and pinned in `compose.yaml` to digest `sha256:94c7aba0dbacd0ad6ddd2d50a86a4bab3c86b2e29926234359fb42c1429e35a6`. Do not change it automatically: validate a data backup and release compatibility before a deliberate MinIO upgrade.
