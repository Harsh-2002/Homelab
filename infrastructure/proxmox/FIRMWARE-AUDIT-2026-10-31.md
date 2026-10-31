# Driver and firmware audit — 31 October 2026

Owner requested available driver/firmware updates across px10, px20 and px30,
with permission to reboot nodes sequentially if necessary. Refreshed APT metadata
and reviewed full-upgrade plans on all three: zero upgrades, removals or held-back
updates. No new kernel/driver/microcode payload was available to activate.

| Component | px10 | px20 | px30 |
| --- | --- | --- | --- |
| Live model | OptiPlex5060 | OptiPlex5060 | OptiPlex5060 replacement |
| BIOS | 1.32.0 | 1.32.0 | 1.32.0 |
| Running kernel / NIC driver version | 7.0.14-26-pve | 7.0.14-26-pve | 7.0.14-26-pve |
| Driver / onboard firmware | e1000e / 0.5-4 | e1000e / 0.5-4 | e1000e / 0.5-4 |
| pve-firmware | 3.18-8 | 3.18-8 | 3.18-8 |
| intel-microcode package | 3.20251111.1~deb13u1 | 3.20251111.1~deb13u1 | 3.20251111.1~deb13u1 |
| Active CPU microcode | 0xfa | 0xfa | 0xfa |
| NVMe model | Micron2400 | Samsung MZVLQ512HALU-000H1 | SK hynix PC611 |
| NVMe firmware | V3MA001 | HPS4NFXV | 11002111 |
| SATA model | XF1230-1A1920 | XF1230-1A1920 | Samsung MZ7KM960HMJP-00005 |
| SATA firmware | ST200354 | ST200354 | GXM5104Q |

Dell's published [OptiPlex5060 BIOS release](https://www.dell.com/support/home/en-us/drivers/driversdetails?driverid=npkrw)
matches the installed1.32.0. Refreshed LVFS catalogs on all three hosts offered
no matching newer BIOS, onboard NIC or SSD firmware. Catalog coverage is limited;
absence of an offer does not establish that every OEM-specific SSD firmware is
the latest available anywhere. No generic Intel NVM image, cross-model disk
firmware, out-of-tree driver or forced/downgrade payload was used.

fwupd2.0.20-1~deb13u1+pmx1 was already installed on px10. Installed the same
Proxmox-provided audit tool with no recommended extras on px20, then px30
(22 new packages each, no upgrades/removals). Only catalog refresh and device/
update inspection were run; no `fwupdmgr update` or capsule staging. No ESP mount,
new boot entry, UEFI variable change or BIOS flash was performed. The historical
failed px10 remote BIOS handoff was not repeated.

## Remaining Secure Boot database offers

These are deliberately recorded separately from drivers/device firmware:

- px10: UEFI dbx20100507 → catalog20260707.
- px20 and px30: UEFI dbx20160809 → catalog20260402; KEK CA2011 →2023;
  UEFI CA2011 →2023.

Secure Boot is currently disabled on all three hosts (EFI SecureBoot value0).
These offers remain unapplied. They change Secure Boot trust/revocation data,
not the NIC driver or the observed power-key behavior. A later Secure Boot
maintenance operation must check actual ESP executables, boot/recovery media and
fwupd's compatibility gates before applying them. Do not claim “all firmware
updated” from this audit or bypass an ESP/revocation refusal.

## Activation, cleanup and health

All nodes already run their sole retained kernel26-pve; no package reboot marker
is present. The active microcode is0xfa on each CPU. No reboot was needed or
performed for this audit. Proxmox [microcode documentation](https://github.com/proxmox/pve-docs/blob/master/firmware-updates.adoc)
requires rebooting when a new early microcode payload needs activation; there
was no new payload here.

All links remain1Gbps/full duplex, TSO/GSO/GRO and EEE disabled as intended.
dpkg audit is clean; autoremove simulations have no candidates. APT archives,
binary caches and refreshed package-index caches were cleared after validation.
Native journals, running kernel and required firmware-tool dependencies remain.
Cluster/service recovery checks are recorded in the incident report. This audit
does not identify or fix px20's abrupt loss or px30's unsolicited power events.
