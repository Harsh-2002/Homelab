#!/bin/sh
set -eu

directory=/var/lib/prometheus/node-exporter
path=/mnt/datastore/external
temp=$(mktemp "$directory/pbs.prom.XXXXXX")
trap 'rm -f "$temp"' EXIT HUP INT TERM

set -- $(stat -f -c '%S %b %a' "$path")
block_size=$1
blocks=$2
available=$3
printf 'pbs_datastore_size_bytes{datastore="external"} %s\n' "$((block_size * blocks))" > "$temp"
printf 'pbs_datastore_available_bytes{datastore="external"} %s\n' "$((block_size * available))" >> "$temp"
since=$(( $(date +%s) - 86400 ))
proxmox-backup-manager task list --all true --limit 1000 --output-format json |
  jq -r --argjson since "$since" '
    [.[] | select(.worker_type == "backup" and .starttime >= $since)] as $backups |
    "pbs_backup_tasks_24h{result=\"success\"} \($backups | map(select(.status == "OK")) | length)\n" +
    "pbs_backup_tasks_24h{result=\"failed\"} \($backups | map(select(.status != "OK" and .status != null)) | length)\n" +
    "pbs_backup_last_start_timestamp_seconds \($backups | map(.starttime) | max // 0)"
  ' >> "$temp"
chmod 644 "$temp"
mv "$temp" "$directory/pbs.prom"
