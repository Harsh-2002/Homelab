# Container data map

Where every running container keeps its state. Verified 2026-11-09 against
`docker inspect`. All application state is bind-mounted under `/data/apps`;
Docker-managed volumes are used only for cache/TLS data and live on the NVMe
per the host policy.

| Container | Stack | Host data |
|---|---|---|
| `adguard` | dns | `/data/apps/adguard/conf` -> `/opt/adguardhome/conf`; `/data/apps/adguard/work` -> `/opt/adguardhome/work` |
| `beszel` | beszel | `/data/apps/beszel/data` -> `/beszel_data` |
| `caddy` | proxy | `/data/apps/caddy/config` -> `/config`; `/data/apps/caddy/data` -> `/data`; `/data/apps/caddy/Caddyfile` -> `/etc/caddy/Caddyfile`; `/data/apps/caddy/caddy` -> `/usr/bin/caddy` |
| `cairn` | cairn | `/data/apps/cairn` -> `/data/cairn` |
| `desktop` | desktop | `/data/apps/desktop/home` -> `/home/ubuntu` |
| `frigate` | frigate | `/data/apps/frigate/config` -> `/config`; `/data/apps/frigate/media` -> `/media/frigate` |
| `homeassistant` | homeassistant | `/data/apps/homeassistant` -> `/config`; `/data/apps/homeassistant/media` -> `/media`; `/data/apps/homeassistant/share` -> `/share`; `/data/apps/homeassistant/ssl` -> `/ssl`; `/BACKUP/homeassistant` -> `/BACKUP/homeassistant` |
| `homepage` | dashboard | `/data/apps/homepage/config` -> `/app/config` |
| `immich` | immich | `/data/apps/immich/media` -> `/data` |
| `immich-ml` | immich | `/data/apps/immich/model` -> `/cache` |
| `immich-postgres` | immich | `/data/apps/immich/postgres` -> `/var/lib/postgresql/data` |
| `jellyfin` | jellyfin | `/data/apps/jellyfin/cache` -> `/cache`; `/data/apps/jellyfin/config` -> `/config`; `/data/apps/smb` -> `/media` |
| `karakeep` | karakeep | `/data/apps/karakeep/data` -> `/data` |
| `karakeep-meilisearch` | karakeep | `/data/apps/karakeep/meilisearch` -> `/meili_data` |
| `motrix` | motrix | `/data/apps/motrix/motrix-data` -> `/data`; `/data/apps/smb/downloads` -> `/downloads`; `/data/apps/smb` -> `/media` |
| `mqtt` | mqtt | `/data/apps/mqtt/config` -> `/mosquitto/config`; `/data/apps/mqtt/data` -> `/mosquitto/data`; `/data/apps/mqtt/log` -> `/mosquitto/log` |
| `n8n` | n8n | `/data/apps/n8n/files` -> `/files`; `/data/apps/n8n/data` -> `/home/node/.n8n` |
| `n8n-db` | n8n | `/data/apps/n8n/db` -> `/var/lib/postgresql` |
| `nivra` | nivra | `/data/apps/nivra` -> `/data` |
| `ollama` | memory | `/data/apps/openviking/ollama` -> `/root/.ollama` |
| `opencloud` | opencloud | `/data/apps/opencloud/config` -> `/etc/opencloud`; `/data/apps/opencloud/data` -> `/var/lib/opencloud` |
| `openviking` | memory | `/data/apps/openviking/state` -> `/app/.openviking`; `/data/apps/openviking/state/hotfixes/session_commit_processor.py` -> `/app/.venv/lib/python3.13/site-packages/openviking/storage/queuefs/session_commit_processor.py` |
| `orva` | orva | `/data/apps/orva` -> `/var/lib/orva` |
| `paperless` | paperless | `/data/apps/paperless/consume` -> `/usr/src/paperless/consume`; `/data/apps/paperless/data` -> `/usr/src/paperless/data`; `/data/apps/paperless/export` -> `/usr/src/paperless/export`; `/data/apps/paperless/media` -> `/usr/src/paperless/media` |
| `paperless-broker` | paperless | `/data/apps/paperless/valkey` -> `/data` |
| `pocketid` | identity | `/data/apps/pocket-id/data` -> `/app/data`; `/data/apps/pocket-id/encryption-key` -> `/run/secrets/pocket-id-key` |
| `portainer` | portainer | `/data/apps/portainer` -> `/data` |
| `qbittorrent` | qbittorrent | `/data/apps/qbittorrent` -> `/config`; `/data/apps/smb` -> `/data` |
| `registry` | registry | `/data/apps/registry/auth` -> `/auth`; `/data/apps/registry/storage` -> `/var/lib/registry`; `/data/apps/registry/config.yml` -> `/etc/docker/registry/config.yml` |
| `rustfs` | rustfs | `/data/apps/rustfs/data` -> `/data`; `/data/apps/rustfs/logs` -> `/logs` |
| `sandbox-api` | n8n | `/data/apps/n8n-sandbox/api` -> `/var/lib/n8n-sandbox-api`; volume `n8n_sandbox-tls` -> `/tls` |
| `sandbox-runner` | n8n | volume `n8n_sandbox-tls` -> `/tls`; volume `db07d6e9a4319763abae782f9477fc025bc4648f3a4e956f1c10b9af93ff39d5` -> `/var/lib/docker` |
| `searxng` | n8n | `/data/apps/n8n/searxng-settings.yml` -> `/etc/searxng/settings.yml`; volume `b008ceb665db5695902c49b9a2550301363f28fb3858a7bad8f79509c494a471` -> `/etc/searxng`; volume `3fbab30660c8bab365e2010f88539415604940a75c24189daa48fe3f1b245353` -> `/var/cache/searxng` |
| `theking` | theking | `/data/apps/nivra-theking` -> `/data` |
| `tinyauth` | identity | `/data/apps/tinyauth/data` -> `/data` |
| `unbound` | dns | `/data/apps/unbound/unbound.conf` -> `/etc/unbound/unbound.conf`; `/data/apps/unbound/state` -> `/var/lib/unbound` |

## Containers without persistent mounts

These are stateless or cache-only by design; a recreate loses nothing that matters:

- `immich-redis`
- `jolly_hellman`
- `karakeep-chrome`
- `watchtower`

## Notes

- The registry stores blobs in RustFS (S3 bucket `docker-registry`), not in `/data/apps/registry/storage`; the empty bind mounted at `/var/lib/registry` is vestigial.
- `immich-redis` is a queue/cache and intentionally has no volume.
- `karakeep-chrome` is a disposable browser profile.
- `jolly_hellman` is the shared OLX MCP proxy and holds no state.
- Old Jellyfin cache volumes and a stale SearXNG volume were pruned on 2026-11-09.

