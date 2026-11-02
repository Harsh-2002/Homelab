# l3b host-native baseline

Only components that need the host kernel, hardware, boot path or must survive
a Docker outage run outside Docker.

| Component | Unit / path | Notes |
| --- | --- | --- |
| WireGuard | `wg-quick@wg0.service` | VPN; no Docker dependency |
| Beszel agent | `beszel-agent.service` | Native 0.21.1; `10.1.1.10:45876`; daily update timer; monitors `/`, `/data`, USB backup |
| SMART monitoring | `smartd.service` | Warnings forwarded to Telegram by `smartd-alert.py` |
| Security updates | `unattended-upgrades.service` | Debian security updates only; no automatic reboot |
| Network | `systemd-networkd`, `systemd-resolved` | Sole host network/DNS manager |
| Remote shell | `ssh.service` | Existing keys only |
| Coding agents | `opencode.service`, Hermes user gateway | Need host filesystem/tool access |

## Beszel limits

The Dell OptiPlex exposes no fan tachometers through `/sys/class/hwmon`, so
Beszel cannot show fan RPM. The i915 GPU has no compatible hwmon energy counters, and Beszel reports no
valid Intel GPU data even after installing `intel-gpu-tools`; iGPU utilization
is therefore not shown in the UI. Temperatures, disk usage/IO, network and
Docker stats are available.

## SMART alerts

`/etc/smartd.conf`:

```text
DEVICESCAN -d removable -n standby -m <nomailer> -M exec /usr/local/sbin/smartd-alert
```

Install `smartd-alert.py` as `/usr/local/sbin/smartd-alert` (0700). It reads
`/etc/smartd-alert.env` (0600, root) containing the existing Hermes Telegram
bot token and chat ID. The token is never stored in Git or passed on the command
line. Test with a harmless message:

```sh
printf 'test\n' | sudo env SMARTD_DEVICE=/dev/sda SMARTD_FAILTYPE=TEST /usr/local/sbin/smartd-alert
```

## Security updates

`20auto-upgrades` enables daily package-list updates and unattended upgrades.
`50unattended-upgrades` restricts allowed origins to Debian security, keeps
automatic reboot disabled and removes obsolete kernel packages. Validate with:

```sh
sudo unattended-upgrade --dry-run --debug
```

## Deliberately not native

Backup runner and UPS/NUT are out of scope per the owner. Application services,
databases, Caddy, DNS and Beszel hub stay in Docker for isolation and easy
rollback.
