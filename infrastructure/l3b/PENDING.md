# Pending restores on l3b

Checked 2 November 2026. Omni is removed from scope because Kubernetes is gone.
Omni is out of scope and is not deployed.

## Deployed now

Core: Portainer, AdGuard/Unbound, Caddy, Pocket ID/Tinyauth, Homepage,
OpenViking/Ollama, native OpenCode with Playwright CLI only.

Applications: Nivra, Orva, Karakeep, Immich, OpenCloud, Paperless, n8n,
qBittorrent, Motrix, Jellyfin, Registry, Forgejo, Frigate and Nivra The King.

Object storage: RustFS (including existing buckets) and Cairn (including the
Quick Share bucket/user and successful upload/download round trip).

## Still pending

| Item | State |
| --- | --- |
| n8n sandbox services | Core n8n/Postgres/SearXNG are deployed; the optional privileged AI sandbox runner was not restored. |
| Forgejo mirror | Running; its external mirror configuration/data was not yet validated. |
| Hermes | Configuration/data staged; stack remains stopped and messaging/automation is not launched. |
| Watchtower | Optional updater; deliberately inactive. |

## Outstanding acceptance

- Frigate camera/MQTT and recording verification; the service is running with the restored outdoor camera config.
- Human passkey/OIDC sign-in for the public apps.
- Independent off-network checks for public routes.
- WireGuard profile re-import on MacBook/iPhone.
- Reboot, Docker-daemon restart and current-node backup/restore drills.
- OpenCloud LDAP bind credential rotation remains a controlled follow-up.
