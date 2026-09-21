# MinIO retirement record

MinIO was retired on 2026-09-21 after migration to native RustFS. The active S3 API is now `https://s3.l3b.cc.cd` and the OIDC console is `https://rustfs.l3b.cc.cd`.

The migration copied all ten buckets, 4,224 object versions, and `13,836,594,670` bytes. The source and RustFS inventories matched after transfer and during a final post-copy delta check. The versioned `artifact` bucket retained all 371 versions, and its bucket policy matched byte-for-byte.

The Portainer `minio` Stack (ID `111`), Caddy routes, local working directory `/data/minio`, container image, and MinIO-specific runtime secrets were removed only after validation. The original read-only recovery source remains at `/EX/RECOVERY/2026-09-15/SSD/Minio`; it is not a live service data path.

The reusable, non-secret migration utility is tracked at `scripts/migrate-minio-to-rustfs.py`; it requires Python `boto3`, source credentials supplied through the environment, and the existing RustFS AWS CLI profile. Do not recreate a MinIO deployment without a separate reviewed decision.
