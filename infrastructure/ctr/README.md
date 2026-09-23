# ctr SMB media mount

VM 204 `ctr` mounts Store's encrypted SMB3 share `//smb.l3b.cc.cd/AV` at `/mnt/AV`. This is the external Crucial SSD's `external/share` volume on `store`, not `ctr`'s local 500 GB `/data` disk. Motrix writes to `/mnt/AV/downloads`; Jellyfin indexes `/mnt/AV/media/movies` and `/mnt/AV/media/shows`. Application configuration and databases stay under `/data/apps`.

`cifs-utils` provides the client. The root-only `/etc/samba/credentials-av` file (mode `0600`) uses the existing `Store SMB` item from the HomeLab 1Password vault; never commit or print it. The tracked `mnt-AV.mount` pins SMB 3.1.1 and requires encryption (`seal`), with UID/GID 1000, no device files, setuid, or execution. `mnt-AV.automount` starts at boot and retries on access after an outage. The Docker service drop-in makes the automount ready before Docker starts, so a missing share cannot silently become a writable directory on the 50 GB OS disk. The automount does not make the physical SSD highly available: if `store` loses the USB disk, media stays unavailable until the disk is reattached.

Install the tracked unit files into `/etc/systemd/system/`, and `docker-av.conf` into `/etc/systemd/system/docker.service.d/`. After `systemctl daemon-reload`, enable and start `mnt-AV.automount`; do not enable `mnt-AV.mount` separately. Access `/mnt/AV` to trigger the mount. The credential file must exist first.

Check with:

```bash
ssh ctr 'systemctl is-enabled mnt-AV.automount; systemctl is-active mnt-AV.automount; findmnt /mnt/AV; ls -ld /mnt/AV/downloads /mnt/AV/media'
ssh ctr 'systemctl show docker.service -p Requires -p After | grep mnt-AV'
```

When deploying containers, bind the exact subdirectory, not the whole `/mnt` tree. Confirm `findmnt /mnt/AV` is `cifs` and `seal` is in the options before starting a downloader.
