# l3b host-native baseline

Only components that need the host kernel, hardware, boot path or must survive
a Docker outage run outside Docker.

| Component | Unit / path | Notes |
| --- | --- | --- |
| WireGuard | `wg-quick@wg0.service` | VPN; no Docker dependency |
| Beszel agent | `beszel-agent.service` | Native 0.21.1; `10.1.1.10:45876`; daily update timer; monitors `/` (NVMe) and `/data` (SATA) only |
| OLX MCP gateway | `olx-mcp-gateway.service` | Native `mcp-proxy` on `127.0.0.1:8811`; one shared OLX stdio container on `l3b` for Hermes, OpenCode and Claude Code |
| SMART monitoring | `smartd.service` | Warnings forwarded to Telegram by `smartd-alert.py` |
| Security updates | `unattended-upgrades.service` | Debian security updates only; no automatic reboot |
| Network | `systemd-networkd`, `systemd-resolved` | Sole host network/DNS manager |
| Remote shell | `ssh.service` | Existing keys only |
| SMB share | `smbd.service` | Native Samba; shares `MEDIA` (`/data/apps/smb`) and `BACKUP` (`/BACKUP`) on TCP **445** only; see [../smb/README.md](../smb/README.md) |
| Coding agents | `opencode.service`, Hermes user gateway | Need host filesystem/tool access |
| microsandbox | `/opt/microsandbox`, `/usr/local/bin/msb` | Global CLI for disposable agent microVMs (libkrun + KVM); per-user state in `~/.microsandbox`. See [../microsandbox/README.md](../microsandbox/README.md) |

## OLX MCP gateway

Install `mcp-proxy@6.7.21` into the `dev` npm prefix so
`/home/dev/.local/bin/mcp-proxy` exists, then enable
`olx-mcp-gateway.service` (tracked beside this file). It serves `/mcp` on
loopback and owns one shared OLX stdio container on `l3b`; Hermes, OpenCode and
Claude Code all use `http://127.0.0.1:8811/mcp`.

## Beszel sensors

The OptiPlex fan tachometer is exposed only when `dell_smm_hwmon` is loaded
with `force=1`; this is persisted by `dell-smm-hwmon.conf` and the modules-load
file. Fan RPM then appears in Beszel.

Intel iGPU usage is read via `intel_gpu_top`; the binary and the agent service
carry `CAP_PERFMON`/`CAP_SYS_ADMIN`, with the APT post-invoke hook reapplying
the file capabilities after package updates. SMART uses `/dev/nvme0n1:nvme`
and `/dev/sda:sat`, so the external USB disk is not included.

The forced Dell SMM probe is specific to this OptiPlex 5060 and BIOS; remove the
module option if a future firmware update makes it unstable.

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
