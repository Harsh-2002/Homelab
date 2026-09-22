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
