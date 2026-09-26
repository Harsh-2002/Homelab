#!/bin/sh
set -eu

backup_dir=/srv/PX/exports/dump
output_dir=/var/lib/prometheus/node-exporter
test -f /srv/PX/.store-volume
test -d "$backup_dir"
install -d -m 0755 "$output_dir"
tmp_file="$(mktemp "$output_dir/backups.prom.XXXXXX")"
trap 'rm -f "$tmp_file"' EXIT HUP INT TERM

{
  printf '# TYPE pve_backup_latest_timestamp_seconds gauge\n'
  for vmid in 100 101 102 103 104 105 204; do
    latest=0
    for archive in "$backup_dir"/vzdump-*-"$vmid"-*.zst; do
      test -f "$archive" || continue
      stem="${archive%.zst}"
      log_file="${stem%.*}.log"
      test -f "$log_file" || continue
      grep -q "Finished Backup of VM $vmid " "$log_file" || continue
      modified="$(stat -c %Y "$archive")"
      if test "$modified" -gt "$latest"; then latest="$modified"; fi
    done
    printf 'pve_backup_latest_timestamp_seconds{vmid="%s"} %s\n' "$vmid" "$latest"
  done
  printf 'pve_backup_inventory_timestamp_seconds %s\n' "$(date +%s)"
} > "$tmp_file"

chmod 0644 "$tmp_file"
mv -f "$tmp_file" "$output_dir/backups.prom"
trap - EXIT HUP INT TERM
