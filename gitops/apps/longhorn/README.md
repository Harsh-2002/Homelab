# Longhorn

Longhorn `1.12.1` provides replicated Kubernetes block storage on the three Talos control-plane nodes. Each node contributes one dedicated 500 GiB disk mounted by Talos at `/var/mnt/longhorn`.

## Capacity and failure model

- Raw capacity: 1.5 TiB across three nodes.
- Default replica count: 2.
- Approximate usable capacity before safety headroom: 750 GiB.
- Minimum free space: 10% on each Longhorn disk.
- Failure tolerance: one replica or one node for a healthy two-replica volume.
- Data engine: V1 with `iscsi-tools`; V2 is disabled.
- Reclaim policy: `Retain` for normal workloads.

Replication is availability, not backup. Configure an external backup target before storing irreplaceable data.

## Access

- Private UI: `https://longhorn.l3b.cc.cd`
- LoadBalancer service: `10.1.1.172:80`
- Caddy supplies TLS, LAN access control, and authentication.

The initial Caddy password exists only in `~/.config/longhorn/initial-password` on `dev`. Remove that file after the password has been saved in the password manager. Never commit the password or its hash.

## Validation performed

The initial deployment passed these checks on 2026-09-20:

- all Longhorn managers, CSI components, engine images, and instance managers became Ready;
- a two-replica PVC provisioned and attached successfully;
- a 256 MiB payload retained its SHA-256 checksum across restart and failover;
- online filesystem expansion from 10 GiB to 15 GiB completed;
- a native snapshot was created and successfully reverted;
- abrupt loss of the workload node caused the pod to reschedule and attach from its surviving replica;
- the failed node returned and Longhorn restored the volume to two healthy replicas;
- the disposable test namespace, PV, volume, replicas, and snapshots were deleted afterward.

Kubernetes uses a five-minute default `NotReady` pod eviction toleration, so automatic workload rescheduling after hard node loss is not instantaneous.

## Routine checks

```bash
kubectl -n longhorn-system get pods -o wide
kubectl -n longhorn-system get nodes.longhorn.io
kubectl -n longhorn-system get volumes.longhorn.io
kubectl get storageclass longhorn
```

Before planned node maintenance, cordon and drain workloads, but exclude the Longhorn instance-manager pod because its disruption budget intentionally protects mounted replicas:

```bash
kubectl drain NODE \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --pod-selector='longhorn.io/component!=instance-manager'
```

After the node returns and is Ready:

```bash
kubectl uncordon NODE
```

Wait for affected volumes to report `healthy` before taking another storage node offline.

## Removal warning

Do not delete the Argo CD Application as an uninstall shortcut. Remove all Longhorn-backed workloads and volumes first, then follow Longhorn's documented uninstall-job workflow.
