# Proxmox package maintenance

## 30 October 2026

Owner requested current Proxmox/kernel/security packages on every node and removal
of obsolete kernels, unused dependencies and APT caches. px30 was already updated
and has been powered off for its rack move. Do not start it remotely or restore
evacuated workloads as part of package cleanup.

px10 and px20 were updated sequentially using refreshed configured Debian and
Proxmox repositories, `apt-get full-upgrade --no-remove`, existing conffile
preservation and independent low-priority systemd jobs. Plans contained no
removals (52 upgrades on px10, 50 on px20; one new kernel each). Proxmox manager
is now 9.2.24; kernel 7.0.14-26-pve is installed. They still run 7.0.14-19-pve
until the owner's next restart. No host or guest reboot was requested by the
updater. Firmware is pve-firmware 3.18-8. Existing NIC workaround settings remain.

px20 has limited free RAM while hosting evacuated services. A temporary
initramfs-tools conf.d override used supported gzip level 1 compression for
boot-image generation. It was removed after the successful upgrade; the generated
gzip initramfs remains valid. No swap or guest-memory changes were introduced.

Reviewed autoremove plans remove only obsolete 17-pve and unused ipvsadm/
libnl-genl-3-200. Downloaded .deb archives, APT binary caches and repository
index caches were removed after verifying zero outstanding upgrades. Future
package operations should refresh metadata with `apt-get update` first.
Kernel packages are removed through APT, never by deleting /boot or modules.
Diagnostic journals, recovery bundles, legitimate guest disks and data remain.

Validation: both upgrade jobs exited zero, dpkg audit was clean and a final
upgrade simulation showed no outstanding updates before removing index caches.
Core PVE services and two-node quorum remain active, local pools healthy, and all
ten HA-managed resources remain started on the evacuated placement. Kernel 26
is present on each configured UEFI ESP; the boot images include e1000e. Home
Assistant, OpenCode, Proxmox and OIDC discovery responded HTTP 200. This checks
update continuity, not a new host reboot or full application/failover exercise.
Cleanup candidate selection excludes current/newer kernels and meta packages;
live dry runs on both nodes correctly refuse removal while kernel 19 is running.

## Remove the former active kernel after restart

The tracked `prune-old-kernels.py` is installed as
`/usr/local/sbin/homelab-prune-old-kernels` on px10/px20, with the adjacent
`homelab-kernel-cleanup.service` and `.timer` in /etc/systemd/system.
The timer is enabled for next boot, not started during maintenance.

It waits three minutes after boot and retries every five minutes. Removal requires
kernel 26 or newer running, healthy local ZFS pools, quorum, core PVE services,
clean dpkg audit and installed running-kernel boot files. Only exact older
versioned kernel/header packages are candidates; active/newer kernels and meta
packages are excluded. A simulation rejects any additional dependency removal.
After successful removal/cache cleanup, it writes a protected completion marker
and disables its timer. It does not alter HA/watchdogs or force quorum.

Run without arguments for a gated dry run. Check results after restart:

```bash
uname -r
journalctl -u homelab-kernel-cleanup.service --no-pager
cat /var/lib/homelab-kernel-cleanup/completed
proxmox-boot-tool kernel list
dpkg --audit
```

If the node has no quorum (for example, peers remain off), cleanup waits rather
than changing cluster safety settings. The 19-pve package intentionally remains
while running. px30 old-kernel/cache cleanup is pending its next online session;
do not claim offline cleanup completed.

Protected per-host execution logs and package/config snapshots are in
`/root/package-maintenance-20261030`. The owner intends to shut px10/px20 down
manually. They are currently the two voting online nodes: guest shutdown and HA
coordination must precede a full-cluster shutdown. Do not perform unplanned
rolling reboots with px30 offline. Rebalance only after rack-return validation.
