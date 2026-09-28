# External monitoring on slate

`slate` is the GCP VM outside the home network. It runs three native systemd services, with no Docker or Portainer Agent:

| Service | Version | Public URL | Local listener | State |
| --- | --- | --- | --- | --- |
| ntfy | 2.28.0 | `https://ntfy.l3b.cc.cd` | `127.0.0.1:2586` | `/var/lib/ntfy` |
| Uptime Kuma | 2.5.5 | `https://watch.l3b.cc.cd` | `127.0.0.1:3001` | `/var/lib/uptime-kuma` |
| Caddy | 2.11.4 + Cloudflare DNS plugin | TCP/UDP 443 | public | `/var/lib/caddy` |

Cloudflare has explicit DNS-only A records for `ntfy` and `watch` pointing to slate's public IP `8.235.70.28`. Internal AdGuard/Unbound has matching exact-name exceptions so the private wildcard does not send these names to the home proxy. Caddy uses Cloudflare DNS-01 for independent certificates and serves only these two names. Port 80 is unnecessary; TCP 443 is required and UDP 443 enables HTTP/3. The slate OS resolver is independent of home DNS. Tailscale accepts the approved `10.1.1.0/24` subnet route but does not accept tailnet DNS. Home services can reach the public ntfy endpoint; slate reaches home checks through the redundant Proxmox subnet routers.

The public URLs are intentionally different from the private internal Uptime Kuma at `status.l3b.cc.cd`. The external instance has its own database and native password plus TOTP login. Its credentials are in the distinct HomeLab vault item `Uptime Kuma - Slate`; the native ntfy administrator credential and `infra` publisher token are in the `ntfy` item. Neither token nor password belongs in Git. The ntfy default access is deny-all; anonymous publish is forbidden. The `publisher` account is limited to write-only access to topic `infra`. ntfy is configured with `upstream-base-url` for timely iOS background pushes; the owner still needs to subscribe to the self-hosted server/topic in the mobile client and verify delivery.

## Monitors and alerts

The six 60-second monitors are `Home public web`, `Home private proxy`, `Home DNS`, and `Proxmox px10`, `px20`, `px30`. Public web checks the storefront. Private proxy checks its expected unauthenticated `401` across Tailscale. DNS queries AdGuard at `10.1.1.2:53`. Proxmox checks each node's API endpoint and expects `401`; TLS verification is disabled only for those private, self-signed node endpoints. All monitors send alerts to local ntfy topic `infra` using the restricted publisher token. The notification test and all six UP heartbeats were verified on 2026-09-28.

After a cold-cache restart on slate's small GCP persistent disk, Uptime Kuma took about two minutes to load its Node modules and open port 3001. During that window Caddy returned 502, even though systemd already reported the process as active. Verify the listener and HTTP response after maintenance; do not infer readiness from `systemctl is-active` alone.

This VM is an independent external viewpoint, not a replacement for the private status dashboard. A slate or GCP outage can prevent its own alerts. An outage of both home internet and the Tailscale path prevents private checks, while public checks remain independent. Avoid publishing unauthenticated service internals or monitoring secrets.

## Files and operations

The sanitized files in this directory map to the same paths on slate: `Caddyfile` to `/etc/caddy/Caddyfile`, `caddy.service` to `/etc/systemd/system/caddy.service`, `ntfy-server.yml` to `/etc/ntfy/server.yml`, and `uptime-kuma.env` to `/etc/uptime-kuma/uptime-kuma.env`. The Cloudflare token lives only in `/etc/caddy/cloudflare.env` (root:caddy, `0640`). The Caddy binary at `/usr/local/bin/caddy` was copied from the existing custom proxy build; its checksum was checked against the source. The Uptime Kuma application is root-owned at `/opt/uptime-kuma`, while its service account owns only `/var/lib/uptime-kuma`. `setup-kuma.cjs`, `kuma-2fa.cjs`, and `configure-kuma.cjs` are installation/recovery helpers; supply credentials through stdin, never command-line arguments or Git.

```bash
ssh slate 'systemctl is-enabled ntfy uptime-kuma caddy; systemctl is-active ntfy uptime-kuma caddy'
ssh slate 'journalctl -u ntfy -u uptime-kuma -u caddy --since=-15min --no-pager'
curl -I https://ntfy.l3b.cc.cd/
curl -I https://watch.l3b.cc.cd/
```

For upgrades, read upstream release notes and pin explicit versions. ntfy uses its native Debian package. Uptime Kuma is Node.js, not a Go binary: reinstall build-time npm if needed, run `npm ci --omit=dev --no-audit --no-fund` and `npm run download-dist` at the pinned tag, and then restart the service. Keep a consistent copy of `/var/lib/uptime-kuma` (stop the service or use a SQLite-safe backup) and `/var/lib/ntfy` before upgrades. Keep `/var/lib/caddy` for ACME account/certificate recovery. Do not delete the two vault items or rotate their secrets without updating dependent notifications. Re-run the tests above, a logged-in Uptime Kuma browser check, an unauthenticated ntfy publish denial, and an ntfy test notification after changes.
