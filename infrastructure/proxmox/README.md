# Proxmox hosts

All three Proxmox nodes use AdGuard Home as the primary resolver and Cloudflare as the availability fallback. The `l3b.cc.cd` search suffix expands short hostnames such as `px10` to `px10.l3b.cc.cd`. DNS is configured per node in `/etc/resolv.conf`; `systemd-resolved` is inactive.

Deploy the tracked resolver file to `px10`, `px20`, and `px30`:

```bash
scp infrastructure/proxmox/resolv.conf px10:/etc/resolv.conf
scp infrastructure/proxmox/resolv.conf px20:/etc/resolv.conf
scp infrastructure/proxmox/resolv.conf px30:/etc/resolv.conf
```

Validate private, public, and fallback resolution:

```bash
getent ahostsv4 px10.l3b.cc.cd
getent ahostsv4 github.com
dig @1.1.1.1 example.com A +short
```

## px20 spare USB SSD

The separate px10 256 GB USB SSD (serial `20260200000000001716`, ext4 UUID `a19cf10d-4e36-4e00-94ce-bacc9381b30b`) now backs the cluster-wide `ISO` CIFS storage via `store` CT 109. It is mounted at `/mnt/external/ISO` on px10, with the matching mount unit staged on px20 for manual USB failover. The former px10-only `iso-store` storage entry and `/etc/fstab` mount were removed after checking that no guest configuration referenced it. See [`../store/README.md`](../store/README.md). It is **not** the px20 spare disk below.

The 256 GB `CONSISTENT SSD S7 256GB` USB disk (serial `20260200000000001741`, ext4 partition UUID `6e73fae7-a244-4b6c-899d-5023b1305546`) is attached to px20 but intentionally **unmounted and unregistered**. On 2026-09-24, the empty `backup-store` directory-storage entry was removed from cluster storage configuration, its UUID mount was removed from px20 `/etc/fstab`, and the mountpoint was removed. The disk was not formatted, wiped, or physically detached; its ext4 filesystem and standard `dump`/`lost+found` directories remain on the disk. Native critical-guest backups now target the separate `PX` share on the Crucial SSD, not this spare.

Identify the disk by serial and UUID before any future use; `/dev/sdc` is not a stable name. Check with `lsblk -o NAME,MODEL,SERIAL,SIZE,FSTYPE,UUID,MOUNTPOINTS` on px20 and `pvesm status` on a cluster node. Do not assume the spare is another backup copy. To reuse it, decide its role first, then deliberately mount and register it; do not format it merely to make it visible.

## VM installer media

On 2026-09-26, all six VMs (100, 106, 201, 202, 203, 204) had `ide2: none,media=cdrom` and `ide2` in their boot order. No installer ISO was attached. The empty `ide2` devices were deleted from their configurations and boot order changed to `scsi0;net0`, preserving disk boot and network fallback. Proxmox keeps these changes in `[PENDING]` while the VMs run; they take effect at each VM's next planned restart. Do not reboot Kubernetes or service VMs merely to remove an already-empty optical drive. VM 106's separate `ide0` Cloud-Init drive remains attached because it provides guest configuration. LXC containers have no CD-ROM devices.

For model-specific firmware package mapping, the sequential USB update
procedure, validation gates, and the 2026-09-22 fwupd cleanup record, see
[`BIOS-UPGRADE.md`](BIOS-UPGRADE.md).

## Intel I219-V transmit-hang workaround

`px10` and `px20` use the same Intel I219-V revision 10 NIC (`8086:15bc`)
with the in-kernel `e1000e` driver. Both hosts have repeatedly logged
`Detected Hardware Unit Hang` during sustained bridged network transfers.
The NIC then stops transmitting, Corosync loses quorum, and Proxmox HA
correctly watchdog-fences the isolated node. The reboot is therefore the
consequence of the NIC failure, not the original fault.

The problem reproduced after the BIOS update and on kernels
`7.0.14-17-pve` and `7.0.14-19-pve`, so BIOS and kernel updates alone are not
a sufficient correction. `px30` has a different I219-LM revision and no
recorded hangs. On 2026-09-23 the owner chose the same conservative NIC
settings for `px30` for consistency; that host has an I219-LM with firmware
`0.8-4`, and applying the settings there does not mean its NIC is affected.
Applying EEE-off to px30 briefly renegotiated the link (about three seconds);
it returned at 1000 Mb/s full duplex, with all three cluster nodes quorate.

The persistent settings on all three nodes disable TSO, GSO, GRO, and
EEE while retaining checksum offload. The I219-V does advertise and enable
TSO and checksum offload; it is incorrect to say that this NIC lacks these
capabilities. GSO and GRO are Linux software aggregation features. EEE was
enabled but inactive before the change, so there is no evidence it caused
the observed incidents.
Deploy or restore it with:

```bash
scp infrastructure/proxmox/e1000e-stability.service px10:/etc/systemd/system/
scp infrastructure/proxmox/e1000e-stability.service px20:/etc/systemd/system/
scp infrastructure/proxmox/e1000e-stability.service px30:/etc/systemd/system/
ssh px10 'systemctl daemon-reload && systemctl enable --now e1000e-stability.service'
ssh px20 'systemctl daemon-reload && systemctl enable --now e1000e-stability.service'
ssh px30 'systemctl daemon-reload && systemctl enable --now e1000e-stability.service'
```

Validate the active state and counters:

```bash
ethtool -k nic0 | grep -E 'tcp-segmentation|generic-segmentation|generic-receive|tx-checksumming'
ethtool --show-eee nic0
ethtool -S nic0 | grep -E 'tx_timeout_count|tx_dma_failed|rx_dma_failed|tx_errors|rx_errors'
journalctl -k -g 'Hardware Unit Hang|NETDEV WATCHDOG|Reset adapter'
```

On 2026-09-23 an 8 GiB `ctr` (px20) to `dev` (px10) transfer sustained
approximately 115 MB/s after applying the mitigation. Both NICs retained
zero errors, DMA failures, and transmit timeouts. This proves wire-speed
operation for that test, not long-term stability or a confirmed root cause.

### Crash evidence and software-only investigation

At px20's 2026-09-23 00:19 IST incident, Corosync links dropped at
00:19:45. Starting at 00:19:46 the kernel reported `e1000e` transmit
hardware-unit hangs every two seconds: TX descriptor head `TDH=0x7c`
remained unchanged while the tail was `TDT=0xb4`. The HA watchdog expired
at 00:20:41 and the host rebooted. This sequence identifies a stalled NIC
transmit path as the immediate cause of network isolation and reboot; it
does **not** prove whether the underlying defect is silicon, firmware,
driver, or a load/thermal interaction. There were no thermal-throttle,
machine-check, or PCIe AER error messages in the previous boot. The SSD
reported 48°C shortly before the failure. Later live readings were about
77–78°C for the Cannon Lake PCH (120°C reported critical trip) and 63–64°C
for the CPU package; temperature was **not** recorded at the crash instant.
Do not label overheating as ruled out or claim a confirmed root cause.

The owner requires a software/firmware-only solution; do not propose or
install any additional NIC, USB adapter, or other hardware. Keep the
offload/EEE workaround active on all three nodes and watch for a
recurrence under real traffic. If it recurs, capture the full first hang
and preceding kernel log, driver/firmware version, offload state, NIC
counters, and contemporaneous PCH/CPU temperatures before selecting a
specific upstream patch or a controlled Proxmox-kernel comparison. Avoid
compiling an arbitrary older driver or applying a patch for a different
chipset just because it prints the same error.

- [Intel's e1000e driver guidance](https://www.intel.com/content/www/us/en/support/articles/000005480/ethernet-products.html)
  says I219 uses the in-kernel `e1000e` driver, and updates now go through
  upstream Linux. Installing Intel's old standalone driver is not a sound
  upgrade path.
- [Intel's historical transmit-hang patch](https://lists.osuosl.org/pipermail/intel-wired-lan/Week-of-Mon-20171023/010559.html)
  documents a DMA buffer overrun and reduces outstanding transmit requests
  for earlier SPT/KBL chipsets. Current [Linux source](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/intel/e1000e/netdev.c)
  applies that workaround only to `e1000_pch_spt`. The 5060's PCI ID
  `8086:15bc` maps to `board_pch_cnp`, so that particular patch cannot be
  assumed to fix these hosts. The identical log message does not establish
  the same underlying erratum.
- [Proxmox staff](https://forum.proxmox.com/threads/kernel-90070-981674-e1000e-0000-00-1f-6-eno2-detected-hardware-unit-hang.173143/)
  recommends disabling TSO/GSO for this failure class, but
  [other firsthand reports](https://forum.proxmox.com/threads/intel-nic-e1000e-hardware-unit-hang.106001/)
  show the hang can persist after offloads are disabled. Treat the current
  settings as a monitored mitigation.

There is currently no verified chipset-specific source patch that is safer
than the running in-kernel driver. A custom driver build is warranted only
after identifying and reviewing such a patch, then testing one node at a
time with a rollback kernel available.
