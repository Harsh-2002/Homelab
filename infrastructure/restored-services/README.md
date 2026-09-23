# Restored Portainer services

These workloads were recovered from the former external SSD tree at `/EX/RECOVERY/2026-09-15` into the persistent ext4 data disk on `ctr`. That recovery tree was erased when the owner reformatted the SSD on 2026-09-23. Portainer owns their stack definitions and retained application secrets; this repository records the topology and recovery decisions without secrets. Cairn is no longer part of this Portainer group.

| Stack | Persistent path | Host port | URL | State |
| --- | --- | ---: | --- | --- |
| `n8n` | `/data/apps/n8n` | 5678 | `https://n8n.l3b.cc.cd` | Running |
| `jellyfin` | `/data/apps/jellyfin` + `/mnt/AV/media` | 8096 | `https://media.l3b.cc.cd` | Running; see `infrastructure/jellyfin/README.md` |

The `AV` SMB share is mounted on `ctr` at `/mnt/AV`. Jellyfin reads only `/mnt/AV/media` and keeps its application state on local `/data/apps`; JDownloader remains stopped. See `infrastructure/ctr/README.md`.

Each running stack uses its own Compose default bridge. Only the application ports needed by Caddy are published; databases remain bridge-only. Do not attach new stacks to the retired shared `docknet` bridge.

## Recovery layout

- n8n: application data, files, and PostgreSQL 18 data under `/data/apps/n8n`
Nextcloud was retired after its 706 live files were compared byte for byte with OpenCloud; see `infrastructure/opencloud/README.md`.

n8n's existing owner email is `iam.anuragvishwakarma@gmail.com`. Native password login and its existing MFA were verified; Caddy's extra Tinyauth gate was removed, but the route stays LAN/Tailscale-only. The existing `N8N` 1Password item was updated, not duplicated.


## Retired workloads

Guacamole, firstfinger/Ghost, Orva, and code-server were removed from Portainer and their associated recovery data was intentionally deleted. The temporary recovered Cairn stack and `/data/apps/cairn` copy were also removed after Cairn was redeployed fresh as a native service on the `s3` LXC; see `infrastructure/cairn/README.md`.

Nextcloud Portainer stack 92 and both containers were removed. Its staged `/data/apps/nextcloud` and `/data/backups/nextcloud` directories were deleted after OpenCloud verification. The former whole-system tar was later erased by the external SSD reformat.

## Validation

```bash
ssh ctr 'curl -fsS http://127.0.0.1:5678/healthz'
ssh ctr 'curl -fsS http://127.0.0.1:5230/healthz'
ssh ctr 'sudo docker ps --format "{{.Names}} {{.Networks}}"'
```

After any stack edit, validate both the local health endpoint and the Caddy URL. Do not infer a successful restore from Portainer metadata alone.
