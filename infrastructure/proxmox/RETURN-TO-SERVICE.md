# Return to normal placement — 30 October 2026

**Superseding incident, 31 October:** see [incident and recovery](INCIDENT-2026-10-31.md). Workloads were restored again after the owner power-cycled the cluster. The earlier checks did not establish N+1 memory capacity: Docker failover to px10 was OOM-killed.

The owner returned all three hosts to service and authorized restoring the
pre-evacuation placement, replication and ordinary memory/HA settings, followed
by cleanup. px30 retains its original identity and drives in the verified
OptiPlex 5060 / i5-9400T / 32 GiB replacement.

| Host | Normal running guests |
| --- | --- |
| px10 | VM100 dev, CT104 observability, CT109 store, VM201 Talos |
| px20 | VM106 Orva, VM204 Docker, VM202 Talos |
| px30 | CT101 proxy, CT102 DNS, CT103 identity, CT105 S3, VM107 Home Assistant, VM203 Talos |

## Restoration

Validated new-kernel boot, quorum, pools, onboard NIC/offload policy and existing
Tailscale identity. Restored VM203 onboot=1, started it, verified etcd membership
and node readiness, cleared Longhorn node eviction and restored scheduling.
All three Kubernetes nodes are uncordoned. Existing two-replica volume policy
and three-instance PostgreSQL configuration remain in place.

Re-enabled the five paused Proxmox replication jobs and verified fresh native
syncs before releasing px30 HA maintenance. Restored VM107's strict affinity to
px30:2,px20:1. The HA scheduler returned containers through supported relocation
and Home Assistant through live migration. VM100 balloon minimum is again
2048 MiB with its temporary shares override removed; maximum remains12288 MiB.
VM204's original16384/16384 allocation is unchanged. No forced quorum, weakened
fencing, guest reinstall or application-data reset was used.

### Cluster peer DNS repair

After the full cluster restart, peer names absent from each host's /etc/hosts
were expanded through guest DNS into the wildcard proxy address. Replication
therefore attempted SSH to the proxy instead of the target host. Existing
local-host entries alone were insufficient.

Added all Corosync peer short names and their .local aliases to each host's
/etc/hosts using the actual ring0 addresses. Preserved unrelated entries and
DNS settings. This removes the boot-time dependency on the DNS guest for
cluster peer lookup. Cross-host resolution and subsequent native replication
were verified on all three hosts.

Reproduce or validate without printing credentials or hardcoding addresses:

```bash
ssh px10 'python3 - --apply' < infrastructure/proxmox/configure-cluster-hosts.py
ssh px20 'python3 - --apply' < infrastructure/proxmox/configure-cluster-hosts.py
ssh px30 'python3 - --apply' < infrastructure/proxmox/configure-cluster-hosts.py
```

The helper derives addresses from Corosync, preserves metadata, is idempotent,
and refuses conflicting existing peer mappings. Omit --apply for a dry run.

### Kubernetes and storage recovery

Full shutdown left terminated/Unknown Longhorn manager, CSI and instance-manager
containers on k8s-202. Deleted only the stale pods through ordinary Kubernetes
deletion so their existing controllers could recreate them. Longhorn reattached
volumes and rebuilt failed replicas through its normal controllers. No forced
pod deletion, manual replica-file removal or forced database promotion.

SQL validation then found a real gap missed by pod readiness: standby3 was in
recovery but had no live WAL receiver. Its logs repeatedly reported a required
WAL segment had already been removed during its long offline interval. Primary2
was writable and standby1 was streaming synchronously. Those gates and exact
PVC ownership were checked before retiring only the stale standby with the
matching official CNPG1.30.1 `destroy supabase-db 3` command. The temporary CLI
archive was SHA256-verified against the upstream release digest and removed
immediately after use; no global plugin install or new agent tool was added.
The operator cloned a fresh standby3 from the existing primary. Both standby1
and standby3 now report streaming/quorum directly in pg_stat_replication.

The old PVC used Retain, so its Released PV remained after the supported destroy.
After confirming both live streaming standbys and no current PVC references,
changed only that obsolete Released PV to Delete for native CSI cleanup. Its
Longhorn volume and PV are gone. Ordinary storage-class retention and current
PVCs are unchanged. All six current volumes are attached/healthy with two
running replicas each. No backups/PITR or weaker consistency settings were added.

Home Assistant briefly passed through px20 during HA return. Native replication
direction reversal left job107-0 pointing to px10, where its old disk lineage
had no common snapshot with the newly mirrored px30 disk. Created107-1 for the
intended px30→px20 replica and completed fresh seeding before retiring107-0
through native cleanup. Job numbers are identifiers;107-1 is the permanent
five-minute HAOS replication job. Do not resurrect107-0 or keep obsolete disks
as a second active replication plan.

## Cleanup and verification

All three hosts run7.0.14-26-pve with manager9.2.24. Obsolete kernels and unused
dependencies were purged through APT; only the active kernel remains. Removed
APT archives/index/binary caches and the completed one-time cleanup helpers,
units, timers and markers from the live hosts. Sources remain in Git for reuse.

Removed both renamed pre-swap VM107 datasets on px20 after verifying the new
107-1 snapshots, current guest ownership and authenticated Home Assistant API.
Native retirement of107-0 removed the obsolete px10 replica. Normalized all ten
replication descriptions and retained their five-minute schedules.

Removed the private px30-diagnostics capture/receiver scratch directory
(934031870 bytes of files), per-host px30-swap and package-maintenance scratch
bundles. Confirmed no temporary receiver/switch tunnel listeners or px10 switch
management alias remain. Native system/PVE journals, legitimate guest disks,
current replica datasets/managed snapshots and ordinary backups remain.

Also removed the old untracked Cilium CLI test namespaces cilium-test-ccnp1 and
cilium-test-ccnp2 (no PVCs) and the default-namespace lb-test deployment. They had
no repository/GitOps ownership and were test artifacts, not application services.

Authenticated Home Assistant API returned200 with144 entities. Local bulb and
camera were available. Both AC entities were unavailable: the owner confirms
the AC is switched off at mains; LocalThings remains loaded. The independent
SmartThings cloud entry reports a subscription quota and remains in setup_retry;
a reload did not clear it. No cloud subscriptions or appliance controls were
changed to mask that separate issue.

The earlier unsolicited power/reset cause remains unresolved. Successful warm
reboot tests, rack return and service checks do not establish its hardware or
firmware cause, or prove future failover behavior.


## Final acceptance

Three hosts are quorate with healthy local pools, active core PVE services and
all ten HA resources started on the normal hosts. All ten five-minute replication
jobs are enabled with zero failures after repeated post-return syncs. The final
VM107 replica is on px20; no old107-0 job, px10 VM107 volumes or renamed px20
migration copies remain. All three Talos nodes are Ready, schedulable and etcd
members; all Longhorn node/disk scheduling is restored with no eviction request.

All nine Argo CD applications are Synced/Healthy. CNPG reports three ready
instances on three nodes, with primary2 and two live streaming/quorum standbys.
Supabase's auth health and authenticated REST metadata endpoints return200;
all eleven Supabase Deployments have their desired ready replicas. Analytics,
Realtime and pooler completed supported rolling restarts after database recovery,
clearing cold-start backoff and distributing replacement pods across the nodes.

Home Assistant/OpenCode/Proxmox/OIDC endpoints respond, and HA's authenticated
API, physical-node sensors and camera snapshot are checked without actuator
commands. The original power/reset root cause remains unproven. The separate,
pre-existing gitea-mirror worker still restarts because its bind-mounted data
folder is unwritable; its unrelated application data/permissions were preserved.
Do not report every Docker application healthy or every appliance online.


### Node metric startup recovery

Final HA checks found11 restored/unavailable metric entities although every
exporter was up and the backend returned all27 series. Entity update calls
reported those CPU entities missing. Reloading the REST integration recovered
all27. Added per-sensor availability guards for missing/undefined/non-numeric
samples so startup gaps do not attempt to expose a non-numeric measurement.
Native config validation passed after correcting an indentation error caught
before loading; reloaded REST and verified all27 actual runtime entities.
Template API checks passed for valid, missing, undefined and NaN inputs. There
was no additional host/Core reboot or deliberate exporter outage test. A full
cold-start regression is therefore not claimed.


Operational references: [CNPG1.30.1 instance removal implementation](https://github.com/cloudnative-pg/cloudnative-pg/blob/v1.30.1/internal/cmd/plugin/destroy/destroy.go),
[Longhorn replica rebuilding](https://longhorn.io/docs/1.12.0/advanced-resources/rebuilding/),
and [Home Assistant REST sensor availability](https://www.home-assistant.io/integrations/sensor.rest/).
