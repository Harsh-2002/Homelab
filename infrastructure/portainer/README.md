# Portainer

Portainer EE runs as a Docker Compose service on VM 204 `ctr`, with restored state in `/data/portainer` and its Compose files in `/data/apps/portainer`. It is served privately at `https://portainer.l3b.cc.cd` by Caddy; Portainer retains its own login rather than using a Caddy authentication layer.

## Recovery and access

The preserved Portainer state originates at `/EX/RECOVERY/2026-09-15/rootfs/opt/SRVR/Portainer/portainer_data`. It contains the Portainer database, cryptographic key material, configuration, and its automatic database rollback copy. The external recovery disk remains read-only; recovery copies its contents into `/data/portainer` before the service is started.

Recovery was validated on 2026-09-21 with the preserved database migrating from `2.45.0` to `2.45.1`. The source and its rollback copy remain untouched on `/EX`; only the working copy under `/data/portainer` was migrated.

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
