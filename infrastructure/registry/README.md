# Docker Registry

Future work: [minimal Go-based Registry UI](UI-PLAN.md), recorded2026-10-22.
This is a plan only; no UI has been built or deployed. Existing API behavior was
verified read-only, with limitations and security boundaries recorded there.

The Docker Registry runs on `ctr` as Portainer stack `registry` and stores image layers in the migrated RustFS bucket `docker-registry`, under the immutable legacy prefix `/registry`. Its Docker client endpoint is public at `https://registry.l3b.cc.cd`; access still requires the retained Registry `htpasswd` credentials.

Registry uses its default in-memory metadata cache; a separate Redis cache is unnecessary for this single-instance deployment. Only Registry port `5000` is bound to `10.1.1.4`, where Caddy terminates TLS. Caddy deliberately does not use response compression or the private/OIDC policy on this route: Docker clients authenticate with Registry's own HTTP Basic credentials and transfer signed layer data without interference.

## Data and credentials

Recovery copied the preserved `htpasswd` file from the former `/EX` source to `/data/apps/registry`. The external source was erased when the SSD was reformatted on 2026-09-23. Image blobs remain in RustFS, so no object data was copied locally.

The RustFS application identity is restricted to the `docker-registry` bucket and `registry/*` object prefix. Its access key and secret, together with the retained Docker client credentials and Stack runtime secrets, belong in the existing `HomeLab` 1Password item **Docker Private Registry**. Never reuse the RustFS root or `s3-admin` credentials.

## Operations

The Compose file and environment template are tracked here. Portainer supplies the real stack environment; do not commit it.

```bash
curl -i https://registry.l3b.cc.cd/v2/
docker login registry.l3b.cc.cd
docker pull registry.l3b.cc.cd/<repository>:<tag>
```

The unauthenticated `/v2/` response must be `401` and include `Docker-Distribution-Api-Version: registry/2.0`. A valid Docker login must succeed before pushing or pulling.

## Custom images in the registry, 8 November 2026

The registry stores blobs in RustFS S3 (bucket `docker-registry`, endpoint
`http://rustfs:9000`, `rootdirectory: /registry`), so images survive a registry
container rebuild and ride along with RustFS data. Authentication is htpasswd;
the username/password and the RustFS keys are in 1Password (`Docker Private
Registry`, `RustFS - S3`).

Push flow for a locally built image:

```bash
docker login registry.l3b.cc.cd          # credentials from 1Password
docker tag localdesk:1 registry.l3b.cc.cd/localdesk:1
docker push registry.l3b.cc.cd/localdesk:1
```

The first push of the desktop image uploaded the whole 3 GB image. Docker stores
the login in `~/.docker/config.json`, so later pushes need no password prompt.
Verified after the push: `/v2/localdesk/tags/list` shows `1`, the manifest is an
OCI index with an amd64 image plus attestation, a pull reports "up to date", and
`docker-registry/registry/docker/registry/v2/blobs/...` objects exist in RustFS.

The registry route is reachable over HTTPS at `registry.l3b.cc.cd` and relies on
the registry's own basic auth, not Tinyauth (Docker cannot complete an OAuth
redirect).
