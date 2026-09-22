# Uptime Kuma

Uptime Kuma `2.5.5` runs natively under systemd in Proxmox CT 104 `beszel`; Docker and PM2 are intentionally not installed. The private UI is `https://status.l3b.cc.cd`. Caddy restricts it to LAN/Tailscale clients, and Tinyauth requires the canonical administrator email plus Pocket ID group `infrastructure-admins` before any request reaches Uptime Kuma.

Uptime Kuma does not support native OIDC. Its built-in authentication is disabled so a successful Pocket ID/Tinyauth session opens the dashboard directly. This is safe only because CT 104's persistent nftables policy permits TCP `3001` from loopback and Caddy `10.1.1.3`, then rejects every other source. Do not disable or weaken that rule while application authentication is disabled. The saved Uptime Kuma username/password remains the break-glass credential to re-enable local authentication from the CT console.

## Layout

```text
application:  /opt/uptime-kuma
data:         /var/lib/uptime-kuma
environment:  /etc/uptime-kuma/uptime-kuma.env
service:      /etc/systemd/system/uptime-kuma.service
firewall:     /etc/nftables.conf
backend:      10.1.1.7:3001
```

The application tree is root-owned and pinned to Git tag `2.5.5`. The dedicated `uptime-kuma` system account can write only its SQLite data directory. That directory resides on CT 104's local ZFS root disk and is included in the existing five-minute Proxmox replication from `px10` to `px30`. Uptime Kuma and Beszel share the same HA failure domain; neither service is an external check for total cluster, router, power, or internet failure.

## Operations

```bash
ssh root@10.1.1.7 'systemctl is-enabled uptime-kuma; systemctl is-active uptime-kuma'
ssh root@10.1.1.7 'journalctl -u uptime-kuma --since=-15min --no-pager'
curl -I https://status.l3b.cc.cd
```

An unauthenticated HTTPS request must return `401` from Tinyauth. An authenticated Pocket ID session must open the dashboard without a second Uptime Kuma login. Caddy supports the application's WebSocket connection automatically through `reverse_proxy`. A connection to `10.1.1.7:3001` from any machine except proxy `10.1.1.3` must be rejected.

## Backup

The authoritative application state is `/var/lib/uptime-kuma`. Use Uptime Kuma's built-in backup, or stop the service before copying the SQLite directory. Store a tested copy outside the Proxmox cluster; HA replication is not a backup.

## Upgrade

Read the upstream release and migration notes first. Take a consistent data backup, fetch the explicit release tag in `/opt/uptime-kuma`, run `npm ci --omit dev --no-audit` and `npm run download-dist`, restore root ownership on the application tree, then restart and validate the service. Never track `latest` or force-reset over local state; all mutable state belongs under `/var/lib/uptime-kuma`.
