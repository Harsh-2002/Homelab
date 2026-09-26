# Store: AV, PX, and ISO

`store` is Debian 13 LXC 109 at `10.1.1.12`, normally on px10. It runs Samba 4.22.11 with 1 vCPU, 1 GiB RAM, and an 8 GiB `local-zfs` root disk. It uses the stock `debian-13-standard_13.6-1_amd64.tar.zst` template. The former PBS VM 107 and datastore were removed after all seven native backups and a test restore succeeded on 2026-09-26. This directory is the source of truth for Samba and the host mount units; the live CT, storage, HA, and backup-job objects are Proxmox state.

## External SSDs and shares

The Crucial X9 Pro 4 TB USB SSD, serial `2338E8C83CF2`, has one LVM PV and VG `external`. There is no need to repartition or reformat the SSD for this migration. Mount the two existing ext4 LVs on the Proxmox host and bind them into the unprivileged CT:

| LV | UUID | Host mount | CT mount | SMB share |
| --- | --- | --- | --- | --- |
| `external/share`, ~1.64 TiB | `2489f3c3-bbaa-4f4b-bdf5-69d240a6bdab` | `/mnt/external/AV` | `/srv/AV` | `AV` |
| `external/backup`, 2 TiB | `c21cf584-1056-4d9c-8d52-ba2c72d92379` | `/mnt/external/PX` | `/srv/PX` | `PX` at `/srv/PX/exports` |

The separate 256 GB `CONSISTENT SSD S7` USB disk on px10 (serial `20260200000000001716`, ext4 UUID `a19cf10d-4e36-4e00-94ce-bacc9381b30b`) is mounted at `/mnt/external/ISO`, bound to CT 109 at `/srv/ISO` as `mp2,replicate=0`, and served by the `ISO` SMB share. Its original filesystem and useful Omarchy ISO/Debian template were retained; it was not formatted. The obsolete PBS installer ISO was removed after verifying no guest configuration referenced the former `iso-store` storage ID. The old px10-only `iso-store` definition and empty mountpoint were removed. This is **not** px20's other 256 GB spare USB disk (serial ending `1741`).

Install `mnt-external-AV.mount`, `mnt-external-PX.mount`, and `mnt-external-ISO.mount` on px10 and px20. Enable/start them only on the node holding the corresponding SSD; all three are enabled on px10 and staged but disabled on px20. CT bind mounts use `replicate=0`; only the 8 GiB root disk is replicated to px20 every five minutes (`109-0`). HA node affinity `ct109-replica-nodes` is strict to px10/px20, preferring px10; automatic failback and rebalancing are disabled. The host directories alone are **not** the data volumes. Each volume has a `.store-volume` marker. `smbd-external.conf` must be installed as `/etc/systemd/system/smbd.service.d/external.conf`: Samba refuses to start unless AV/PX markers are present; the `ISO` share separately rejects connections when its marker is missing. Install `node-exporter-network.conf` at `/etc/systemd/system/prometheus-node-exporter.service.d/network.conf`. Both units wait for `networking.service` before binding to `10.1.1.12`; reboot verification confirmed ports 445 and 9100. Do not enable `systemd-networkd-wait-online` in this LXC: Proxmox configures eth0 via ifupdown2, and networkd reports it unmanaged. After px10 fails, **both USB SSDs** must be physically moved to px20 and all three mount units started there. Then restart CT 109 or `smbd` after confirming its bind mounts point to the real filesystems.

All three shares require SMB3 encryption and signing. They use the **same** Samba account: login `iam.anuragvishwakarma@gmail.com`, mapped to local `iam.anuragvishwakarma` (UID 1000). Its password remains in the existing `Store SMB` item in the HomeLab 1Password vault; that item has all three share URLs. No PAM or OIDC password is involved. On an unprivileged CT, UID 1000 maps to host UID 101000; the `AV` volume, `PX/exports`, and writable ISO template directories must keep matching ownership. The ext4 `lost+found` and marker files are hidden from the browseable shares.

Connect to `AV` using `smb://smb.l3b.cc.cd/AV` on macOS or `\\smb.l3b.cc.cd\AV` on Windows. `PX` is `smb://smb.l3b.cc.cd/PX` or `\\smb.l3b.cc.cd\PX`, intended for Proxmox backups only. `ISO` is `smb://smb.l3b.cc.cd/ISO` or `\\smb.l3b.cc.cd\ISO`. `ctr` still mounts `AV` at `/mnt/AV` with its existing encrypted SMB 3.1.1 automount; its Motrix and Jellyfin paths remain unchanged. SMB is not HTTP and does not pass through Caddy.

## Shared installation media

Cluster storage ID `ISO` is CIFS/SMB at `10.1.1.12`, share `ISO`, with only `iso,vztmpl` content, SMB 3.1.1, and `seal`. Its cluster-private credential file `/etc/pve/priv/storage/ISO.pw` contains the same Store SMB password; do not put it in Git. Proxmox stores ISO images in `template/iso/` and LXC templates in `template/cache/`. It is active on px10, px20, and px30; a px20 write was verified visible on px30. The former px10-only `iso-store` entry was removed after checking every current VM/CT configuration for references. Existing installed VMs boot their own disks and LXC containers boot their root filesystems; deleting the source installer/template does not delete an installed guest. An ISO still attached in a VM's CD-ROM configuration is different: check and update that reference before removing its storage. The ISO SSD is node-local hardware even though its SMB share is cluster-wide, and must be moved manually on host failure.

## Proxmox native backups

Cluster storage ID `PX` is CIFS/SMB at `10.1.1.12`, share `PX`, `content backup`, SMB 3.1.1 with `seal`. The credential file is cluster-private `/etc/pve/priv/storage/PX.pw`; do not put it in Git or commands/logs. A single storage definition is available to px10, px20, and px30. The scheduled job `critical-to-px` uses snapshot mode, zstd, daily `02:00` Asia/Kolkata time, and `keep-last=1` for guests 100, 101, 102, 103, 104, 105, and 204. K8s/Longhorn VMs 201-203, orva 106, and store CT 109 are excluded. Native file backups are **full archives**, not PBS-style incremental transfers; ensure capacity for the current and replacement archive during rotation.

The `PX` share is served by CT 109, so using it as the only backup location for CT 109 creates a recovery dependency. Its root disk is replicated to px20, while this repo records the service configuration and 1Password holds its credential. The SSD is a single physical failure domain for both `AV` and `PX`; a VM backup on `PX` does not protect files stored in `AV` against SSD failure.

## Checks and recovery

1. On the node holding the SSDs, confirm serials `2338E8C83CF2` and `20260200000000001716` with `lsblk -o NAME,SERIAL,SIZE,FSTYPE,UUID,MOUNTPOINTS` before mounting anything. Never initialize or format an unidentified disk.
2. Confirm `findmnt /mnt/external/AV`, `findmnt /mnt/external/PX`, and `findmnt /mnt/external/ISO`, all three marker files, and the expected UUIDs. Start the matching mount units if needed.
3. In CT 109, check `findmnt /srv/AV`, `findmnt /srv/PX`, `findmnt /srv/ISO`, `systemctl status smbd`, `testparm -s`, and `ss -ltnp | grep 445`. If the CT started before the host mounts, restart it after the real filesystems are mounted; merely mounting over the host paths does not repair existing bind mounts.
4. From all three PVE nodes, check `pvesm list PX`, `pvesm list ISO`, `findmnt /mnt/pve/PX`, and `findmnt /mnt/pve/ISO`. Verify a fresh `vzdump` archive and periodically restore a guest to a temporary ID. The Proxmox UI shows backups under `PX` and installation media under `ISO`.

The old PBS datastore and VM were removed after backup and restore verification. The PBS-only 1Password items were moved to Recently Deleted (recoverable for the vault retention period). See repository history for the retired PBS setup; do not restore its OIDC client, Caddy route, Homepage widget, or credentials unless PBS is intentionally redeployed.
