# Pending restores on l3b

Checked 2 November 2026. Omni is removed from scope because Kubernetes is gone.
Omni is out of scope and is not deployed.

## Deployed now

Core: Portainer, AdGuard/Unbound, Caddy, Pocket ID/Tinyauth, Homepage,
OpenViking/Ollama, native OpenCode with Playwright CLI only.

Applications: Nivra, Orva, Karakeep, Immich, OpenCloud, Paperless, n8n
(including SearXNG and the isolated sandbox API/runner), qBittorrent, Motrix,
Jellyfin, Registry, Frigate, Home Assistant, Nivra The King, MQTT and Beszel.
Forgejo and its mirror stacks are retained; their stopped containers and images
were removed by the Docker prune. Forgejo 14 is EOL pending an upgrade decision. Hermes is native and active.

Object storage: RustFS (including existing buckets) and Cairn (including the
Quick Share bucket/user and successful upload/download round trip).

## Still pending

| Item | State |
| --- | --- |
| Forgejo | Stack 135 retained; containers/images removed by prune. Forgejo 14 is EOL; upgrade/replacement is a separate decision. |
| Watchtower | Optional updater; deliberately inactive. |

## Outstanding acceptance

- Frigate outdoor camera, go2rtc stream, MQTT and HA camera/sensors are verified; recording is active with 114 GB retained. Detection/zone tuning remains optional.
- Human passkey/OIDC sign-in for the public apps.
- Portainer is the only running container without an in-container healthcheck (no shell in image); monitor its API externally.
- Home Assistant Frigate camera and MQTT are working; the Tuya bulb and Localthings AC are working after their DHCP addresses changed. VictoriaMetrics/Grafana are retired in favour of Beszel. No Supervisor/add-ons in Container mode.
- Independent off-network checks for public routes.
- WireGuard: iPhone handshake verified and router route/forward owner-confirmed; MacBook profile import and cold-boot recheck remain.
- Reboot, Docker-daemon restart and current-node backup/restore drills.
- OpenCloud LDAP bind credential rotation remains a controlled follow-up.
