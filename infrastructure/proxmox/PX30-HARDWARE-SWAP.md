# px30 hardware swap: preparation and return plan

## Current checkpoint: back on 7040, prepared for another attempt, October 30

The owner returned both existing drives to the old7040. SSH, three-node quorum,
UEFI boot and both ZFS pools were verified, followed by a successful controlled
reboot after the network repair. Current hardware reports OptiPlex7040,
i5-6500TE and16GiB RAM. The planned next machine is owner-described as a Dell
OptiPlex with an i5 ninth-generation CPU; its next boot must verify actual model,
CPU, RAM, firmware and device paths. Do not treat the attempted machine's identity
as proof of the next machine's specifications.

Preserved boot logs establish the earlier network failure: on the attempted
replacement (DMI OptiPlex5060, BIOS1.32.0), Intel e1000e LAN at PCI0000:00:1f.6
became `eno1`. The MAC-bound installer rule did not match, and ifupdown2 logged
`vmbr0: bridge port nic0 does not exist`. This is now confirmed, not speculation.

The last seven recorded replacement boots also show logind receiving a short
power-key event, then an orderly power-off. The owner explains those were manual
attempts to force power-off after the login display appeared to shut down while
the device stayed powered. Therefore these events do not establish a spontaneous
shutdown, faulty button, kernel panic or HA watchdog reset. The earlier display
behavior remains unproven. The watchdog multiplexer exited cleanly in the last
boot; do not disable HA fencing or ignore power keys as an assumed fix.

### Applied preparation

- `/etc/systemd/network/50-pmx-nic0.link` overrides the same-named vendor rule,
  matching the Intel PCH onboard PCI path instead of a motherboard MAC. The path
  was observed on both the7040 and attempted5060. Source: `px30-onboard-nic.link`.
  It preserves bridge port`nic0` and static host address. A different PCI path or
  multiple/replaced adapters require a reviewed rule; this is not universal NIC
  discovery or DHCP. No live interface trigger/down/up was issued.
- `/etc/initramfs-tools/hooks/px30-nic` embeds the override for early udev.
  Both installed kernel initramfs images were regenerated and synced to the ESP.
  Source: `px30-nic-initramfs-hook`. The old vendor rule remains for rollback.
- VM203 `onboot` is temporarily0 (restore1 after validated replacement return).
  It remains stopped. px30 stays in HA maintenance; evacuated services, paused
  replication jobs, Kubernetes cordon and Longhorn eviction remain unchanged.
- Protected config/state bundle copied to px10 with matching SHA256, under
  `/root/px30-swap-20261029/config-prepared-20261030.tar.gz`. Source bundle and
  previous-boot journal are under `/root/px30-swap-20261030/` on px30. This bundle
  includes Tailscale identity, is mode0600, and must never enter Git or memory.

Reproduce the rule installation only after verifying the target onboard PCI path:

```bash
scp infrastructure/proxmox/px30-onboard-nic.link px30:/etc/systemd/network/50-pmx-nic0.link
scp infrastructure/proxmox/px30-nic-initramfs-hook px30:/etc/initramfs-tools/hooks/px30-nic
ssh px30 'chmod 0644 /etc/systemd/network/50-pmx-nic0.link; chmod 0755 /etc/initramfs-tools/hooks/px30-nic; udevadm control --reload; update-initramfs -u -k all'
```

The controlled reboot returned with a new boot ID, the override selected,
`nic0`/vmbr0 and its original default route intact, both pools healthy, VM203
still stopped and three-node quorum restored. Machine ID and SSH host-key hash
matched their pre-reboot values; Tailscale state can legitimately change during
reconnection, so confirm its node identity/addresses and running connection
instead of requiring a byte-identical mutable state file. Services on px10/px20
were not restarted or failed back. Leave this host powered on for inspection;
use a normal shutdown and confirm it is off before another physical drive move.
Next replacement boot still needs SSH, NIC link, quorum, pools and stability
verification before any workload return.

Post-reboot endpoint checks: Home Assistant and aggregate Proxmox HTTPS200;
Homepage's per-card checks passed32/33 initially, including px30. Longhorn's
monitor request timed out once, then its VIP returned200 and three consecutive
checks through Homepage's actual handler returned200. Both UI replicas were
Ready, five attached volumes healthy and the stopped standby volume detached
with unknown robustness as expected. This does not certify every authenticated
application workflow or restore the missing third Kubernetes node.

## Original decision and evacuation record, October 29

Prepared on **2026-10-29**. The owner plans to replace the OptiPlex 7040 chassis
with a machine described as having an Intel i5-9500T. Its exact model, BIOS,
NIC and disk connectivity are not yet verified. Update the replacement's BIOS
using its own model-specific Dell package before transferring the existing disks.
Do not reuse the 7040/5060 firmware package based only on the processor generation.

**Evacuation authorized and completed on 2026-10-29.** The owner explicitly
requested starting after the earlier wait decision. All five service guests are
running on surviving hosts, VM203 is cleanly stopped, and px30 is in HA maintenance.
The owner subsequently authorized a normal shutdown. It was issued after repeating
the safety gates; px10/px20 retained quorum. Confirm the power light is off before removing disks.
This is a temporary hardware swap retaining the existing px30 installation and
cluster identity, not node decommissioning or reinstallation. The replacement
hardware is not yet recorded as installed in the architecture inventory.

## Replacement power-on / network investigation, later October 29

The owner powered on px10/px20 and reports the replacement px30 powered on.
The survivors are reachable and quorate with the evacuated services started.
px30 still does not answer at its static address or appear as a new SSH/Proxmox
endpoint in the LAN scan. A healthy boot/new NIC configuration is not verified.
Do not mistake the previous powered-off checkpoint for current physical state.
The new machine's exact model/RAM detection remain unverified; its i5-9500T is
owner-reported. The old 7040 is retained only as historical rollback inventory.

The Netgear GS110TPv3 is now identified. Owner confirms px30 cable on g7, with
1Gbps link but no learned MAC in the copied dynamic table. This establishes
physical link, not an alternate IP or a completed OS boot. See the verified
[port map, temporary management access and recovery limits](../network/NETGEAR-SWITCH.md).
No switch changes or permanent px30 repair were made. Existing maintenance,
paused-replication, Longhorn and supervised-return requirements still apply.

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
| VM107 Home Assistant | px30 | **px10 during this swap** | Live migration completed; temporary affinity and replica reseed below |
| VM203 k8s-203 | px30 | Keep its disks on px30 | Drain Kubernetes, then cleanly stop the VM for the swap |

Existing strict HA node-affinity rules already permit the listed service targets.
Do not add VM203 to HA or copy its 200 GiB boot and 500 GiB data disks to a second
physical host just for this short swap. Its Talos/Kubernetes identity and
Longhorn disk remain within the unchanged VM disks.

## Execution record and temporary settings

The final placement is CT101 on **px20**; CT102/103/105 and VM107 on **px10**.
VM203 remains on px30, stopped. There are zero running px30 guests, no active
Proxmox tasks on that host, healthy pools and no HA resource errors. The host is
in manual maintenance mode and was normally powered off after final safety checks. No node identity was removed.

Longhorn replica eviction completed before the Kubernetes drain. Every one of
the six volumes has two non-failed replicas on k8s-201/k8s-202; no assigned replica
remains on k8s-203. Its scheduling is disabled and evictionRequested=true.
Drain respected PDBs (including waiting for the instance-manager budget); no
force deletion or PDB bypass. VM203 shut down cleanly with task status OK.
PostgreSQL primary supabase-db-2 and standby supabase-db-3 remain ready, with the
standby streaming/quorum. The third instance is intentionally Pending while its
node is cordoned. Five volumes are attached/healthy; the stopped standby's volume
is detached/unknown with both surviving replicas retained. Do not label that
expected detached status a storage failure or pretend all three DB instances run.

Memory plan changed based on evidence: lowering VM204's balloon target to 12 GiB
reduced guest-visible RAM but did not reduce its host footprint. Its iGPU/VFIO VM
had approximately 16 GiB locked. The original 16 GiB minimum/maximum was restored
without restarting Docker. Instead VM100 on px10 temporarily has balloon=10240,
shares=0 and unchanged memory=12288. Original balloon=2048, shares omitted (native
1000 default). A memory check showed adequate guest headroom before reclaiming it.
Host pressure averages were zero at final checks; spare RAM remains limited.
Do not start additional large workloads while the cluster is on two hosts.

VM107's temporary node-affinity rule is px10:3,px30:2,px20:1 (strict), preserving
the original rule name. Its original rule was px30:2,px20:1. Live migration to the
previously non-replica host copied the disk through the native migration path and
completed successfully in 2m10s. That left replication job107-0 without a common
base with the old px20 replica. After confirming no px20 owner/config/process for
VM107, the two inactive old replica datasets were **renamed**, not destroyed:

```text
px20 rpool/data/px30-swap-vm107-disk0-before-20261029
px20 rpool/data/px30-swap-vm107-disk1-before-20261029
```

A fresh native job107-0 sync px10→px20 completed, followed by another successful
incremental sync; fail count is zero. Keep the renamed recovery datasets until
validated return, then remove only those confirmed obsolete copies. Do not touch
running VM107 volumes. Verify or seed the return destination before live failback,
and recheck common snapshots afterward instead of assuming multi-target lineage.

After successful final syncs, jobs targeting the soon-offline px30 were paused:
**101-0,102-0,103-0,104-0,105-0**. Jobs100-0,106-0,107-0,109-0,204-0 remain enabled
and healthy. This includes CT104's ordinary backup replica even though CT104 did
not move. Re-enable all five paused jobs when px30 is healthy and account for
native replication-direction reversal during failback. No jobs or backups were
deleted. Existing VMID-based nightly backups still include the moved guests.

Validation: Home Assistant authenticated API200; bulb/AC entities available and
camera reporting recording (no actuator commands sent); proxy/OpenCode200, OIDC
discovery200, AdGuard/Unbound/Caddy active, RustFS health200. Quick Share performed
an actual Cairn-backed upload and download with exact byte comparison; harmless
test object expires after one hour. Supabase Studio302, surviving PostgreSQL
replication streaming. External slate Uptime Kuma's original six monitors were
all UP after cutover, including private proxy, DNS and all physical host APIs.
No permanent monitors or notification edits were made. Endpoint/API checks do not
claim a fresh browser login to every application or an actuator/camera playback test.

Later, after the owner's px10/px20 restart, CT101 was running but Caddy failed
before its static LAN address was ready. Restored Caddy and its node exporter;
both now wait for ifupdown2 networking and retry failures automatically. See
[proxy boot RCA](../proxy/README.md#boot-time-outage-and-recovery-2026-10-29).
The recovered Home Assistant browser connected live and its authenticated API
returned200. Homepage backend/SSO routing worked and32/33 card monitors responded,
with px30 still unavailable. This failure was inside the evacuated proxy guest,
not evidence of missing VM migration. Guest HA alone is not application health.

Recovery bundle refreshed before evacuation on px30 and px10 at
`/root/px30-swap-20261029/config-before-evacuation.tar.gz`; checksums matched.
The existing disks, ZFS pools, all guest data and node membership were preserved.
Internal/public topology, SVG/Mermaid/PNG/PDF exports and live inventory now show
this temporary placement. Retain the 7040 hardware label until actual replacement
hardware is verified, then rebuild the final architecture after return.

### Mandatory restoration after the replacement returns

1. Validate host, NIC mapping, pools, quorum and Tailscale before releasing HA
   maintenance. VM203 has onboot=1 and may start automatically but remains cordoned.
2. Verify Talos/etcd/node readiness, clear Longhorn evictionRequested, restore its
   scheduling, then uncordon k8s-203. Wait for the third PostgreSQL instance and
   application/storage health. Preserve current two-replica data during this.
3. Re-enable jobs101-0 through105-0 that were paused above. Verify fresh syncs
   before using px30's replicas. Supervise HA failback and final disk ownership.
4. Restore VM107 affinity to px30:2,px20:1 as part of supervised return; its
   temporary preference for px10 will otherwise keep it there. Validate fresh
   replication from its final owner and remove the renamed old px20 copies only
   once their replacement and final service state are verified.
5. After services have left px10, restore VM100 balloon=2048 and remove its
   temporary shares setting (native auto-balloon shares default1000). Its maximum
   remains 12288. VM204 already has its original 16384/16384 settings.
6. Reconcile placement, HA/replication/backup state, clear temporary inventory
   maintenance metadata and compact layout as appropriate, validate services,
   rebuild all diagrams, refresh Notion/OpenViking and commit/push scoped work.
   This is temporary evacuation; do not delete px30 from the cluster or remove
   legitimate long-term HA/replication/backup rules as cleanup.

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
[Longhorn node maintenance](https://longhorn.io/docs/1.12.1/maintenance/maintenance/).
Longhorn node eviction/drain controls were verified against the installed v1.12.1 documentation during execution.
