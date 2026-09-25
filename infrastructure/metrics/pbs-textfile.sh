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
chmod 644 "$temp"
mv "$temp" "$directory/pbs.prom"
