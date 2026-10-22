# Minimal Registry UI: future plan

Status: planned, not built or deployed. Recorded at the owner's request on
2026-10-22. No hostname or implementation repository has been selected.

## Goal and stack

Build a small, polished UI over the existing registry, without replacing it.
Preferred implementation: Go standard-library HTTP backend, HTML templates,
CSS and small JavaScript interactions. Embed static assets in the Go binary.
One process/container, no database, Redis, Docker socket or separate frontend
runtime. Short-lived bounded in-memory metadata caching is optional.

Reuse existing Caddy for HTTPS and Pocket ID/Tinyauth for private UI access.
Keep Docker's public `registry.l3b.cc.cd/v2/` route and native Basic auth intact.
Store upstream credentials server-side, sourced from the existing HomeLab vault
item Docker Private Registry. Never embed credentials in browser assets or logs.
The UI's backend also avoids the registry's current lack of CORS headers.

## Verified existing API

Read-only inspection on2026-10-22 found Distribution2.8.3 (`registry:2`), S3
storage in RustFS bucket docker-registry, prefix /registry, htpasswd auth and
delete-enabled configuration. Catalog contained five repositories at inspection.
Unauthenticated API401 and authenticated200 were verified.

- GET /v2/_catalog, with pagination and Link header.
- GET /v2/{repository}/tags/list.
- GET/HEAD /v2/{repository}/manifests/{tag-or-digest}.
- GET image-config blobs and HEAD layer blobs under /v2/{repository}/blobs/{digest}.
- Sample OCI index, platform manifest, OS/architecture, creation timestamp and
  compressed layer sizes successfully read. Attestation descriptors such as
  unknown/unknown must not be presented as runnable CPU architectures.

Push/upload endpoints exist in the specification but were not mutation-tested.
Deletion is enabled, not destructively tested. Distribution2.8.3 manifest delete
requires a digest; there is no simple independent tag-delete/rename API.

## Initial scope

Repository list and search, paginated tag browsing, image/platform details,
digest and creation time, compressed image-size estimate, copy-pull commands,
clear loading/empty/error/authentication states. Responsive, minimal interface.

Start read-only. Explicitly allowlist backend operations; do not expose a generic
authenticated registry proxy. Registry Basic auth is not UI role-based access
control. Reuse the trusted identity boundary and deliberately authorize writes
if destructive capabilities are added later. Restrict registry origin to the
configured upstream, validate repository/reference paths and preserve TLS checks.

## Later capabilities and limitations

- Guarded manifest deletion with confirmation and affected-tag disclosure.
- Deleting a digest can affect multiple tags referencing it. Do not offer an
  unsafe Delete tag button that silently deletes a shared manifest.
- Layer sums are estimates, not deduplicated bucket usage or reclaimable space.
- Image creation time is not registry push time. Standard API has no pull counts,
  vulnerability scanner, running-container status or user-management API.
- Storage reclamation requires separate controlled garbage collection, with
  registry writes stopped/read-only as upstream requires. No always-on online
  delete-all/GC button or storage admin credentials in the UI.
- Do not expose arbitrary image-config environment values as harmless metadata;
  images may accidentally contain secrets. Prefer a bounded allowlist of fields.

## Future deployment and acceptance

Use reproducible Docker Compose through the existing Portainer workflow, standard
docker-compose.yaml, runtime secrets outside Git, non-root container and bounded
resources/logging. Protect UI access; don't alter public Docker client auth.
Validate pagination, schema2/OCI/index handling, inaccessible/stale references,
backend timeout/auth errors, browser credential non-disclosure, CORS independence,
desktop/mobile usability and any eventual destructive operation separately.

No build/deployment is authorized merely by recording this plan. Reverify the
registry version and API behavior when implementation starts.

Sources: https://distribution.github.io/distribution/spec/api/,
https://distribution.github.io/distribution/about/garbage-collection/,
https://pkg.go.dev/net/http, https://pkg.go.dev/html/template, https://pkg.go.dev/embed.
