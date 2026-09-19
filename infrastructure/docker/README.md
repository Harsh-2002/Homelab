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

The data disk uses one GPT partition with an ext4 filesystem labeled `docker-data`. It mounts at `/srv/docker` by filesystem UUID. Docker has a systemd `RequiresMountsFor=/srv/docker` dependency, so it cannot silently start on the OS disk if the data filesystem is unavailable.

## Tracked configuration

- `daemon.json` → `/etc/docker/daemon.json`
- `10-data-root.conf` → `/etc/systemd/system/docker.service.d/10-data-root.conf`
- `fstab.fragment` → append to `/etc/fstab`

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

VM 204 is registered with Proxmox HA but does not yet have ZFS replication. Both disks are node-local, so HA cannot restart it on another node until replication and a matching strict node-affinity rule are configured. The intended target is `px10`.
