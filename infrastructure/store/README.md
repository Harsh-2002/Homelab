# Store: PBS and SMB

`store` is VM 107 (`10.1.1.12`), normally on px10. It runs Proxmox Backup Server 4.2 and Samba. The PBS UI is private at `https://pbs.l3b.cc.cd`; SMB is `smb://smb.l3b.cc.cd/AV` (Windows: `\\smb.l3b.cc.cd\AV`). The cluster token and SMB credentials are in the HomeLab 1Password vault as `PBS API Token - PVE` and `Store SMB`. The PBS root PAM password remains the one the owner set during installation; it was not changed. Never put secrets in this repo.

## Storage

The Crucial X9 Pro 4 TB USB SSD (serial `2338E8C83CF2`) is passed through to VM 107. It has a GPT partition with an LVM VG named `external`:

| LV | Size | Filesystem | Mount | Purpose |
| --- | ---: | --- | --- | --- |
| `external/backup` | 1 TiB | ext4 | `/mnt/datastore/external` | PBS removable datastore `external` |
| `external/share` | 1 TiB | ext4 | `/srv/AV` | SMB share `/srv/AV` |

About 1.64 TiB remains unallocated in the VG for future expansion. The PBS filesystem UUID is `c21cf584-1056-4d9c-8d52-ba2c72d92379`; the SMB filesystem UUID is `2489f3c3-bbaa-4f4b-bdf5-69d240a6bdab`. Use UUIDs/LVM names, not `/dev/sdX`, when moving the SSD. Both filesystems have zero reserved blocks. Samba requires the SMB mount and stops if it disappears. The PBS datastore is configured as removable, bound to its backing-device UUID.

The SSD is **not replicated**. HA and Proxmox replication cover only VM 107's 100 GB OS disk on local ZFS. VM 107 has a strict HA node-affinity rule for px10 (preferred) and px20 (fallback), with replication every five minutes. px30 is excluded. After px10 fails, the VM may start on px20, but the PBS datastore and SMB share remain unavailable until the USB SSD is physically moved and passed through to VM 107 there. Do not treat this disk as its own backup.

## Backups

PVE storage ID `external` points to PBS at `10.1.1.12:8007` using token `pve@pbs!cluster`. The token has `DatastoreBackup` permission. The scheduled job `critical-to-pbs` runs at 01:00 IST daily, snapshot mode, for dev (100), proxy (101), DNS (102), auth (103), Beszel (104), s3 (105), and ctr (204). PBS job `daily-retention` prunes at 03:00 IST to seven daily and four weekly points; garbage collection runs at 04:00 IST. New backups are verified automatically, and job `monthly-recheck` runs Sundays at 05:00 IST to reverify snapshots older than 30 days. It excludes orva (106), store itself (107), and K8s/Longhorn VMs (201–203) to protect the 1 TiB capacity. CT 102's initial backup completed on 2026-09-23. Monitor datastore use before broadening scope. Back up important SMB files elsewhere; the same SSD cannot provide an independent copy.

## Recovery and checks

1. Attach the exact Crucial SSD to px10 or px20. Confirm its serial with `lsblk -o NAME,SERIAL,SIZE` before changing the VM's USB mapping. Never initialize or format it during recovery.
2. Ensure VM 107's `usb0` maps the SSD, then start/restart VM 107. The USB ID on px10 was `0634:5603`, but identify the device again after a move.
3. In `store`, check `lvs external`, `findmnt /mnt/datastore/external /srv/AV`, `proxmox-backup-manager datastore show external`, `systemctl status proxmox-backup-proxy smbd`, and `smbclient -L localhost -N` (listing may be denied without credentials). Mount `/srv/AV` with `systemctl start srv-AV.mount` if needed.
4. From a PVE node check `pvesm status` and `pvesm list external`. Test a guest restore before depending on a backup.

The PBS UI is private behind Caddy. The direct LAN service is `https://10.1.1.12:8007`. `store.l3b.cc.cd` and `smb.l3b.cc.cd` resolve directly to the VM, while `pbs.l3b.cc.cd` resolves to the proxy wildcard. Keep them distinct. Caddy's TLS upstream uses the PBS self-signed certificate; the client-facing wildcard certificate is Caddy's. SMB is not HTTP/TLS and does not pass through Caddy.

PBS has native Pocket ID OIDC realm `pocketid` and an explicitly authorized `iam.anuragvishwakarma@gmail.com@pocketid` administrator. Its OIDC client secret is in the `Pocket ID OIDC - pbs` 1Password item. The browser passkey callback still needs owner verification. `root@pam` and the PVE backup token remain unchanged. PVE storage `external` lets the Proxmox UI browse and restore PBS backups, but PVE and PBS remain separate administrative UIs and separate RBAC databases; sharing Pocket ID does not replicate local users.

Homepage's PBS statistics use the separate token-only `homepage@pbs!homepage` identity. Both the user and token have the read-only `Audit` role on `/`, and the secret is stored in `PBS API Token - Homepage` in 1Password plus the live `homepage-widgets` Kubernetes Secret. The Homepage chart pins the PBS server certificate for direct TLS-verified API access; update that public certificate in Git if PBS rotates it.

Samba is Debian 13's 4.22.11 package and negotiates SMB3 only (`SMB3_00` minimum, `SMB3` maximum), with signing and per-share SMB3 encryption required. This is native SMB encryption, not TLS. It binds only to loopback and `10.1.1.12`, not Tailscale interfaces. Sign in to `AV` as `iam.anuragvishwakarma@gmail.com`; `/etc/samba/user.map` maps that SMB login to the local `iam.anuragvishwakarma` account that owns `/srv/AV`. The `Store SMB` 1Password item holds the separate Samba `tdbsam` password, not a PAM or OIDC password. A test file was uploaded, downloaded, and removed successfully.

The ext4 filesystem's `lost+found` directory is for `fsck` recovery, not a recycle bin. Keep it on disk. Samba's `veto files = /lost+found/` hides and denies it through the `AV` share; `downloads` and `media` remain visible. Do not enable `delete veto files`.

VM 204 `ctr` mounts this share at `/mnt/AV` with SMB 3.1.1 encryption and a systemd automount. Its planned downloader and media paths are `/mnt/AV/downloads` and `/mnt/AV/media`; see `infrastructure/ctr/README.md`. This client mount does not create another copy of the data.

Config sources in this directory are the PBS apt source files, Samba config, and mount/systemd drop-in. The live PBS datastore, PVE storage, backup job, HA rule, and USB mapping are platform state, not generated from these files.
