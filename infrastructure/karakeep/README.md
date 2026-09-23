# Karakeep

Karakeep is restored on Docker VM 204 `ctr` as Portainer Stack `karakeep` (ID `80`). It is publicly available at `https://pin.l3b.cc.cd`. Pocket ID is the normal sign-in path; native Karakeep login remains as a deliberate break-glass path.

## Layout

| Purpose | Path or endpoint |
| --- | --- |
| Application SQLite data | `/data/apps/karakeep/data` |
| Meilisearch derived index | `/data/apps/karakeep/meilisearch` |
| Asset store | RustFS bucket `karakeep` at `http://10.1.1.8:9000` |

The `karakeep` bucket was migrated from MinIO to RustFS before this application restore. The dedicated RustFS IAM identity is restricted to this bucket's listing and object read/write/delete operations; it has no access to other buckets and does not use the RustFS root credential.

Karakeep, Chrome, and Meilisearch run on the Compose-created `karakeep_default` bridge network. No workload uses Docker host networking. Karakeep binds its web port only to `10.1.1.4:3000`; Caddy supplies TLS and the public endpoint. Its application-native authentication is the access control layer.

## Restore and upgrade notes

During recovery, the correct source was `/EX/RECOVERY/2026-09-15/SSD/Karakeep/data`, not the older in-container Hoarder tree. It contained the September 2026 SQLite snapshot and asset tree. The Hoarder database was a February 2025 rollback source only. The mistakenly restored live tree was removed on 2026-09-21 after the corrected source, SQLite integrity, bookmark data, and browser sign-in were verified. Both historical `/EX/RECOVERY` sources were erased when the external SSD was reformatted on 2026-09-23.

The original stack used the legacy Hoarder product name. Karakeep is its successor, so the correct SQLite data is copied intact rather than exported/imported. The legacy Alpine Chrome image is replaced with Karakeep's maintained Chrome image; this does not change application data.

The restored Meilisearch index was created by v1.16 while the supported current image is v1.41.0. If v1.41 rejects its old `data.ms` directory, recreate only the derived index by moving the current `data.ms` aside, starting Meilisearch, then running **Admin Settings → Background Jobs → Reindex All Bookmarks** in Karakeep. Back up current Karakeep data before doing so; the external recovery source no longer exists.

Portainer supplies runtime values through its protected Stack environment, which is never committed. The Compose definition explicitly maps only the required values into the relevant containers; it does not use `env_file`, because Portainer's API does not materialize that file. Karakeep session/search secrets and the bucket-scoped RustFS credential are stored in the existing `Karakeep` item in the HomeLab 1Password vault.

## Identity

Karakeep uses native OIDC with Pocket ID. The confidential client is restricted to Pocket ID group `infrastructure-admins`; its exact callback is `https://pin.l3b.cc.cd/api/auth/callback/custom`. The issuer is `https://auth.l3b.cc.cd/.well-known/openid-configuration` and scopes are `openid email profile`.

The existing account email was changed to `iam.anuragvishwakarma@gmail.com` before first OIDC sign-in. `OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true` is intentionally enabled only for this trusted first-party provider, allowing Pocket ID to attach to that existing Karakeep account rather than create a second account. The OIDC client ID and secret are stored as fields in the existing `HomeLab` → `Karakeep` item; do not create a duplicate credential item. Native password login is not disabled and is the break-glass method.

## Operations

Use Portainer to redeploy Stack `80`; change this tracked Compose definition before updating the stack. Do not enable automatic image updaters. A planned update requires release review, a copy of `/data/apps/karakeep/data`, and a fresh browser check.
