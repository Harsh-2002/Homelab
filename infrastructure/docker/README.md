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

## Temporary Crucial X9 Pro import

A 4 TB Crucial X9 Pro USB-C SSD is temporarily passed through from `px20` to VM 204 as `usb0`. Its exFAT partition has label `EX`, UUID `72FF-5AED`, and is mounted read-only inside the VM at `/EX`. It is intentionally absent from `/etc/fstab`.

The source files are:

```plain text
/EX/linux-recovery.tar         502214830080 bytes, about 468 GiB
/EX/linux-recovery-errors.log  2335 bytes
```

The 500 GiB destination has approximately 492 GiB usable, so the archive fits but leaves little working space. Do not retain both the complete tar file and a full extracted copy on `/data`.

Because exFAT cannot preserve Linux ownership, permissions, ACLs, extended attributes, hard links, and symlinks, the recovery archive must not be extracted directly into an exFAT directory. `extract-recovery.sh` is retained as a reviewed extraction helper, but no extraction service is currently active.

The first attempt created `/EX/linux-recovery.ext4`, but `px20` then lost its HA agent lock and self-rebooted while that new image was being initialized. After reboot, `fsck.exfat -n /dev/sdc2` reported the source filesystem clean, and `/EX/linux-recovery.tar` retained its exact size and modification timestamp. `/EX` was remounted read-only. The 600 GiB image is incomplete and must not be mounted or treated as recovered data.

The full-fidelity ext4-image extraction was stopped cleanly and its partial image retained. A direct full extraction to exFAT was tested and stopped after measured throughput fell below 1 MiB/s in the old root filesystem's small-file tree. The optimized convenience extraction selects only `2026-09-15/SSD`, about 357.3 GB of application data, and writes it to `/EX/RECOVERY` on the Crucial SSD. The original tar remains untouched. Because `/EX` is exFAT, the convenience copy cannot preserve Linux ownership, permissions, ACLs, xattrs, hard links, or symlinks; the tar remains the authoritative full-fidelity backup and the partial ext4 image remains available as a fallback.

Status revalidated on 2026-09-20 after the node restart:

```plain text
/EX mount:                    /dev/sdc2, exFAT, read-only
Source archive:               502214830080 bytes, original timestamp unchanged
Source readability:           archive header and initial entries readable
Incomplete ext4 image:        644245094400 bytes / 600 GiB physically allocated
Extraction process/service:   none
Loop-device attachment:       none
/data capacity:               492 GiB free
/data contents:               empty Docker root plus lost+found only
Docker state:                 active, 0 containers, 0 images
VM 204 state:                 running on px20
Replication job 204-0:        OK, FailCount 0
Temporary HA placement:       strict px20-only
```

The archive listing command ended with status 141 only because `head` intentionally closed the diagnostic pipe after the first 20 entries; it is not an archive-read failure. The backup error log contains ignored Unix socket entries, which are expected because tar archives cannot store live socket objects. No recovery data has been extracted to `/data`.

A temporary read-only ratarmount trial was stopped after its full-archive index projected roughly 70–85 minutes, offering little advantage over selective extraction for this one-time recovery. `/RECOVERY` was never mounted. The partial 286 MB index, ratarmount environment, FUSE packages installed for the trial, and empty temporary directories were removed. The source tar remained read-only with its exact size and timestamp unchanged. Use `tar -tf` to locate required paths, then extract only explicitly selected paths into `/data`.

While the physical USB disk is present, the strict HA rule is temporarily restricted to `px20` so Proxmox cannot attempt recovery on `px10` without the device. After the import is complete:

```bash
# inside VM 204
sudo umount /EX

# on a Proxmox node
qm set 204 --delete usb0
ha-manager rules set node-affinity vm204-replica-nodes --nodes 'px20:2,px10:1'
```

Confirm `/EX` is unmounted before physically disconnecting the SSD. The tar file nearly fills the 500 GiB destination if copied intact, so do not retain both the archive and a full extracted copy on `/data` without checking space first.

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
