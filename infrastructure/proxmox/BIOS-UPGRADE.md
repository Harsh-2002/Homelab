# Dell BIOS maintenance

## Hardware and package mapping

| Node | Model | BIOS observed 2026-09-22 | Package/status |
|---|---|---:|---|
| `px10` | Dell OptiPlex 5060 | 1.4.2 | Upgrade with `OptiPlex_5060_1.32.0.exe` |
| `px20` | Dell OptiPlex 5060 | 1.2.17 | Upgrade with `OptiPlex_5060_1.32.0.exe` |
| `px30` | Dell OptiPlex 7040 | 1.24.0 | Already at the latest 7040 release; do not use the 5060 package |

BIOS packages are model-specific. The same verified 5060 package is used for
`px10` and `px20`; it must never be applied to `px30`.

## Approved USB package

Download only from Dell's OptiPlex 5060 BIOS release page. The approved files
for 1.32.0 and Dell-published SHA-256 values are:

```text
02cf30c0646550b69b95293232a8a628d56c512265d8d1930f4b61ff44b1c42b  OptiPlex_5060_1.32.0.exe
9c1cba4fb05eb279bcf3f256593fdebb6503f24c0945e251a9f17b86fb70af18  BIOS_IMG.rcv
```

The USB drive must be FAT32 but does not need to be bootable. Copy the BIOS
executable to its root. Retain `BIOS_IMG.rcv` as the matching recovery image;
do not select it during a normal update.

On 2026-09-22, the 4 GB USB drive previously used for the Proxmox installer
was erased and rebuilt as a single MBR/FAT32 volume named `BIOSUSB`. The BIOS
executable, recovery image, checksum manifest, and operator instructions were
copied to its root. Both Dell payloads passed SHA-256 verification when read
back from the USB, and the drive was safely ejected. It is ready for `px10`.

## Sequential procedure

Perform `px10` first, validate it completely, and then perform `px20`. Keep
workloads on their existing hosts and stop them cleanly in place. Do not flash
`px30` while 1.24.0 remains Dell's latest OptiPlex 7040 release.

For each 5060:

1. Record BIOS settings, boot entries, cluster and storage health, guest state,
   replication state, and passthrough configuration in an off-host recovery
   bundle.
2. Stop the node's guests cleanly and preserve their original HA requested
   states. Do not evacuate them to another node.
3. Keep the node and display on UPS power, insert the FAT32 USB drive, reboot,
   and press F12 at the Dell logo.
4. Select **BIOS Flash Update** under **Other Options**, select
   `OptiPlex_5060_1.32.0.exe`, and verify the displayed model and target version
   before starting.
5. Do not interrupt power or remove the USB while the firmware update and its
   automatic reboots are in progress.
6. After Proxmox returns, confirm BIOS 1.32.0 through SMBIOS. Validate RAM, NIC
   link, ZFS, IOMMU/GPU and USB passthrough, cluster quorum, HA, Kubernetes,
   Longhorn, and the application paths affected by the outage.
7. Restore the original guest and HA states on the same node and observe stable
   operation before proceeding to the next node.

## Cleanup completed before USB maintenance

On 2026-09-22, the failed `px10` fwupd attempt was disarmed and cleaned up. The
stale capsule, `fwupdx64.efi`, `Linux Firmware Updater` NVRAM entry, obsolete
`EspLocation=/mnt/esp` setting, and empty `/mnt/esp` directory were removed.
`Linux Boot Manager` remained the sole boot entry. A read-only remount verified
that the temporary firmware files were absent; `proxmox-boot-tool status`
reported the EFI System Partition healthy, cluster quorum remained 3/3, both
ZFS pools were online, and all original `px10` guests remained running.

The fwupd failure history is intentionally retained as evidence. No BIOS
setting was changed and no node was rebooted during cleanup.

## px10 result

On 2026-09-22, `px10` was upgraded through Dell's F12 BIOS Flash Update from
1.4.2 to 1.32.0. SMBIOS and the kernel boot log both reported 1.32.0 after the
flash. Linux Boot Manager remained the sole boot entry, the Proxmox EFI System
Partition remained healthy, both ZFS pools were online, cluster quorum was
3/3, and all Proxmox services recovered. The Intel NIC linked at 1 Gb/s full
duplex with no RX or TX errors, all 32 GiB RAM was present, VT-d and CPU
virtualization remained enabled, and the Intel GPU remained bound to
`vfio-pci`. Legacy Option ROMs, Attempt Legacy Boot, and Secure Boot remained
disabled, matching the pre-upgrade state.

VM 100, VM 201, and CT 104 recovered on `px10`; HA, replication, the Beszel
health endpoint, and the management endpoints were checked. All three
Kubernetes nodes were Ready, the Longhorn volume was attached and healthy, and
there were no non-running kube-system or Longhorn pods.

At the operator's request, `px10` was then shut down cleanly. Before host
shutdown, HA requested state for VM 100 and CT 104 was changed from `started`
to `stopped`, and VM 201 was shut down locally. All three guests were confirmed
stopped before powering off the host. `px20` and `px30` retained quorum with
two votes, and no `px10` workload relocated. After `px10` is powered on again,
restore VM 100 and CT 104 to HA requested state `started`, confirm VM 201 is
running, repeat endpoint and data-path validation, and complete the 30-minute
stability observation before beginning `px20`.

For operator-requested physical maintenance later on 2026-09-22, `px20` was
also shut down while `px10` remained off. VM 202 and VM 204 were confirmed
stopped before `px20` became unreachable, and HA entered shutdown mode without
relocating them. This intentionally leaves only `px30` online and therefore
without Proxmox cluster quorum. Do not force quorum or reduce expected votes.
Complete the physical work before applying the 5060 BIOS package to `px20`.
Bring both maintained nodes back normally afterward so the cluster regains
quorum before restoring HA and workload states.

## px20 result and px30 disposition

On 2026-09-22, `px20` was upgraded from BIOS 1.2.17 to 1.32.0 through Dell's
F12 BIOS Flash Update. SMBIOS confirmed 1.32.0 after boot. Linux Boot Manager
and the Proxmox EFI System Partition remained healthy; both ZFS pools were
online; all 32 GiB RAM was present; the NIC linked at 1 Gb/s full duplex; VT-d
remained active; and the Intel GPU remained bound to `vfio-pci`. No systemd
units were failed. VM 202 and VM 204 remained stopped. At the operator's
request, `px20` was then shut down again and confirmed unreachable.

Dell's live OptiPlex 7040 release page was rechecked on 2026-09-22 and still
lists 1.24.0 as the newest release. `px30` already runs 1.24.0, so it is marked
already current and must not be reflashed during this maintenance window.

## Final restored state

All three nodes were powered on and revalidated on 2026-09-22. Cluster quorum
returned to 3/3. VM 100 and CT 104 were first reassigned from their temporary
stopped HA locations back to `px10`, then their original requested state
`started` was restored. Final placement matched the pre-maintenance state and
all HA services were started. Every replication job completed with zero
failures.

Each physical NIC uses the in-kernel Intel `e1000e` driver and negotiated
1 Gb/s full duplex with link detected. All host ZFS pools were healthy and all
physical NVMe, SATA, and attached USB disks reported SMART `PASSED`. The
`px10` USB ISO store and `px20` USB backup store were mounted at their expected
Proxmox paths.

The available Proxmox update set was installed on all nodes: kernel
7.0.14-19, `libunbound8` 1.26.1-0+deb13u1, `proxmox-widget-toolkit` 5.2.10,
and `pve-docs` 9.2.12. All three EFI System Partitions contain kernel
7.0.14-19. A controlled rolling reboot was then completed in node order
`px10`, `px20`, `px30`, stopping each node's workloads in place and restoring
them before continuing. All three nodes now actively run 7.0.14-19 and its
updated in-kernel driver code.

VM 204 retained its Intel iGPU and 4 TB Crucial X9 Pro USB passthrough. The
external exFAT partition was manually mounted read-only at `/EX`, as intended;
it remains deliberately absent from `/etc/fstab`. The authoritative
`/EX/linux-recovery.tar` retained its exact documented size of 502214830080
bytes. A non-modifying `fsck.exfat -n` reported pre-existing duplicate filename
entries, so no repair or rename was performed.

All three Kubernetes nodes were Ready, the Longhorn volume was attached and
healthy, and no non-running pods were present. VM 204 containers and GPU access
were healthy. Beszel, Pocket ID, Immich, Registry, S3, Homepage, Argo CD,
Longhorn, Headlamp, Uptime Kuma, Frigate, the Proxmox cluster endpoint, and all
three node endpoints returned their expected success or authentication status.

After the rolling reboot, CT 104 replication had one expected failed attempt
while `px30` was offline; a targeted retry completed successfully and reset the
failure count to zero. Longhorn briefly reported degraded during replica
recovery and then returned to attached/healthy. Final state was quorum 3/3,
every HA service started on its original node, every replication job OK, every
Kubernetes node Ready, no non-running pods, all pools healthy, and all three
NICs linked at 1 Gb/s full duplex.
