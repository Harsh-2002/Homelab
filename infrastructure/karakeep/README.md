# Karakeep

Karakeep is restored on Docker VM 204 `ctr` as Portainer Stack `karakeep` (ID `80`). It is publicly available at `https://pin.l3b.cc.cd` and retains native Karakeep login during the recovery phase.

## Layout

| Purpose | Path or endpoint |
| --- | --- |
| Application SQLite data | `/data/apps/karakeep/data` |
| Meilisearch derived index | `/data/apps/karakeep/meilisearch` |
| Asset store | RustFS bucket `karakeep` at `http://10.1.1.8:9000` |
| Restored source | `/EX/RECOVERY/2026-09-15/SSD/Karakeep/data` |
| Preserved legacy rollback source | `/EX/RECOVERY/2026-09-15/rootfs/opt/SRVR/Hoarder` |

The `karakeep` bucket was migrated from MinIO to RustFS before this application restore. The dedicated RustFS IAM identity is restricted to this bucket's listing and object read/write/delete operations; it has no access to other buckets and does not use the RustFS root credential.

Karakeep, Chrome, and Meilisearch run on the Compose-created `karakeep_default` bridge network. No workload uses Docker host networking. Karakeep binds its web port only to `10.1.1.4:3000`; Caddy supplies TLS and the public endpoint. Its application-native authentication is the access control layer.

## Restore and upgrade notes

The correct Portainer-mounted data source is `/EX/RECOVERY/2026-09-15/SSD/Karakeep/data`, not the older in-container Hoarder tree. It contains the current September 2026 SQLite snapshot and asset tree. The Hoarder database is a February 2025 rollback source only. Before the corrected restore, the mistaken live directory was preserved at `/data/apps/karakeep/data.pre-ssd-restore-20260921T211944Z`; do not remove it without an explicit retention decision.

The original stack used the legacy Hoarder product name. Karakeep is its successor, so the correct SQLite data is copied intact rather than exported/imported. The legacy Alpine Chrome image is replaced with Karakeep's maintained Chrome image; this does not change application data.

The preserved Meilisearch index was created by v1.16 while the supported current image is v1.41.0. The recovery copy is retained first. If v1.41 rejects its old `data.ms` directory, retain the original and recreate only the derived index by moving the copied `data.ms` aside, starting Meilisearch, then running **Admin Settings → Background Jobs → Reindex All Bookmarks** in Karakeep. Do not delete the preserved recovery source.

Portainer supplies runtime values through its protected Stack environment, which is never committed. The Compose definition explicitly maps only the required values into the relevant containers; it does not use `env_file`, because Portainer's API does not materialize that file. Karakeep session/search secrets and the bucket-scoped RustFS credential are stored in the existing `Karakeep` item in the HomeLab 1Password vault.

## Operations

Use Portainer to redeploy Stack `80`; change this tracked Compose definition before updating the stack. Do not enable automatic image updaters. A planned update requires release review, a copy of `/data/apps/karakeep/data`, and a fresh browser check.
