# Docker Registry

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
