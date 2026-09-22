# Restored Portainer services

These workloads were recovered from the read-only external SSD at `/EX/RECOVERY/2026-09-15` into the persistent ext4 data disk on `ctr`. Portainer owns their stack definitions and retained application secrets; this repository records the topology and recovery decisions without secrets.

| Stack | Persistent path | Host port | URL | State |
| --- | --- | ---: | --- | --- |
| `n8n` | `/data/apps/n8n` | 5678 | `https://n8n.l3b.cc.cd` | Running |
| `memos` | `/data/apps/memos` | 5230 | `https://notes.l3b.cc.cd` | Running |
| `code` | `/data/apps/code` | 8080 | `https://code.l3b.cc.cd` | Running |
| `nextcloud` | `/data/apps/nextcloud` | pending validation | pending validation | Restore in progress |
| `jellyfin` | Existing Portainer definition | none | none | Definition retained; intentionally stopped |

All running stacks attach to the external Docker bridge `docknet`. Only the application ports needed by Caddy are published; databases remain bridge-only.

## Recovery layout

- n8n: application data, files, and PostgreSQL 18 data under `/data/apps/n8n`
- Memos: SQLite state under `/data/apps/memos/data`
- code-server: configuration, local state, and workspace under `/data/apps/code`
- Nextcloud: configuration, user data, and MariaDB under `/data/apps/nextcloud/{config,data,mariadb}`

The source SSD normally remains mounted read-only. Do not start Nextcloud until all three source trees have copied successfully and ownership has been validated.

## Retired workloads

Guacamole, firstfinger/Ghost, and Orva were removed from Portainer and their associated recovery data was intentionally deleted. Cairn was explicitly retained and restored; see `infrastructure/cairn/README.md`.

## Validation

```bash
ssh ctr 'curl -fsS http://127.0.0.1:5678/healthz'
ssh ctr 'curl -fsS http://127.0.0.1:5230/healthz'
ssh ctr 'curl -fsS http://127.0.0.1:8080/healthz'
ssh ctr 'sudo docker ps --filter network=docknet'
```

After any stack edit, validate both the local health endpoint and the Caddy URL. Do not infer a successful restore from Portainer metadata alone.
