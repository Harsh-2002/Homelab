# px30 afternoon outage — 31 October 2026

## Current verified state, approximately 16:58 IST

px30 is unreachable by LAN SSH and Tailscale. Both surviving Proxmox nodes
retain quorum (two of three votes). The owner subsequently confirmed px30 is off and unplugged after it stopped
responding. That intervention does not establish the earlier failure trigger.

Peer Corosync journals show repeated disappearance and return, including
15:37:11 join,15:38:11 loss,15:44:54 join, and final15:45:07 link loss.
The15:45:13 membership excludes px30, with no leave message received.
These observations alone cannot distinguish reset, hang or network failure.
The CT101 migration task separately records remote PAM messages
"System is going down" at15:35:44–47. This establishes shutdown underway
in that earlier interval, not its initiating cause or the cause of every loss.
Do not attribute this incident to CPU generation, sleep, NIC offloads, or the
previous unsolicited power-key events without px30's own journal evidence.

## Failback and proxy recovery

HA had automatically attempted to move DNS, identity, S3 and Home Assistant back
to px30 when it briefly rejoined. Interrupted proxy CT101 migration left its
configuration on px30 with a migrate lock and HA in error. The proxy address
was not responding. Home Assistant recovered to px20 automatically; DNS,
identity and S3 recovered to px10.

The offline node-maintenance command was rejected by CRM as node not online.
Instead, the following existing strict HA node-affinity rules now exclude px30:

| Rule | Temporary eligible nodes | Restore only after deliberate acceptance |
| --- | --- | --- |
| ct101-replica-nodes | px20:1 | px20:1,px30:2 |
| ct102-replica-nodes | px10:1 | px10:1,px30:2 |
| ct103-replica-nodes | px10:1 | px10:1,px30:2 |
| ct104-replica-nodes | px10:2 | px10:2,px30:1 |
| ct105-replica-nodes | px10:1 | px10:1,px30:2 |
| vm107-replica-nodes | px20:1 | px20:1,px30:2 |

After prior CRM fencing acknowledgement and more than an hour without a
reachable px30, disabled CT101 to clear its error. Verified a complete local
ZFS filesystem on px20 (no receive-resume token), with15:37 replication snapshot.
Moved its existing cluster configuration to px20, cleared the stale migration
lock and returned desired HA state to started. No rollback, disk destruction,
reinstallation, quorum change or watchdog disable was performed.

At16:57:34 all ten HA resources reported started on px10/px20; proxy Caddy
was active and OpenCode and Home Assistant HTTPS both returned200.
This is replica recovery, not a claim that every application transaction
survived or that replicas on the unavailable host are current.

## Remaining degraded state

- VM203's host remains unreachable; k8s-203 is NotReady,SchedulingDisabled.
  k8s-201 and k8s-202 are Ready; no Pending pods were listed.
- Five Longhorn volumes report attached/healthy. One reports attaching/unknown.
- Two Supabase database pods are running; the standby on k8s-203 is terminating.
  No force deletion or storage detach was performed.
- px20 has approximately1GiB available RAM after proxy recovery, with no swap.
  Do not attempt to fit another16GiB Talos VM onto it.
- Replication toward px30 cannot complete while the node is unavailable.
- HA rule restoration and normal placement require an explicit stability
  acceptance; a brief reconnect must not trigger another automatic failback.

Next diagnosis requires px30's console/power state and retained host journals
when accessible. Keep the two quorate survivors running. Prior unresolved
power-key and abrupt-reset evidence remains in REBOOT-DIAGNOSTICS.md and the
morning incident document; it does not establish this outage's trigger.

## RAM identification follow-up

Live SMBIOS on px10 and px20 reports two16GB DDR4 modules per host, each
rated and configured at2666MT/s. Micron part16ATF2G64HZ-2G6E1 is present
on both; one px10 module has no populated part number. No retained record
verified px30 module speed. Do not copy the peer specification onto px30
or the old7040 module; inspect its label or dmidecode when available.
