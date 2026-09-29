# Home Assistant OS

Home Assistant OS 18.3 is installed as Proxmox VM 107 (`haos`) on px30. The official `haos_ova-18.3.qcow2.xz` KVM image was downloaded directly on px30, checked against the release's SHA-256 digest, decompressed, validated with `qemu-img check`, and imported to `local-zfs:vm-107-disk-1`. The source download and QCOW2 staging directory were removed after the independent ZFS disk was verified.

Current VM configuration: OVMF with the `4m` EFI vars type and no pre-enrolled Secure Boot keys, one socket with two vCPUs, fixed 4 GiB RAM (`balloon: 0`), VirtIO NIC on `vmbr0`, VirtIO SCSI single controller, `scsi0` on local-zfs with discard, SSD and I/O thread enabled, and boot order `scsi0`. The imported disk was expanded from its 32 GiB image default to **40 GiB** at the owner's request; Proxmox reports the ZFS zvol at 40 GiB. Home Assistant OS can expand its guest data partition after a boot with the larger disk. The empty virtual CD-ROM was removed. VM 107 was started and is running on px30.

The owner has no physical Zigbee, Thread, Z-Wave or other radio passthrough planned. Home Assistant OS in a dedicated VM was chosen over Home Assistant Container because the supported HAOS/Supervisor installation manages its own core, OS and apps and preserves the option to move the VM between nodes. No VM boot ISO is needed; HAOS is imported as a prepared KVM disk.

## Access and availability

- LAN IP: `10.1.1.13/24` (static, gateway `10.1.1.1`). HAOS initially received temporary DHCP address `10.1.1.231`; after the owner configured its static address, the UI responded at `http://10.1.1.13/` on 2026-09-29. Port 8123 redirects to port 80 on this image. Port 4357 is only the HAOS Observer page, not the setup UI; it reported Supervisor connected, supported and healthy.
- The owner completed initial onboarding and created an account. The Proxmox QEMU guest agent responds to `qm guest cmd 107 ping`. Home Assistant's HTTP settings trust `X-Forwarded-For` only from Caddy `10.1.1.3/32`; the HA configuration check succeeded.
- Private HTTPS URL: `https://home.l3b.cc.cd`. The existing wildcard DNS resolves it to Caddy `10.1.1.3`, which proxies to `10.1.1.13:80`. Caddy applies the private LAN/Tailscale source policy, and Home Assistant retains its native login. No public Cloudflare record was created. Validated from `dev`: HTTPS root 200, unauthenticated `/api/` 401, WebSocket `/api/websocket` 101 with `auth_required`.
- Proxmox HA resource `vm:107` is started on px30. ZFS replication job `107-0` sends both VM disks from px30 to px20 every five minutes. The initial sync completed successfully on 2026-09-29, with zero failures and both disks verified on px20.
- Strict node-affinity rule `vm107-replica-nodes` prefers px30 and permits px20. HA must not choose px10 because it has no VM 107 replica. A real node-failure/failover test has not yet been performed. Replication is asynchronous, so up to the interval plus any replication lag may be lost in a sudden failure.
- The existing `critical-to-backup` job now includes VM 107. It runs daily at 02:00 to the `BACKUP` SMB storage, uses zstd snapshot backup and keeps the latest backup only. The first scheduled backup has not yet run. Backup is separate from replication and protects against deletion or bad configuration.

## Next steps

- Add monitoring for the private HTTPS URL. Do not create a public DNS record for this hostname.
- Connect Hermes to Home Assistant only after onboarding. Use a dedicated, scoped Home Assistant long-lived access token and keep it in 1Password, not in this repository.
- Test HA relocation to px20 during a planned maintenance window; do not force a host failure merely to validate it.

Official references: [Home Assistant Linux installation](https://www.home-assistant.io/installation/linux/), [Proxmox VM disk import](https://pve.proxmox.com/pve-docs/qm.html).
