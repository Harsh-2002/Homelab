# Termix remote access

Termix 2.8.0 runs on ctr through Portainer stack `termix` (ID 155, endpoint 2). URL: `https://remote.l3b.cc.cd`. Existing Caddy terminates HTTPS using its Cloudflare wildcard certificate and forwards to `10.1.1.4:8090` (container port 8080). Access is private to LAN/Tailscale through Caddy's existing `private` policy, not anonymously public. From elsewhere, connect to the tailnet and use homelab subnet routing. No target SSH/RDP ports or guacd port are published by this stack.

## Deployment and persistence

`compose.yaml` is the sanitized Portainer Stackfile. Two containers: `termix` and `guacd`, on `termix_default`. No docknet, Docker socket, privileged mode, host network, extra database or extra reverse proxy. SQLite, encryption keys, generated security secrets, connections and configuration persist in `/data/apps/termix`, mounted at `/app/data`. Termix uses its official entrypoint with PUID/PGID 1000. The entrypoint resets the directory to 1000:1000 mode 0755, so do not claim a manually set 0700 survives it. A shell wrapper sets umask 077 before executing the unmodified entrypoint; existing secret/database files were set to 0600. Preserve the full directory, especially generated `.env` and encryption keys, not just the database.

Images: `ghcr.io/lukegus/termix:2.8.0` and `guacamole/guacd:1.6.0`. Both use `unless-stopped`, no-new-privileges, capped JSON logs and Watchtower opt-out. Limits: one CPU/1 GiB for Termix and one CPU/512 MiB for guacd. Review limits for concurrent desktop sessions. guacd is internal-only with no published ports or persistent database. Recording is not configured; enabling it requires a deliberately shared recording mount and matching ownership/path settings.

`ENABLE_GUACAMOLE=true`, `GUACD_HOST=guacd`, `GUACD_PORT=4822` and `GUACD_TUNNEL_HOST=termix` configure remote desktop. This uses the protocol daemon, not the retired standalone Guacamole application. Never expose TCP 4822 to LAN/Internet.

## Authentication and use

Owner admin login: `iam.anuragvishwakarma@gmail.com`. Generated password: HomeLab 1Password item `Termix`. Secrets were not printed or committed. Bootstrap was loopback-only with temporary registration enabled. The first admin was created and authenticated before the Portainer stack switched to permanent LAN binding and `ALLOW_REGISTRATION=false`. Password login remains enabled; telemetry is disabled.

Use Host Manager → Add Host. For SSH, specify target address, username and authorized SSH key/password. For RDP, select RDP and supply a reachable Windows/RDP server and its login. App login does not authenticate you to targets. Existing dev private keys and all vault credentials were not copied automatically. No OIDC integration was requested in this replacement task; native account login is configured.

Homepage card: Control section, application favicon, URL health ping. No invented stats widget or admin key in Homepage.

## Operation and verification

Manage through Portainer stack 155, never an independent Compose project. Before upgrading, stop via Portainer for a consistent full data-directory backup, review stable release notes, update Stackfile/version and Git together, then verify login, saved hosts, SSH/RDP sessions and Homepage. The directory is on ctr's local data disk and in its whole-VM backup scope; a disaster-recovery restore was not tested here.

```sh
curl -fsS https://remote.l3b.cc.cd/users/registration-allowed
curl -s -o /dev/null -w '%{http_code}\n' https://remote.l3b.cc.cd/users/me
ssh ctr 'sudo docker inspect termix --format "{{.State.Health.Status}}"'
```

Verified: registration disabled, unauthenticated account API HTTP 401, container healthy. Native admin login and the authenticated 2.8.0 dashboard were verified in a real browser with no page errors, including after a Portainer restart; the account persisted. Official image checks backend `/health`, not just the frontend. TCP connectivity from Termix to guacd was verified; guacd has no published ports. SQLite and Guacamole initialize cleanly. Target-specific SSH/RDP sessions must be tested against actual configured targets before claiming they work. No Windows RDP target was supplied in this task. The first-login onboarding is optional; use Skip setup to go straight to adding hosts.

Sources: [Docker deployment](https://docs.termix.site/install/server/docker/), [environment configuration](https://docs.termix.site/setup/environment-variables/), [remote desktop setup](https://docs.termix.site/setup/remote-desktop/), [release](https://github.com/Termix-SSH/Termix/releases/tag/release-2.8.0-tag).
