# Karakeep

Karakeep runs on the `l3b` Docker host as Portainer Stack `karakeep` (ID `80`). It is publicly available at `https://pin.l3b.cc.cd`. Pocket ID is the normal sign-in path; native Karakeep login remains as a deliberate break-glass path.

## Layout

| Purpose | Path or endpoint |
| --- | --- |
| Application SQLite data | `/data/apps/karakeep/data` |
| Meilisearch derived index | `/data/apps/karakeep/meilisearch` |
| Asset store | RustFS bucket `karakeep` at `http://rustfs:9000` |

The `karakeep` bucket was migrated from MinIO to RustFS before this application restore. The live RustFS container is on the external `l3b` network at `10.1.3.24:9000`; `rustfs:9000` resolves to it from Karakeep. The dedicated RustFS IAM identity is restricted to this bucket's listing and object read/write/delete operations; it has no access to other buckets and does not use the RustFS root credential.

Karakeep, Chrome, and Meilisearch run on the external `l3b` Docker network (`karakeep-meilisearch` and `karakeep-chrome` service names). No workload uses Docker host networking. Karakeep exposes port `3000` only on that internal network; Caddy supplies TLS and the public endpoint. Its application-native authentication is the access control layer.

## Images and thumbnails missing

Symptom: link banners, screenshots, avatars and bookmark images return `500`, and the Karakeep log shows:

```text
ENOENT: no such file or directory, open '/data/assets/<user>/<asset>/metadata.json'
GET /api/assets/<id> 500
```

Cause: the live stack had no `ASSET_STORE_S3_*` environment, so Karakeep fell back to the filesystem asset store. The local tree contained only 3 assets while the database referenced 402. The missing objects were in the RustFS `karakeep` bucket (405 asset directories), which the app was not using.

Fix, verified 2026-11-11: add the six asset-store variables to Portainer stack `80`, mapped in the `karakeep` service:

```text
ASSET_STORE_S3_ENDPOINT=http://rustfs:9000
ASSET_STORE_S3_REGION=us-east-1
ASSET_STORE_S3_BUCKET=karakeep
ASSET_STORE_S3_ACCESS_KEY_ID=<Karakeep S3 Access Key ID>
ASSET_STORE_S3_SECRET_ACCESS_KEY=<Karakeep S3 Secret Access Key>
ASSET_STORE_S3_FORCE_PATH_STYLE=true
```

The credentials are the existing bucket-scoped values in the `Karakeep` 1Password item. Redeploy stack `80` without pulling a new image. Verification: startup logs list `assetstore: - S3`; `/api/assets/<id>` returns `200` with `image/png` or `image/jpeg`; the container is healthy. Do not print the keys.

## Restore and upgrade notes

During recovery, the correct source was `/EX/RECOVERY/2026-09-15/SSD/Karakeep/data`, not the older in-container Hoarder tree. It contained the September 2026 SQLite snapshot and asset tree. The Hoarder database was a February 2025 rollback source only. The mistakenly restored live tree was removed on 2026-09-21 after the corrected source, SQLite integrity, bookmark data, and browser sign-in were verified. Both historical `/EX/RECOVERY` sources were erased when the external SSD was reformatted on 2026-09-23.

The original stack used the legacy Hoarder product name. Karakeep is its successor, so the correct SQLite data is copied intact rather than exported/imported. The legacy Alpine Chrome image is replaced with Karakeep's maintained Chrome image; this does not change application data.

The restored Meilisearch index was created by v1.16 while the supported current image is v1.41.0. If v1.41 rejects its old `data.ms` directory, recreate only the derived index by moving the current `data.ms` aside, starting Meilisearch, then running **Admin Settings → Background Jobs → Reindex All Bookmarks** in Karakeep. Back up current Karakeep data before doing so; the external recovery source no longer exists.

Portainer supplies runtime values through its protected Stack environment, which is never committed. The Compose definition explicitly maps only the required values into the relevant containers; it does not use `env_file`, because Portainer's API does not materialize that file. Karakeep session/search secrets and the bucket-scoped RustFS credential are stored in the existing `Karakeep` item in the HomeLab 1Password vault. The live stack uses `L3B_KARAKEEP_*` environment names; the tracked Compose maps them into the containers.

## Identity

Karakeep uses native OIDC with Pocket ID. The confidential client is restricted to Pocket ID group `infrastructure-admins`; its exact callback is `https://pin.l3b.cc.cd/api/auth/callback/custom`. The issuer is `https://auth.l3b.cc.cd/.well-known/openid-configuration` and scopes are `openid email profile`.

The existing account email was changed to `iam.anuragvishwakarma@gmail.com` before first OIDC sign-in. `OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true` is intentionally enabled only for this trusted first-party provider, allowing Pocket ID to attach to that existing Karakeep account rather than create a second account. The OIDC client ID and secret are stored as fields in the existing `HomeLab` → `Karakeep` item; do not create a duplicate credential item. Native password login is not disabled and is the break-glass method.

## Operations

Use Portainer to redeploy Stack `80`; change this tracked Compose definition before updating the stack. Do not enable automatic image updaters. A planned update requires release review, a copy of `/data/apps/karakeep/data`, and a fresh browser check.
# Hermes CLI and search credential mapping

As of 2026-10-03, Hermes on dev uses the official CLI 0.33.2 and a dedicated scoped API key saved in HomeLab → Karakeep → Hermes API Key. See [the Hermes runbook](../hermes/README.md#karakeep-cli-integration-2026-10-03) for protected configuration, scopes and validation.

Both the app and Meilisearch services must receive the same `MEILI_MASTER_KEY` from Portainer stack environment variables. The missing app mapping caused `missing_authorization_header` search failures; it was corrected through stack 80 without changing secrets or resetting data. Bookmark indexing and full-text/tag search passed after the correction.

## Meilisearch restart loop after power loss (2026-11-09)

Symptom: `karakeep-meilisearch` restarting continuously; the log repeats
`Meilisearch (v1.56.1) failed to infer the version of the database`, and
Karakeep search is unavailable.

Cause: `data.ms/VERSION` had been truncated to **0 bytes** (root:root, mtime
09:28, matching a hard power-off during the host power-fault investigation).
The LMDB stores and both indexes were intact - only the version marker was lost.

Fix, verified 2026-11-09 11:45:

```sh
printf '1.56.1' | sudo tee /data/apps/karakeep/meilisearch/data.ms/VERSION >/dev/null
sudo chown 1000:1000 /data/apps/karakeep/meilisearch/data.ms/VERSION
sudo chmod 600 /data/apps/karakeep/meilisearch/data.ms/VERSION
docker restart karakeep-meilisearch
```

The value must match the running image (`getmeili/meilisearch:v1.56.1`). The
pre-upgrade archive in `/BACKUP/preupgrade-20261107-2318/karakeep-meilisearch.tgz`
confirms the format: a bare version string, no trailing newline (it holds
`1.41.0`, the version Karakeep migrated from on 2026-11-07). The truncated
original is kept as `meilisearch/VERSION.corrupt-20261109`.

Verification: `/health` returns `available`; indexes `bookmarks` and
`bookmarks_vectors` present; 11 documents; a live `POST /indexes/bookmarks/search`
returns hits; the Karakeep indexing worker logs no errors.

Do **not** delete `data.ms` for this symptom - it is only the version marker.
Wiping the index remains the fallback for genuine LMDB corruption, followed by
Karakeep's *Reindex All Bookmarks*.
