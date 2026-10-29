#!/usr/bin/env bash
# Read-only report. It does not migrate, drain, stop, or modify any workload.
set -euo pipefail
for host in px10 px20 px30; do
  printf '\n%s\n' "=== $host ==="
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$host" 'set -e
    hostname
    pveversion
    free -h
    zpool list -o name,size,alloc,free,health
    tailscale version | head -1
    tailscale status --json | python3 -c '\''import json,sys; d=json.load(sys.stdin); print({"tailscale":d["BackendState"],"online":d["Self"]["Online"]})'\''
    qm list
    pct list
  '
done
ssh -o BatchMode=yes px30 'set -e
  pvecm status
  ha-manager status
  pvesr status
  proxmox-boot-tool status
  lsblk -dn -o NAME,SIZE,MODEL
  ip -br link show nic0
  cat /usr/local/lib/systemd/network/50-pmx-nic0.link
'
kubectl get nodes -o wide
kubectl top nodes
kubectl get pdb -A
kubectl get pods -A --field-selector spec.nodeName=k8s-203 -o wide
kubectl -n longhorn-system get volumes.longhorn.io \
  -o custom-columns=NAME:.metadata.name,STATE:.status.state,ROBUSTNESS:.status.robustness,NODE:.status.currentNodeID,REPLICAS:.spec.numberOfReplicas
kubectl -n supabase-prod get clusters.postgresql.cnpg.io supabase-db -o json |
  python3 -c 'import json,sys; s=json.load(sys.stdin)["status"]; print({k:s.get(k) for k in ["currentPrimary","targetPrimary","readyInstances","instances","phase"]})'
printf '\n%s\n' 'Report complete. This is not an automatic authorization or readiness verdict. Review capacity, replicas, PDBs and service checks in PX30-HARDWARE-SWAP.md before acting.'
