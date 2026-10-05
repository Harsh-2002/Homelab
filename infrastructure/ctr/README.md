# ctr SMB media mount

Jellyfin-specific startup recovery (2026-10-05): install `jellyfin-mount-recovery.sh` as `/usr/local/sbin/jellyfin-mount-recovery` (0755), and its service/timer in `/etc/systemd/system` (0644). Run `systemctl daemon-reload` and `systemctl enable --now jellyfin-mount-recovery.timer`. This retries only the recorded AV mount-related Docker startup failure, checks real CIFS access, and preserves deliberate stops. The Docker automount dependency remains unchanged; it does not guarantee NAS availability at boot. An actual future reboot/outage recovery is not yet tested.

## VM memory: fixed 16 GiB with GPU passthrough

On 2026-09-30, the owner approved `memory: 16384` and `balloon: 16384` for VM 204. The balloon device remains enabled for statistics, but equal minimum/maximum means fixed allocation. This supersedes the earlier 8 GiB minimum / 16 GiB maximum policy. Leave the Kubernetes and Orva VM settings unchanged. There is no guest swap.

The Intel iGPU uses full PCI passthrough (`hostpci0: mapping=intel-igpu`). Inspection found ctr's QEMU process occupied about 16.04 GiB RSS with about 16.02 GiB locked, while the guest reported only 7.6 GiB usable under the old balloon target. VFIO must keep guest RAM mapped for device DMA: reducing guest-visible RAM did not return the corresponding memory to the host. Dynamic ballooning is therefore not an effective host-memory saving mechanism for this VM. See the [Proxmox staff explanation](https://forum.proxmox.com/threads/proxmox-balloon-does-not-seem-to-work-properly-in-pve8.134202/).

Applied persistently with `qm set 204 --balloon 16384` on px20. The configuration update alone left the live target at 8 GiB, so the existing balloon device was adjusted through the supported monitor API:

```bash
pvesh create /nodes/px20/qemu/204/monitor --command 'balloon 16384'
qm status 204 --verbose
```

No reboot was needed. Verification at about 12:20 UTC: actual balloon allocation 17179869184 bytes, guest total 15999 MiB with 8659 MiB available, host available about 3273 MiB, and unchanged QEMU RSS around 16.04 GiB. `/data` remained ext4, `/mnt/AV` remained CIFS, and running containers were not restarted by this change. The pre-existing `gitea-mirror` restart loop remains a separate unresolved issue; do not claim every container is healthy. Fixed RAM prevents this specific balloon restriction, not future OOM from unbounded application growth.

VM 204 `ctr` mounts Store's encrypted SMB3 share `//smb.l3b.cc.cd/AV` at `/mnt/AV`. This is the external Crucial SSD's `external/share` volume on `store`, not `ctr`'s local 500 GB `/data` disk. Motrix defaults to `/mnt/AV/downloads` and can also save under `/mnt/AV/media`; Jellyfin indexes `/mnt/AV/media/movies` and `/mnt/AV/media/shows`. Application configuration and databases stay under `/data/apps`. The mount intentionally uses the internal DNS hostname. `ctr`'s Proxmox cloud-init nameserver and Netplan configuration use only internal resolver `10.1.1.2`; a public fallback resolver returned the wildcard proxy address for this private SMB name during the 2026-09-27 outage. The checked-in `50-cloud-init.yaml` records the guest network settings.

`cifs-utils` provides the client. The root-only `/etc/samba/credentials-av` file (mode `0600`) uses the existing `Store SMB` item from the HomeLab 1Password vault; never commit or print it. The tracked `mnt-AV.mount` pins SMB 3.1.1 and requires encryption (`seal`), with UID/GID 1000, no device files, setuid, or execution. `mnt-AV.automount` starts at boot and retries on access after an outage. The Docker service drop-in makes the automount ready before Docker starts, so a missing share cannot silently become a writable directory on the 50 GB OS disk. The automount does not make the physical SSD highly available: if `store` loses the USB disk, media stays unavailable until the disk is reattached.

The AV mount also requires `nolease`. On 2026-09-29, the Linux CIFS client returned `EINVAL` when Jellyfin opened a Radarr hardlink while qBittorrent held the original filename open. Both names were readable locally on Store; a separate SMB connection and then a `nolease` mount read them correctly. This option disables SMB lease/oplock caching for this mount, with a potential throughput/latency cost, while preserving SMB encryption, permissions, and physical hardlinks. Do not replace it with `noserverino` or disable Radarr hardlinks without re-testing the actual concurrent-read workload. See [the media playback RCA](../arr/RCA-2026-09-29.md).

To apply a mount-option change, stop only the containers binding AV through Portainer (Jellyfin, Radarr, Sonarr, Bazarr, qBittorrent, Motrix), install the tracked mount unit, run `systemctl daemon-reload` and `systemctl restart mnt-AV.mount`, verify `findmnt -t cifs /mnt/AV`, then start those containers through Portainer. Do not leave containers running against old bind mounts during a remount. A service restart/remount was verified; a whole-VM reboot was not performed for this fix.

Install the tracked unit files into `/etc/systemd/system/`, and `docker-av.conf` into `/etc/systemd/system/docker.service.d/`. After `systemctl daemon-reload`, enable and start `mnt-AV.automount`; do not enable `mnt-AV.mount` separately. Access `/mnt/AV` to trigger the mount. The credential file must exist first.

Check with:

```bash
ssh ctr 'systemctl is-enabled mnt-AV.automount; systemctl is-active mnt-AV.automount; findmnt /mnt/AV; ls -ld /mnt/AV/downloads /mnt/AV/media'
ssh ctr 'systemctl show docker.service -p Requires -p After | grep mnt-AV'
```

When deploying containers, bind the exact subdirectory, not the whole `/mnt` tree. Confirm `findmnt /mnt/AV` is `cifs` and `seal` is in the options before starting a downloader.
