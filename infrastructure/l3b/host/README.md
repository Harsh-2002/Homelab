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
| mDNS | `avahi-daemon.service` | Advertises SMB and the Time Machine destination on `eno1` only |
| Homepage stats | `homelab-stats.service` | Read-only JSON on `10.1.3.1:8099` with CPU, RAM, temp, disk and container totals, image count, failed systemd units and `eno1` throughput for the Homepage widget and Home Assistant REST sensors; unit and script tracked here |
| Power-key watch | `powerkey-watch.service` | Records ACPI power-button events (append-only `/var/log/powerkey-events.log` plus count in `/var/lib/powerkey-watch/state.json`) and exposes them to Home Assistant; see [BIOS-VERSIONS.md](BIOS-VERSIONS.md) |
| Crash evidence | `crash-record.service` | On every boot writes the previous boot's last 200 journal lines, reboot history and temperatures to `/data/apps/diagnostics/crash-history/` |
| Switch proxy | `switch-proxy.socket` | Forwards `10.1.3.1:8088` to the NETGEAR GS110TPv3 UI at `192.168.0.239:80`; the host holds a second address `192.168.0.10/24` on `eno1` because the switch has no route back to the Docker bridge. Reachable through Caddy at `https://switch.l3b.cc.cd` behind Tinyauth. |
| Power logging | `power-log.service` | One line per second with RAPL package watts, package temperature and load, fsynced to `/data/apps/diagnostics/power/power-YYYYMMDD.csv` |
| SMB share | `smbd.service` | Native Samba; shares `MEDIA` (`/data/apps/smb`) and `BACKUP` (`/BACKUP`) on TCP **445** only; see [../smb/README.md](../smb/README.md) |
| Coding agents | `opencode.service`, Hermes user gateway | Need host filesystem/tool access |
| microsandbox | `/opt/microsandbox`, `/usr/local/bin/msb` | Global CLI for disposable agent microVMs (libkrun + KVM); per-user state in `~/.microsandbox`. See [../microsandbox/README.md](../microsandbox/README.md) |

## Power diagnostics

The crash, power and power-key services above exist because of the repeated
hard power-offs on 9 November 2026. Their output lives off the root disk under
`/data/apps/diagnostics`; its README describes the layout and how to read a
crash, while [INCIDENT-2026-11-09-power.md](INCIDENT-2026-11-09-power.md) holds
the timeline, evidence and conclusions.

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

## Package updates, 8 November 2026

Routine global upgrade on Debian 13 (trixie), kernel 7.2.11, uptime 5 days.

| Source | Before | After |
| --- | --- | --- |
| docker-ce, cli, rootless-extras | 29.9.2 | 29.9.3 |
| docker-compose-plugin | 5.6.1 | 5.7.0 |
| claude-code (Anthropic apt) | 2.1.316-1 | 2.1.319-1 |
| npm `@excalidraw/cli` | 0.2.0 | 0.3.0 |
| npm `cf` | 1.0.0-beta.26 | 1.0.0-beta.28 |
| npm `mcp-proxy` | 6.7.21 | 6.9.1 |

`opentunnel` 0.6.2, `@playwright/cli` 0.1.23, `bash-language-server` 5.8.1 and
`typescript` 7.0.2 were already current. No kernel, libc or systemd change, so no
reboot was required; `apt-get autoremove` had nothing to remove.

The Docker upgrade restarted `dockerd`. All 40 containers stayed up with none
unhealthy, and reachability was verified afterwards: `l3b.cc.cd` returned 401
from the auth gate as designed, `home.l3b.cc.cd` and `notes.l3b.cc.cd` returned
200, and the Portainer API returned 200.

npm 12 blocks dependency install scripts by default, so `workerd` and `tldjs`
post-install scripts were skipped. Both were checked rather than blindly allowed:
`tldjs` resolves public suffixes correctly (`example.co.uk`), and `workerd` is only
needed for the Cloudflare Workers runtime, not the DNS/API commands used here. If
a Workers command is ever needed, reinstall with
`npm install -g cf --allow-scripts=workerd,tldjs`.

## Power-button and backup-mount hardening, 7 November 2026

Two unexplained shutdowns on 7 November were ACPI power-button events, not
crashes; see [INCIDENT-2026-11-07-power.md](INCIDENT-2026-11-07-power.md). Short
presses are now ignored by logind
(`/etc/systemd/logind.conf.d/10-ignore-powerkey.conf`, `HandlePowerKey=ignore`),
so a bouncing switch cannot power the host off; intentional stops use
`sudo poweroff`.

`/BACKUP` now mounts only after the VL817 UAS rebind has finished, via
`x-systemd.requires=usb-uas-rebind.service,x-systemd.after=usb-uas-rebind.service`
and a 30 s device timeout in `/etc/fstab`. Previously the mount and the rebind
started from the same USB event, and the device disappeared mid-mount, leaving
the filesystem shut down and Time Machine paused. Previous fstab kept at
`/etc/fstab.bak-2026-11-07`.

## Second package pass, 8 November 2026

| Layer | Before | After |
| --- | --- | --- |
| apt `zlib1g`, `zlib1g-dev` (stable-security) | `1.3.1-1+b1` | `1.3.1-1+deb13u1` |
| Hermes Agent (stable channel) | v0.22.5 | v0.23.0 |
| rustup | 1.29.2 | 1.29.3 (rustc 1.99.1 already current) |

Already current and unchanged: Node 26.13.0, npm 12.2.1, Go 1.27.3, gopls 0.24.0,
all npm globals, Docker 29.9.3, kernel 7.2.11, Intel microcode `0xfa`,
Home Assistant 2026.11.0, Jellyfin 12.4, Frigate 0.18.2, n8n 2.46.6.

Deliberately not changed:

- **System Python libraries** (anyio, cryptography, click and so on) are Debian
  packages in `/usr/lib/python3/dist-packages`. `pip` would break apt ownership
  (PEP 668); they move with Debian security updates.
- **OpenCode 2.2.5** must not be upgraded from inside its own serving process;
  see the native handover runbook.
- **zlib in running processes:** 37 host processes (systemd, sshd, Samba,
  journald and others) still map the old library. The fix reaches them at the
  next planned reboot or service restart; `homelab-stats` and `powerkey-watch`
  were restarted now. No reboot flag is set.

Hermes was updated with `hermes update --yes`; the gateway restarted with a drain
and reported v0.23.0 up to date. Shared skills (`opentunnel`, `microsandbox`,
`playwright-cli`, `herdr-control`, `excalidraw-local`) and the 0600 config files
were intact, and `check-integrations.py --single-node` passed.

### Container images behind upstream (not changed)

| Container | Running | Upstream | Pinning | Note |
| --- | --- | --- | --- | --- |
| Caddy | 2.11.4 | 2.11.9 | digest | security fixes in 2.11.6 and 2.11.8/2.11.9 |
| Pocket ID | 2.16.0 | 2.19.2 | digest | security fixes in 2.18.0 and 2.19.2 |
| AdGuard Home | 0.107.79 | 0.107.80 | digest | patch |
| Immich | 3.3.5 | 3.3.6 | `IMMICH_VERSION` | patch; telemetry already disabled by env |
| Paperless-ngx | 3.4.1 | 3.4.2 | tag | repo compose still says 3.2.1 (stale) |
| Meilisearch | 1.41.0 | 1.56.1 | tag | large jump; needs a dump/reindex plan |
| OpenCloud | 7.2.4 | 9.0.0 | tag | major; LDAP credential rotation still open |

Digest-pinned images are skipped by Watchtower by design. Container updates are
Portainer stack changes and need the owner's go-ahead per service.

## Shell startup error fixed, 7 November 2026

SSH logins printed `-bash: /tmp/uv/env: No such file or directory` twice, once from
the login shell (`~/.profile`) and once from the interactive shell (`~/.bashrc`).
`~/.zshrc` carried the same line.

Cause: a uv installer run on 5 November at 12:54 used `/tmp/uv` as its install
directory, and the installer appends `. "<dir>/env"` to the shell startup files.
`/tmp` does not survive a reboot, so the directory vanished while the lines stayed,
and every new shell then sourced a file that no longer existed. uv is not installed
on this host, so nothing depended on it.

Fix: removed the single `. "/tmp/uv/env"` line (and its blank line) from
`~/.bashrc`, `~/.profile` and `~/.zshrc`. Verified with fresh login and interactive
shells and a real SSH session with a TTY; the temporary backup copies were deleted
once the fix was confirmed.

Rule: never install tooling into `/tmp` with an installer that edits dotfiles. If
uv is wanted later, install it to `~/.local/bin` (`UV_INSTALL_DIR`) so the sourced
path survives reboots.
