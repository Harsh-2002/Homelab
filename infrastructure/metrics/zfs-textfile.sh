#!/bin/sh
set -eu

output_dir=/var/lib/prometheus/node-exporter
install -d -m 0755 "$output_dir"
tmp_file="$(mktemp "$output_dir/zfs.prom.XXXXXX")"
trap 'rm -f "$tmp_file"' EXIT HUP INT TERM

{
  printf '# TYPE zfs_dataset_used_bytes gauge\n'
  printf '# TYPE zfs_dataset_referenced_bytes gauge\n'
  printf '# TYPE zfs_dataset_available_bytes gauge\n'
  zfs list -Hp -o name,used,referenced,available | awk -F '\t' '
    { name=$1; gsub(/\\/, "\\\\", name); gsub(/"/, "\\\"", name);
      printf "zfs_dataset_used_bytes{dataset=\"%s\"} %s\n", name, $2;
      printf "zfs_dataset_referenced_bytes{dataset=\"%s\"} %s\n", name, $3;
      printf "zfs_dataset_available_bytes{dataset=\"%s\"} %s\n", name, $4; }'
  printf '# TYPE zfs_pool_size_bytes gauge\n'
  printf '# TYPE zfs_pool_allocated_bytes gauge\n'
  printf '# TYPE zfs_pool_free_bytes gauge\n'
  zpool list -Hp -o name,size,alloc,free | awk -F '\t' '
    { name=$1; gsub(/\\/, "\\\\", name); gsub(/"/, "\\\"", name);
      printf "zfs_pool_size_bytes{pool=\"%s\"} %s\n", name, $2;
      printf "zfs_pool_allocated_bytes{pool=\"%s\"} %s\n", name, $3;
      printf "zfs_pool_free_bytes{pool=\"%s\"} %s\n", name, $4; }'
} > "$tmp_file"

chmod 0644 "$tmp_file"
mv -f "$tmp_file" "$output_dir/zfs.prom"
trap - EXIT HUP INT TERM
