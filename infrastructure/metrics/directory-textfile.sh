#!/bin/bash
set -euo pipefail

root_dir="${1:?directory required}"
mountpoint -q "$root_dir"
output_dir=/var/lib/prometheus/node-exporter
install -d -m 0755 "$output_dir"
tmp_file="$(mktemp "$output_dir/directories.prom.XXXXXX")"
trap 'rm -f "$tmp_file"' EXIT

printf '# TYPE storage_directory_bytes gauge\n' > "$tmp_file"
while IFS= read -r -d '' entry; do
  size="$(du -s -x -B1 "$entry" | awk '{print $1}')"
  label="$(printf '%s' "$entry" | sed 's/\\/\\\\/g; s/"/\\"/g')"
  printf 'storage_directory_bytes{path="%s"} %s\n' "$label" "$size" >> "$tmp_file"
done < <(find "$root_dir" -mindepth 1 -maxdepth 1 -type d ! -name lost+found -print0)
printf 'storage_directory_inventory_timestamp_seconds %s\n' "$(date +%s)" >> "$tmp_file"
chmod 0644 "$tmp_file"
mv -f "$tmp_file" "$output_dir/directories.prom"
trap - EXIT
