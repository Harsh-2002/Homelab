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
| OS disk | 50 GiB `local-zfs` volume |
| Docker disk | 500 GiB `data` volume |
| Docker data root | `/srv/docker/data` |
| Docker network pool | `172.20.0.0/14`, allocated as `/24` networks |
| QEMU Guest Agent | installed and active |
| Hardware acceleration | Intel UHD 630 at `/dev/dri/renderD128` |
| Proxmox HA service | `vm:204`, started on `px20` |
| Replication | job `204-0`, `px20` → `px10`, every 5 minutes |
| HA placement | strict `vm204-replica-nodes`: `px20:2`, `px10:1` |

The data disk uses one GPT partition with an ext4 filesystem labeled `docker-data`. It mounts at `/srv/docker` by filesystem UUID. Docker has a systemd `RequiresMountsFor=/srv/docker` dependency, so it cannot silently start on the OS disk if the data filesystem is unavailable.

## Tracked configuration

- `daemon.json` → `/etc/docker/daemon.json`
- `10-data-root.conf` → `/etc/systemd/system/docker.service.d/10-data-root.conf`
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
findmnt /srv/docker
docker info --format 'root={{.DockerRootDir}} driver={{.Driver}} logging={{.LoggingDriver}} live-restore={{.LiveRestoreEnabled}}'
systemctl is-active docker qemu-guest-agent srv-docker.mount
```

Expected Docker configuration:

```plain text
root=/srv/docker/data
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
