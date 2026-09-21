#!/usr/bin/env python3
"""Copy every current/non-current S3 object from MinIO to RustFS safely.

The source credentials are supplied only through MINIO_ACCESS_KEY and
MINIO_SECRET_KEY. Destination credentials come from the existing AWS profile.
The script never deletes source objects or buckets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


SDK_CONFIG = Config(
    retries={"max_attempts": 8, "mode": "standard"},
    s3={"addressing_style": "path"},
)
TRANSFER_CHUNK = 8 * 1024 * 1024


def client(endpoint: str, access_key: str | None = None, secret_key: str | None = None):
    kwargs = {"endpoint_url": endpoint, "config": SDK_CONFIG, "region_name": "us-east-1"}
    if access_key and secret_key:
        kwargs.update(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        return boto3.client("s3", **kwargs)
    return boto3.Session(profile_name="s3").client("s3", **kwargs)


def pages(api, operation: str, **kwargs):
    paginator = api.get_paginator(operation)
    yield from paginator.paginate(**kwargs)


def bucket_versions(source, bucket: str) -> dict[str, list[dict]]:
    versions: list[dict] = []
    for page in pages(source, "list_object_versions", Bucket=bucket):
        versions.extend(page.get("Versions", []))
    # S3 returns newer versions first. Uploading oldest first keeps the final
    # current version current on RustFS.
    grouped: dict[str, list[dict]] = defaultdict(list)
    for version in versions:
        grouped[version["Key"]].append(version)
    ordered: dict[str, list[dict]] = {}
    for key in sorted(grouped):
        ordered[key] = list(reversed(grouped[key]))
    return ordered


def inventory(api, buckets: list[str]) -> dict:
    result = {}
    for bucket in buckets:
        versions = []
        markers = []
        for page in pages(api, "list_object_versions", Bucket=bucket):
            versions.extend(page.get("Versions", []))
            markers.extend(page.get("DeleteMarkers", []))
        result[bucket] = {
            "versions": len(versions),
            "bytes": sum(item["Size"] for item in versions),
            "delete_markers": len(markers),
            "current_objects": sum(1 for item in versions if item.get("IsLatest")),
        }
    return result


def get_optional(source, operation: str, **kwargs):
    try:
        return getattr(source, operation)(**kwargs)
    except ClientError as exc:
        if exc.response["Error"].get("Code") in {"NoSuchBucketPolicy", "NoSuchLifecycleConfiguration", "NoSuchTagSet"}:
            return None
        raise


def ensure_bucket(source, destination, bucket: str):
    destination.create_bucket(Bucket=bucket)
    versioning = source.get_bucket_versioning(Bucket=bucket).get("Status")
    if versioning == "Enabled":
        destination.put_bucket_versioning(
            Bucket=bucket, VersioningConfiguration={"Status": "Enabled"}
        )
    policy = get_optional(source, "get_bucket_policy", Bucket=bucket)
    if policy:
        destination.put_bucket_policy(Bucket=bucket, Policy=policy["Policy"])
    lifecycle = get_optional(source, "get_bucket_lifecycle_configuration", Bucket=bucket)
    if lifecycle:
        destination.put_bucket_lifecycle_configuration(
            Bucket=bucket, LifecycleConfiguration={"Rules": lifecycle["Rules"]}
        )


def upload_args(response: dict, tags: list[dict]) -> dict:
    fields = {
        "Metadata": response.get("Metadata") or {},
        "ContentType": response.get("ContentType"),
        "CacheControl": response.get("CacheControl"),
        "ContentDisposition": response.get("ContentDisposition"),
        "ContentEncoding": response.get("ContentEncoding"),
        "ContentLanguage": response.get("ContentLanguage"),
        "Expires": response.get("Expires"),
        "WebsiteRedirectLocation": response.get("WebsiteRedirectLocation"),
    }
    result = {key: value for key, value in fields.items() if value is not None}
    if tags:
        result["Tagging"] = urlencode({item["Key"]: item["Value"] for item in tags})
    return result


def transfer_one(source, destination, bucket: str, item: dict, temporary_dir: Path) -> dict:
    key = item["Key"]
    version = item["VersionId"]
    source_response = source.get_object(Bucket=bucket, Key=key, VersionId=version)
    tags = get_optional(source, "get_object_tagging", Bucket=bucket, Key=key, VersionId=version)
    digest = hashlib.sha256()
    with tempfile.NamedTemporaryFile(dir=temporary_dir, delete=False) as handle:
        temporary_path = Path(handle.name)
        try:
            while chunk := source_response["Body"].read(TRANSFER_CHUNK):
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            destination.upload_file(
                str(temporary_path),
                bucket,
                key,
                ExtraArgs=upload_args(source_response, (tags or {}).get("TagSet", [])),
            )
        finally:
            source_response["Body"].close()
    try:
        copied = destination.head_object(Bucket=bucket, Key=key)
        if copied["ContentLength"] != item["Size"]:
            raise RuntimeError(f"size mismatch for s3://{bucket}/{key}")
        return {"bucket": bucket, "key": key, "bytes": item["Size"], "sha256": digest.hexdigest()}
    finally:
        temporary_path.unlink(missing_ok=True)


def transfer_key(source, destination, bucket: str, versions: list[dict], temporary_dir: Path) -> list[dict]:
    """Copy one key's history serially, preserving its current version."""
    return [
        transfer_one(source, destination, bucket, version, temporary_dir)
        for version in versions
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-endpoint", required=True)
    parser.add_argument("--destination-endpoint", required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--temporary-dir", type=Path, default=Path("/var/tmp/minio-to-rustfs"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    source_key = os.environ.get("MINIO_ACCESS_KEY")
    source_secret = os.environ.get("MINIO_SECRET_KEY")
    if not source_key or not source_secret:
        parser.error("MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required")
    if args.workers < 1:
        parser.error("--workers must be positive")

    source = client(args.source_endpoint, source_key, source_secret)
    destination = client(args.destination_endpoint)
    buckets = sorted(item["Name"] for item in source.list_buckets()["Buckets"])
    if destination.list_buckets().get("Buckets"):
        raise RuntimeError("destination RustFS is not empty; refusing to merge data")

    source_inventory = inventory(source, buckets)
    print(json.dumps({"phase": "source-inventory", "buckets": source_inventory}, sort_keys=True))
    if any(values["delete_markers"] for values in source_inventory.values()):
        raise RuntimeError("source contains delete markers; preserve them explicitly before migration")

    for bucket in buckets:
        ensure_bucket(source, destination, bucket)

    jobs = [
        (bucket, versions)
        for bucket in buckets
        for versions in bucket_versions(source, bucket).values()
    ]
    object_count = sum(len(versions) for _, versions in jobs)
    args.temporary_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    completed = 0
    copied_bytes = 0
    lock = threading.Lock()
    started = time.monotonic()
    manifest = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(transfer_key, source, destination, bucket, versions, args.temporary_dir)
            for bucket, versions in jobs
        ]
        for future in as_completed(futures):
            records = future.result()
            with lock:
                manifest.extend(records)
                completed += len(records)
                copied_bytes += sum(record["bytes"] for record in records)
                if completed % 100 == 0 or completed == object_count:
                    elapsed = max(time.monotonic() - started, 0.001)
                    rate = copied_bytes / elapsed / 1024 / 1024
                    print(
                        f"progress objects={completed}/{object_count} bytes={copied_bytes} rate_mib_s={rate:.1f}",
                        flush=True,
                    )

    destination_inventory = inventory(destination, buckets)
    if source_inventory != destination_inventory:
        raise RuntimeError(
            "destination inventory mismatch: "
            + json.dumps({"source": source_inventory, "destination": destination_inventory}, sort_keys=True)
        )
    report = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source_endpoint": args.source_endpoint,
        "destination_endpoint": args.destination_endpoint,
        "workers": args.workers,
        "inventory": destination_inventory,
        "objects_copied": len(manifest),
        "bytes_copied": copied_bytes,
        "manifest": sorted(manifest, key=lambda item: (item["bucket"], item["key"])),
    }
    args.report.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(args.report, 0o600)
    print(json.dumps({"phase": "verified", "inventory": destination_inventory}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"migration failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
