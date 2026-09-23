# Docker host

VM 204 `ctr` is the standalone Docker host.

## Current state

| Setting | Value |
| --- | --- |
| Address | `10.1.1.4` |
| Placement | `px20` |
| Operating system | Debian 13 |
| CPU | 2 vCPU |
| Memory | 4–8 GiB ballooning |
| CPU model | `host` configured; pending next safe reboot |
| OS disk | 50 GiB `local-zfs` volume |
| Docker disk | 500 GiB `data` volume |
| Persistent data mount | `/data` |
| Docker metadata root | `/data/docker` |
| Containerd image root | `/data/containerd` |
| Docker network pool | `172.20.0.0/14`, allocated as `/24` networks |
| QEMU Guest Agent | installed and active |
| Hardware acceleration | Intel UHD 630 at `/dev/dri/renderD128` |
| Proxmox HA service | `vm:204`, started on `px20` |
| Replication | job `204-0`, `px20` → `px10`, every 5 minutes |
| HA placement | normally strict `vm204-replica-nodes`: `px20:2`, `px10:1` |

The data disk uses one GPT partition with an ext4 filesystem labeled `docker-data`. It mounts at `/data` by filesystem UUID. Docker stores engine metadata in `/data/docker`; Docker 29's containerd image store uses `/data/containerd`. Both services have a systemd `RequiresMountsFor=/data` dependency, so neither can silently start on the OS disk if the data filesystem is unavailable. Application data such as Frigate recordings can use separate paths below `/data`.

## Tracked configuration

- `daemon.json` → `/etc/docker/daemon.json`
- `10-data-root.conf` → `/etc/systemd/system/docker.service.d/10-data-root.conf`
- `containerd.toml` → `/etc/containerd/config.toml`
- `10-data-root-containerd.conf` → `/etc/systemd/system/containerd.service.d/10-data-root.conf`
- `fstab.fragment` → append to `/etc/fstab`
- `debian.sources` → `/etc/apt/sources.list.d/debian.sources`
- `vfio.conf` → `/etc/modprobe.d/vfio.conf` on `px10` and `px20`
- `vfio-modules.conf` → `/etc/modules-load.d/vfio.conf` on `px10` and `px20`

Deploy configuration changes with Docker stopped when moving data:

```bash
sudo dockerd --validate --config-file=/etc/docker/daemon.json
sudo findmnt --verify
sudo systemctl daemon-reload
sudo systemctl restart docker
```

Validate:

```bash
findmnt /data
docker info --format 'root={{.DockerRootDir}} driver={{.Driver}} logging={{.LoggingDriver}} live-restore={{.LiveRestoreEnabled}}'
containerd config dump | grep -E '^(root|state) ='
systemctl is-active docker qemu-guest-agent srv-docker.mount
```

Expected Docker configuration:

```plain text
root=/data/docker
containerd root=/data/containerd
driver=overlayfs
logging=local
live-restore=true
```

## Proxmox HA and replication

VM 204 is registered with Proxmox HA. Replication job `204-0` copies both Proxmox-managed ZFS volumes from `px20` to `px10` every five minutes. The strict node-affinity rule `vm204-replica-nodes` permits the VM to run only on those two nodes, preferring `px20` and using `px10` for recovery.

```plain text
node-affinity: vm204-replica-nodes
    nodes px10:1,px20:2
    resources vm:204
    strict 1
```

Validate from a Proxmox node:

```bash
pvesr status | grep -E '^(204-0|JobID)'
ha-manager rules config
ha-manager status
```

The initial full replication and a subsequent incremental replication were validated on 2026-09-20. The job reported `State OK` and `FailCount 0`; both target volumes and their replication snapshots were present on `px10`, while VM 204 and Docker remained active on `px20`.

This provides automatic restart on `px10` after a confirmed `px20` failure. Replication is asynchronous, so the recovery-point objective is approximately five minutes and the newest writes can be lost during an unplanned failure. Replication is not a backup and does not protect against deletion or corruption replicated to the target.

## Crucial X9 Pro external SSD

A 4 TB Crucial X9 Pro USB-C SSD (serial `2338E8C83CF2`) was temporarily passed through from `px20` to VM 204 as `usb0`. On 2026-09-23, the owner authorized formatting the entire SSD. It has a GPT with one 1 MiB-aligned ext4 partition, label `EX`, UUID `92aa5561-1194-4515-98a4-3a441e80338c`. The filesystem uses 4 KiB blocks, one inode per 64 KiB, and a 1% reserved-block allowance. The post-format mount, clean filesystem state, capacity, and write test were verified; only `lost+found` remained. It was never added to `/etc/fstab`.

Sequential `fio` tests on 2026-09-23 used a 32 GiB temporary file, 1 MiB blocks, direct I/O, and queue depth 16. Two-minute averages were 795 MB/s write and 909 MB/s read; five-minute averages were 814 MB/s write and 916 MB/s read. All four tests finished without I/O errors. The temporary file was removed, restoring about 3.6 TB free. These are single-VM, single-file sequential results, not a guarantee for small-file or concurrent workloads.

The following is the completed 2026-09 recovery history. **Formatting erased `/EX/linux-recovery.tar` and the entire extracted `/EX/RECOVERY` tree. There is no longer an external recovery copy on this SSD.** The original archive was the only whole-system copy known to this runbook.

Before formatting, the source archive was:

```plain text
/EX/linux-recovery.tar         502214830080 bytes, about 468 GiB
```

The 500 GiB `/data` destination had approximately 492 GiB usable, so the archive could not be copied there alongside a full extracted tree.

Because exFAT could not preserve Linux ownership, permissions, ACLs, extended attributes, hard links, and symlinks, the extracted tree on exFAT was a browsable convenience copy only. The original tar was the authoritative full-fidelity backup until the SSD was reformatted.

The first attempt created `/EX/linux-recovery.ext4`, but `px20` then lost its HA agent lock and self-rebooted while that new image was being initialized. After reboot, `fsck.exfat -n /dev/sdc2` reported the source filesystem clean, and `/EX/linux-recovery.tar` retained its exact size and modification timestamp. The incomplete 600 GiB image was later removed; it must not be treated as recovered data.

The full-fidelity ext4-image extraction was stopped cleanly and its partial image was later removed. A direct full extraction to exFAT was tested and stopped after measured throughput fell below 1 MiB/s in the old root filesystem's small-file tree. Recovery was limited to the two datasets that contain the required application state:

```plain text
2026-09-15/SSD
2026-09-15/rootfs/opt/SRVR
```

`recovery-extract.service` extracted the approximately 357.3 GB SSD dataset first. `recovery-srvr-extract.service` was ordered after it and extracted only `/opt/SRVR`, avoiding the rest of the old operating-system tree. Both wrote below the former `/EX/RECOVERY`. These extraction units are no longer installed. The tracked scripts and unit files are historical examples only; their source archive no longer exists.

Historical recovery snapshot from 2026-09-20:

```plain text
/EX mount:                    /dev/sdc2, exFAT, read-write during extraction
Source archive:               502214830080 bytes, original timestamp unchanged
Source readability:           archive header and initial entries readable
Incomplete ext4 image:        644245094400 bytes / 600 GiB physically allocated
SSD extraction:               completed successfully at 16:07:27 UTC
SRVR extraction:              active under recovery-srvr-extract.service
SRVR extraction start:        16:07:27 UTC
Loop-device attachment:       none
/EX usage:                    2.5 TiB used, 1.3 TiB available
/data capacity:               489 GiB free
Docker state:                 active; application containers are restored deliberately through Portainer
VM 204 state:                 running on px20
Replication job 204-0:        OK, FailCount 0
Temporary HA placement:       strict px20-only
```

The archive listing command ended with status 141 only because `head` intentionally closed the diagnostic pipe after the first 20 entries; it is not an archive-read failure. The backup error log contains ignored Unix socket entries, which are expected because tar archives cannot store live socket objects.

All required application data was restored to live services before the owner requested reformatting. Nextcloud's extracted copies were deleted separately after OpenCloud's 706 live files passed a full downloaded-content comparison. Formatting then removed every remaining extracted dataset and the original tar. No recovery or extraction unit is installed or running on `ctr`.

On 2026-09-23, after benchmarking, `/EX` was cleanly unmounted, its empty mount-point directory was removed, and `qm set 204 --delete usb0` removed the live USB passthrough. VM 204 remained running; its guest block-device list no longer showed the Crucial disk and `qm pending 204` showed no USB change awaiting reboot. The physical SSD may now be disconnected from `px20` without rebooting `ctr`.

If the SSD is attached again later, check its filesystem identity before mounting:

```bash
findmnt /EX
lsblk -f /dev/sdc
```

A temporary read-only ratarmount trial was stopped after its full-archive index projected roughly 70–85 minutes. `/RECOVERY` was never mounted. Its partial index, environment, packages, and empty directories were removed.

USB passthrough was node-local to `px20`. The disk is not a backup until a backup job and restore test exist.

## Intel iGPU passthrough

VM 204 has full passthrough of an Intel Coffee Lake UHD 630 for Frigate video decode. Both HA nodes have the same device at host PCI address `0000:00:02.0`, vendor/device ID `8086:3e92`, isolated in IOMMU group 0. Proxmox cluster resource mapping `intel-igpu` contains node-specific entries for `px20` and `px10`, and the VM uses:

```plain text
hostpci0: mapping=intel-igpu
```

Both hosts bind the iGPU to `vfio-pci` at boot. This makes the host consoles headless but preserves SSH and web management. The mapped resource allows HA cold recovery on either permitted node; PCI passthrough does not support ordinary live migration.

The Debian GenericCloud kernel did not contain `i915`. VM 204 therefore uses the normal Debian `linux-image-amd64` kernel together with `firmware-intel-graphics`, `intel-media-va-driver`, `vainfo`, and `intel-gpu-tools`. The obsolete cloud-kernel packages were removed after the normal kernel booted successfully.

Guest device:

```plain text
PCI device:    00:10.0 Intel UHD Graphics 630
Kernel driver: i915
Render node:   /dev/dri/renderD128
VA-API driver: Intel iHD 25.2.3
```

VA-API validation confirmed hardware decode support for H.264, HEVC/H.265 Main and Main10, VP8, VP9, MPEG-2, and JPEG. A complete HA-controlled stop/start also confirmed that the iGPU resets and reattaches cleanly.

Pass only the render node to Frigate:

```yaml
services:
  frigate:
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128
```

Validate:

```bash
lspci -nnk -s 00:10.0
ls -l /dev/dri
vainfo --display drm --device /dev/dri/renderD128
```
