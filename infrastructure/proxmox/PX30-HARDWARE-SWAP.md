# px30 hardware swap: preparation and return plan

## Owner decision and current state

Prepared on **2026-10-29**. The owner plans to replace the OptiPlex 7040 chassis
with a machine described as having an Intel i5-9500T. Its exact model, BIOS,
NIC and disk connectivity are not yet verified. Update the replacement's BIOS
using its own model-specific Dell package before transferring the existing disks.
Do not reuse the 7040/5060 firmware package based only on the processor generation.

**Wait until the owner confirms the replacement BIOS is ready.** No guest has
been migrated, no node drained, no HA maintenance enabled and no shutdown issued.
This is a temporary hardware swap retaining the existing px30 installation and
cluster identity, not node decommissioning or reinstallation. The replacement
hardware is not yet recorded as installed in the architecture inventory.

## Verified preflight

| Item | Observation on October 29 |
| --- | --- |
| Proxmox | 9.2.20, running kernel 7.0.14-19-pve; 3/3 nodes quorate |
| px30 pools | `rpool` and `data` ONLINE; no pool errors reported by `zpool status -x` |
| Boot drive | SK hynix PC611 NVMe, 256 GB advertised / 238.5 GiB visible |
| Data drive | Samsung MZ7KM960HMJP SATA SSD, 960 GB advertised / 894.3 GiB visible |
| Boot | UEFI, ZFS root; ESP configured with current and previous PVE kernels |
| NIC | Bridge uses `nic0`; installer .link file pins that name to the old motherboard MAC |
| px10 capacity | About 5.7 GiB available RAM at observation |
| px20 capacity | About 2.6 GiB available RAM at observation |
| Docker VM 204 | 16 GiB max and 16 GiB balloon minimum, not an 8–16 GiB configuration |
| HA replication | Five px30 service jobs successful with zero failures, every five minutes |
| Backups | October 29 backups present for guests 101, 102, 103, 105 and 107; presence is not a restore test |
| Kubernetes | All three Talos nodes Ready; VM203 is outside Proxmox HA |
| Longhorn | Installed v1.12.1; all six volumes healthy, two replicas each |
| PostgreSQL | Three ready instances; primary on k8s-202, px30's instance is a standby |

These are dated observations, not capacity or health guarantees for the swap.
Repeat the read-only report immediately before the maintenance window:

```bash
infrastructure/proxmox/px30-swap-preflight.sh
```

The script reports state only. A successful exit does not certify safe capacity
or replica placement. It does not read credential-bearing application configs.

## Intended temporary placement

| Guest | Normal host | Eligible maintenance target | Method/constraint |
| --- | --- | --- | --- |
| CT101 proxy | px30 | px20 | Replicated LXC; brief restart required |
| CT102 DNS | px30 | px10 | Replicated LXC; brief restart required |
| CT103 identity | px30 | px10 | Replicated LXC; brief restart required |
| CT105 S3 | px30 | px10 | Replicated data-pool LXC; brief restart required |
| VM107 Home Assistant | px30 | px20 | Replicated VM; attempt live migration after capacity check |
| VM203 k8s-203 | px30 | Keep its disks on px30 | Drain Kubernetes, then cleanly stop the VM for the swap |

Existing strict HA node-affinity rules already permit the listed service targets.
Do not add VM203 to HA or copy its 200 GiB boot and 500 GiB data disks to a second
physical host just for this short swap. Its Talos/Kubernetes identity and
Longhorn disk remain within the unchanged VM disks.

## Gates before evacuation

1. Confirm replacement BIOS is ready, RAM/disks physically fit, and local console
   access is available for first boot. Keep px10 and px20 online throughout.
2. Repeat preflight. Record actual guest demand and a supported two-host RAM plan.
   Current free RAM alone is insufficient for an unrestricted bulk migration.
   Check inside the guests before reducing any allocation; do not assume
   ballooning creates memory or silently reduce VM204 to 8 GiB. Preserve original
   allocations for restoration. If there is no safe capacity plan, stop here.
3. Capture fresh host/network/boot/guest configuration off-host. Check recent
   completed backups and replication timestamps. Existing five-minute replicas
   are asynchronous; abrupt loss can discard changes since the last sync.
   Planned migration must finish its final sync before the source is powered off.
4. In Kubernetes, identify workloads and volume engines/replicas on k8s-203.
   Keep the PostgreSQL primary on a surviving node; verify a current standby on
   the other surviving node. Respect CNPG and other PodDisruptionBudgets.
5. Before stopping VM203, disable Longhorn scheduling on k8s-203 and request
   replica eviction through its supported node controls. Wait until all volumes
   have two healthy replicas on k8s-201/k8s-202 and adequate remaining disk space.
   Record and later clear the temporary eviction flag. Do not delete its disks,
   node object, volumes, PVCs or Talos machine identity. If rebuilding cannot
   complete safely, leave the source running and resolve the blocker.
6. Cordon and drain k8s-203 using Kubernetes eviction, ignoring DaemonSets.
   Inspect emptyDir usage before accepting its deletion. Never bypass PDBs,
   force-delete database pods, or weaken Longhorn's last-replica protection just
   to complete the drain. Confirm service endpoints on the surviving nodes;
   single-replica/RWX workloads can need a short restart. A third strict
   anti-affinity replica may remain Pending during two-node operation.
7. Once ordinary workloads and volume engines have left k8s-203, shut down VM203
   cleanly. Preserve on-boot settings and all disks. Two surviving etcd members
   retain quorum but leave no margin for a second node outage.
8. Enable Proxmox HA maintenance on px30 only after the RAM and Kubernetes gates
   pass. The HA scheduler uses the existing affinity rules to evacuate the five
   service guests. Observe each move/final disk sync; verify DNS, proxy, OIDC,
   S3 data access and Home Assistant. LXC migration is not live migration.

From a surviving node, the maintenance commands are:

```bash
# Run only after the gates above pass and the owner is ready.
ssh px10 'ha-manager crm-command node-maintenance enable px30'
ssh px10 'ha-manager status'
```

HA maintenance covers HA-managed guests only. Check `qm list` and `pct list` on
px30 for **zero running guests**, not just the HA status. Also confirm no backup,
replication or migration task is still writing before issuing a normal shutdown.
Do not pull power to trigger failover. Do not remove px30 from Corosync or reduce
expected votes. Record any maintenance-related replication errors and recheck
all jobs after the node returns.

## Hardware transfer and first boot

Transfer both existing drives and the intended RAM. Keep any attached storage
needed by this node; verify actual devices instead of relying on an old cabling
inventory. Do not initialize, reinstall, format or recreate either ZFS pool.
Use compatible UEFI, SATA/AHCI and virtualization settings. A BIOS reset can
change these. Keep power stable and use the prepared local console.

The current mapping is:

```text
/usr/local/lib/systemd/network/50-pmx-nic0.link
  [Match] MACAddress=<old motherboard MAC>, Type=ether
  [Link] Name=nic0
/etc/network/interfaces
  vmbr0 -> bridge-ports nic0
```

The new NIC has a different MAC. Before relying on SSH, identify it at the local
console with `ip -br link` and `udevadm info`, and update the .link mapping to that
verified NIC. Retain a copy of the old mapping. Use native Proxmox interface
pinning where appropriate, inspect generated `.new` network files, and apply
only the reviewed changes. Do not guess the new MAC, delete the bridge, or
restart live networking on the old host during preparation.

The old UEFI boot entry belongs to the old motherboard's NVRAM. The disks contain
fallback EFI boot files, but the replacement firmware may need its own boot
selection/entry. Inspect the existing ESP if it does not boot; do not format it
or run `proxmox-boot-tool format`. Boot recovery must target the identified
existing EFI partition, never a guessed `/dev/sda` path.

Keeping the original boot filesystem retains px30's hostname/IP configuration,
Corosync membership, SSH keys, machine identity and Tailscale state. This supports
return as the same node, but does not guarantee working boot/NIC configuration.
Do not run the old and replacement installations simultaneously with the same
identity. Do not re-enroll Tailscale or join Proxmox as a new node unless evidence
shows that the existing state is missing and a recovery plan requires it.

## Return and acceptance

Keep HA maintenance enabled until the replacement has passed host checks.
VM203 may start via its existing on-boot configuration; keep its Kubernetes node
cordoned until validation is complete. Do not assume maintenance mode prevents
non-HA VM startup.

- Confirm actual model/CPU/BIOS and full RAM detection. Verify UEFI boot, both
  expected drives, original ZFS pools ONLINE, and existing guest disks present.
- Confirm `nic0`/vmbr0, expected IP/gateway/DNS and 1 Gb/s full-duplex link. Check
  errors, the e1000e mitigation and Tailscale GRO settings against the actual new
  NIC/driver; do not assume the old hardware workaround applies identically.
- Confirm Proxmox quorum 3/3, HA daemons, no failed critical units, Tailscale
  Running/online with its existing identity and the intended subnet advertisement.
- Start/verify VM203, Talos/etcd health and Kubernetes Ready. Clear Longhorn's
  temporary eviction request and restore node scheduling deliberately, then
  uncordon. Wait for healthy volumes, healthy PostgreSQL instances and expected
  application replicas/endpoints; check RWX consumers and singleton services.
- Disable px30 HA maintenance after stable host/guest validation. Proxmox tracks
  maintenance origin and can return services automatically; supervise each move,
  honor any intentional intervening relocation, and confirm final placement.
- Validate DNS resolution, proxy/TLS, Pocket ID login, S3 read/write, Home Assistant
  devices/camera, Homepage, OpenCode/Hermes, Supabase database/storage and external
  monitoring. Validate actual operations, not only an HTTP login page.
- Confirm replication direction and timestamps after migration/failback; retry
  maintenance-related failures only once the source and target are valid.
- Restore any temporary memory allocations; update actual hardware/placement in
  architecture inventory, rebuild/render/check diagrams, refresh docs, Notion
  and OpenViking, and commit/push the final implementation.

```bash
# Only after the return gates pass; run from a surviving node.
ssh px10 'ha-manager crm-command node-maintenance disable px30'
ssh px10 'ha-manager status; pvecm status'
```

## Recovery material and rollback

A mode-0600 configuration baseline is saved on **both px30 and px10** at:
`/root/px30-swap-20261029/config-baseline.tar.gz`.
Both copies were checksum-matched. It contains selected network/boot/cluster/
replication/guest configuration, not a full disk backup or Tailscale state export.
It is root-only, contains internal operational details and is not committed.
Refresh it before actual evacuation. Do not restore baseline guest configs over
newer migrated guest ownership, replication state or disk writes.

If the new chassis cannot boot or has unresolved hardware compatibility, keep
HA services on the surviving hosts, avoid changing their authoritative disks,
and power down the replacement cleanly before moving the same drives/RAM back
to the old chassis. Restore only the old NIC mapping if it was changed. Never
boot stale source guest disks independently after those guests have been writing
on another host. Return through normal cluster migration/reconciliation.

Sources: [Proxmox HA maintenance and shutdown behavior](https://github.com/proxmox/pve-docs/blob/master/ha-manager.adoc),
[Proxmox NIC pinning](https://github.com/proxmox/pve-docs/blob/master/pve-network.adoc),
[Proxmox bootloader recovery](https://github.com/proxmox/pve-docs/blob/master/system-booting.adoc),
[Longhorn node maintenance](https://longhorn.io/docs/1.13.0/maintenance/maintenance/).
The installed Longhorn is v1.12.1; verify version-specific controls again at execution.
