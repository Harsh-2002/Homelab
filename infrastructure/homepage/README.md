# Homepage dashboard (l3b)

Quick-glance dashboard for the whole host: **https://l3b.cc.cd** (private,
behind Tinyauth at `login.l3b.cc.cd`).

Live config: `/data/apps/homepage/config/` (bind-mounted into the container at
`/app/config`). The copies in `config/` here are the tracked source of truth;
Homepage hot-reloads YAML edits without a restart.

## Layout

| Group | What it shows |
| --- | --- |
| **Overview** | `l3b` host (links to Beszel), NETGEAR GS110TPv3 switch (via `switch.l3b.cc.cd`), LAN router |
| **Storage** | OpenCloud, Immich, Paperless-ngx, RustFS (S3 console), Cairn backup target |
| **Media** | Jellyfin, Frigate, qBittorrent, Motrix |
| **Applications** | Karakeep, OpenViking, Nivra, Orva, OpenCode, Home Assistant, n8n, Desktop |
| **Control** | AdGuard Home, Pocket ID, Tinyauth, Portainer, Beszel |

Top widgets: date/time, host stats and storage usage.

## Widgets and health checks

The two `customapi` widgets read `http://10.1.3.1:8099/stats`, the native
`homelab-stats.service` JSON (same source Home Assistant uses):

- CPU %, RAM %, package temperature, running containers, failed units, uptime;
- root / data / backup disk percentages and swap.

`siteMonitor` entries use **internal** container names (`http://immich:2283/...`,
`http://jellyfin:8096/health`, etc.) so the status dot does not depend on
Tinyauth. The switch is monitored through the host forwarder
(`http://10.1.3.1:8088/`). Services that only expose authenticated or S3
endpoints (RustFS, Cairn, registry) have no monitor to avoid false red dots.

## Editing

1. Change `/data/apps/homepage/config/{services,settings,widgets}.yaml`.
2. Mirror the change into `infrastructure/homepage/config/` and commit.
3. Homepage reloads automatically; check `/api/services` or the container log
   for YAML errors.

Backups of the previous layout: `*.bak-20261109` beside each file.

## Notes

- Service tiles must match the Caddy routes; adding a new service means adding
  the URL in `/data/apps/caddy/Caddyfile`, a Tinyauth app entry if it is a new
  host (default ACL is deny), and a tile here.
- The `Router` tile points at `http://10.1.1.1` (LAN only) and is intentionally
  HTTP.
