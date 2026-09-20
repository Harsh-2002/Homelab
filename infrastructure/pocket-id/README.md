# Pocket ID

Pocket ID runs as a pinned standalone Go binary under systemd in Proxmox CT 103. Docker is intentionally not installed.

## Topology

| Item | Value |
| --- | --- |
| Guest | `auth` / CT 103 |
| Primary node | `px30` |
| HA target | `px10` |
| Replication | `103-0`, every 5 minutes |
| Address | `10.1.1.6` |
| URL | `https://auth.l3b.cc.cd` |
| Resources | 1 vCPU, 1 GiB RAM, 512 MiB swap |
| Root disk | 10 GiB `local-zfs` |
| Runtime | systemd, unprivileged Debian 13 LXC |
| Service port | `1411/tcp` |
| Database | local SQLite |

Pocket ID v2 is single-instance software. Availability comes from Proxmox HA restarting CT 103 on another node; do not start a second Pocket ID process against the same database.

The strict `ct103-replica-nodes` HA affinity rule permits only `px30` and `px10`, with `px30` preferred. A controlled relocation to `px10` and back was completed successfully on 2026-09-20 while the HTTPS endpoint remained healthy.

## Access

Root administration is allowed only with the shared Ed25519 SSH key. The root password is locked, and SSH password and keyboard-interactive authentication are disabled. Pocket ID itself runs as the unprivileged `pocket-id` system account.

Complete first-run enrollment from the private network at:

```text
https://auth.l3b.cc.cd/setup
```

Register the primary passkey in 1Password and keep a second recovery passkey before connecting other services.

## Paths

- Binary symlink: `/usr/local/bin/pocket-id`
- Versioned binaries: `/opt/pocket-id/versions/`
- Environment: `/etc/pocket-id/pocket-id.env`
- Sanitized environment template: `pocket-id.env.example`
- Encryption key: `/etc/pocket-id/encryption-key`
- Database and uploads: `/var/lib/pocket-id/`
- Unit: `/etc/systemd/system/pocket-id.service`
- Upgrade helper: `/usr/local/sbin/pocket-id-upgrade`
- SSH policy: `/etc/ssh/sshd_config.d/10-key-only.conf`

The encryption key and application data must be backed up together. Neither belongs in Git or Notion.

## Operations

```bash
systemctl status pocket-id
journalctl -u pocket-id -f
systemctl restart pocket-id
```

## Upgrade

Read the release notes and migration guide, then pass an explicit release tag:

```bash
sudo pocket-id-upgrade v2.16.0
```

The helper downloads the official Linux AMD64 binary and published checksums, verifies SHA-256 before stopping the service, installs into a versioned directory, and restores the previous binary if startup fails. Never use an unpinned `latest` URL in automation.

After an upgrade:

```bash
systemctl is-active pocket-id
journalctl -u pocket-id --since '-5 minutes'
curl --fail --silent https://auth.l3b.cc.cd/ >/dev/null
```

## Backup and recovery

Proxmox replication is availability, not backup. Maintain scheduled Proxmox backups and an application-consistent copy of `/var/lib/pocket-id` plus `/etc/pocket-id/encryption-key`. Retain local break-glass credentials for Proxmox and Kubernetes in case the identity provider is unavailable.
