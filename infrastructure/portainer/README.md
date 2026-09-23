# Portainer

Portainer EE runs as a Docker Compose service on VM 204 `ctr`, with restored state in `/data/portainer` and its Compose files in `/data/apps/portainer`. It is served privately at `https://portainer.l3b.cc.cd` by Caddy; Portainer retains its own login rather than using a Caddy authentication layer.

## Identity

Portainer uses native Custom OAuth/OIDC with Pocket ID. The provider client ID is `portainer`, its callback and redirect URL are exactly `https://portainer.l3b.cc.cd/`, and automatic user provisioning is enabled. The client secret is stored only in the `Pocket ID OIDC - portainer` API Credential item in the `HomeLab` 1Password vault; it is never committed.

Pocket ID is the normal sign-in path. The restored local Portainer administrator remains deliberately available as the break-glass fallback, so **Hide internal authentication prompt** remains off. After the first Pocket ID sign-in, confirm that `iam-anuragvishwakarma` has the intended environment role before relying on it for administration.

## Recovery and access

The restored Portainer state originated at the former `/EX/RECOVERY/2026-09-15/rootfs/opt/SRVR/Portainer/portainer_data` path. Recovery copied the database, cryptographic key material, configuration, and rollback copy into `/data/portainer` before the service was started. The external recovery tree was erased when the SSD was reformatted on 2026-09-23.

Recovery was validated on 2026-09-21 with the preserved database migrating from `2.45.0` to `2.45.1`. The live state and its local rollback copy under `/data/portainer` now require independent backups.

Portainer is configured to serve HTTP internally only at `10.1.1.4:9000`; Caddy terminates public-facing TLS and is the only supported browser entrypoint. The `--trusted-origins` setting is deliberately limited to `https://portainer.l3b.cc.cd`; the old `ctl.qzz.io` origin is not retained.

## Operations

```bash
cd /data/apps/portainer
sudo docker compose config --quiet
sudo docker compose up -d
sudo docker compose ps
curl --fail --silent --show-error http://10.1.1.4:9000/api/status
```

The live `.env` is local-only and must contain an immutable `PORTAINER_IMAGE` digest. Do not use an unreviewed `latest` tag: Portainer database schema upgrades are one-way. Take a Portainer backup and retain `/data/portainer/backups/portainer.db.bak` before deliberately moving to a new release.
