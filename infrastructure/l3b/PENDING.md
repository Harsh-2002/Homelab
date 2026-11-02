# Pending restores on l3b

Checked 2 November 2026. Omni is removed from scope because Kubernetes is gone.
Omni is out of scope and is not deployed.

## Deployed now

Core: Portainer, AdGuard/Unbound, Caddy, Pocket ID/Tinyauth, Homepage,
OpenViking/Ollama, native OpenCode with Playwright CLI only.

Applications: Nivra, Orva, Karakeep, Immich, OpenCloud, Paperless, n8n
(including SearXNG and the isolated sandbox API/runner), qBittorrent, Motrix,
Jellyfin, Registry, Frigate, Home Assistant and Nivra The King.
Forgejo containers are stopped; its stack is retained pending an upgrade decision.

Object storage: RustFS (including existing buckets) and Cairn (including the
Quick Share bucket/user and successful upload/download round trip).

## Still pending

| Item | State |
| --- | --- |
| Forgejo | Containers stopped; stack 135 retained. Forgejo 14 is EOL; upgrade/replacement is a separate decision. |
| Hermes | Restored natively at `/home/dev/.hermes`; `hermes-gateway.service` is active/enabled with Telegram, Photon/iMessage and API server connected. No cron jobs. |
| Watchtower | Optional updater; deliberately inactive. |

## Outstanding acceptance

- Frigate outdoor camera, go2rtc stream, MQTT and HA camera/sensors are verified; recording is active with 114 GB retained. Detection/zone tuning remains optional.
- Human passkey/OIDC sign-in for the public apps.
- Portainer is the only running container without an in-container healthcheck (no shell in image); monitor its API externally.
- Home Assistant Frigate camera and MQTT are working; the Tuya bulb and Localthings AC remain unreachable. VictoriaMetrics/Grafana are retired in favour of Beszel. No Supervisor/add-ons in Container mode.
- Independent off-network checks for public routes.
- WireGuard profile re-import on MacBook/iPhone.
- Reboot, Docker-daemon restart and current-node backup/restore drills.
- OpenCloud LDAP bind credential rotation remains a controlled follow-up.
