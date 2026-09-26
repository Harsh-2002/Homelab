# Store: AV and PX

`store` is Debian 13 LXC 109 at `10.1.1.12`, normally on px10. It runs Samba 4.22.11 with 1 vCPU, 1 GiB RAM, and an 8 GiB `local-zfs` root disk. It uses the stock `debian-13-standard_13.6-1_amd64.tar.zst` template. The former PBS VM 107 and datastore were removed after all seven native backups and a test restore succeeded on 2026-09-26. This directory is the source of truth for Samba and the host mount units; the live CT, storage, HA, and backup-job objects are Proxmox state.

## External SSD and shares

The Crucial X9 Pro 4 TB USB SSD, serial `2338E8C83CF2`, has one LVM PV and VG `external`. There is no need to repartition or reformat the SSD for this migration. Mount the two existing ext4 LVs on the Proxmox host and bind them into the unprivileged CT:

| LV | UUID | Host mount | CT mount | SMB share |
| --- | --- | --- | --- | --- |
| `external/share`, ~1.64 TiB | `2489f3c3-bbaa-4f4b-bdf5-69d240a6bdab` | `/mnt/external/AV` | `/srv/AV` | `AV` |
| `external/backup`, 2 TiB | `c21cf584-1056-4d9c-8d52-ba2c72d92379` | `/mnt/external/PX` | `/srv/PX` | `PX` at `/srv/PX/exports` |

Install `mnt-external-AV.mount` and `mnt-external-PX.mount` on px10 and px20. Enable/start them only on the node holding the SSD. CT mount points use `replicate=0`; only the 8 GiB root disk is replicated to px20 every five minutes (`109-0`). HA node affinity `ct109-replica-nodes` is strict to px10/px20, preferring px10; automatic failback and rebalancing are disabled. The host directories alone are **not** the data volumes. Each volume has a `.store-volume` marker; `smbd-external.conf` must be installed as `/etc/systemd/system/smbd.service.d/external.conf` so Samba refuses to start unless both markers are visible inside the CT. Install `node-exporter-network.conf` at `/etc/systemd/system/prometheus-node-exporter.service.d/network.conf`. Both units wait for `networking.service` before binding to `10.1.1.12`; reboot verification confirmed ports 445 and 9100. Do not enable `systemd-networkd-wait-online` in this LXC: Proxmox configures eth0 via ifupdown2, and networkd reports it unmanaged. After a host restart, verify both mounts before relying on SMB. The SSD itself is not replicated, so after px10 fails it must be physically moved to px20 and the two mount units started there. Then restart CT 109 or `smbd` after confirming its bind mounts point to the real filesystems.

Both shares require SMB3 encryption and signing. They use the **same** Samba account: login `iam.anuragvishwakarma@gmail.com`, mapped to local `iam.anuragvishwakarma` (UID 1000). Its password remains in the existing `Store SMB` item in the HomeLab 1Password vault. No PAM or OIDC password is involved. On an unprivileged CT, UID 1000 maps to host UID 101000; the `AV` volume and `PX/exports` directory must keep matching ownership. The ext4 `lost+found` directory remains on disk but is hidden from the `AV` share.

Connect to `AV` using `smb://smb.l3b.cc.cd/AV` on macOS or `\\smb.l3b.cc.cd\AV` on Windows. `PX` is `smb://smb.l3b.cc.cd/PX` or `\\smb.l3b.cc.cd\PX`, intended for Proxmox backups only. `ctr` still mounts `AV` at `/mnt/AV` with its existing encrypted SMB 3.1.1 automount; its Motrix and Jellyfin paths remain unchanged. SMB is not HTTP and does not pass through Caddy.

## Proxmox native backups

Cluster storage ID `PX` is CIFS/SMB at `10.1.1.12`, share `PX`, `content backup`, SMB 3.1.1 with `seal`. The credential file is cluster-private `/etc/pve/priv/storage/PX.pw`; do not put it in Git or commands/logs. A single storage definition is available to px10, px20, and px30. The scheduled job `critical-to-px` uses snapshot mode, zstd, daily `02:00` Asia/Kolkata time, and `keep-last=1` for guests 100, 101, 102, 103, 104, 105, and 204. K8s/Longhorn VMs 201-203, orva 106, and store CT 109 are excluded. Native file backups are **full archives**, not PBS-style incremental transfers; ensure capacity for the current and replacement archive during rotation.

The `PX` share is served by CT 109, so using it as the only backup location for CT 109 creates a recovery dependency. Its root disk is replicated to px20, while this repo records the service configuration and 1Password holds its credential. The SSD is a single physical failure domain for both `AV` and `PX`; a VM backup on `PX` does not protect files stored in `AV` against SSD failure.

## Checks and recovery

1. On the node holding the SSD, confirm serial `2338E8C83CF2` with `lsblk -o NAME,SERIAL,SIZE,FSTYPE,MOUNTPOINTS` before mounting anything. Never initialize or format an unidentified disk.
2. Confirm `findmnt /mnt/external/AV` and `findmnt /mnt/external/PX`, both marker files, and the expected UUIDs. Start the two mount units if needed.
3. In CT 109, check `findmnt /srv/AV`, `findmnt /srv/PX`, `systemctl status smbd`, `testparm -s`, and `ss -ltnp | grep 445`. If the CT started before the host mounts, restart it after the real filesystems are mounted; merely mounting over the host paths does not repair existing bind mounts.
4. From all three PVE nodes, check `pvesm list PX` and `findmnt /mnt/pve/PX`. Verify a fresh `vzdump` archive and periodically restore a guest to a temporary ID. The Proxmox UI shows these archives under the `PX` storage; no separate PBS UI exists.

The old PBS datastore and VM were removed after backup and restore verification. The PBS-only 1Password items were moved to Recently Deleted (recoverable for the vault retention period). See repository history for the retired PBS setup; do not restore its OIDC client, Caddy route, Homepage widget, or credentials unless PBS is intentionally redeployed.
