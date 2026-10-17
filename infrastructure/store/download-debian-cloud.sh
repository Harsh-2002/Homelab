#!/bin/sh
set -eu
umask 022

destination=${1:-/mnt/pve/ISO/import}
filename=debian-13-genericcloud-amd64.qcow2
base=https://cloud.debian.org/images/cloud/trixie/latest

if [ ! -d /mnt/pve/ISO ] || ! mountpoint -q /mnt/pve/ISO; then
    echo 'ISO SMB storage must be mounted before downloading.' >&2
    exit 1
fi
case "$destination" in
    /mnt/pve/ISO/*) ;;
    *) echo 'Destination must be inside mounted ISO storage.' >&2; exit 1 ;;
esac
mkdir -p "$destination"
if [ -e "$destination/$filename" ] || [ -e "$destination/$filename.part" ]; then
    echo 'Image or partial download already exists; refusing to overwrite.' >&2
    exit 1
fi
expected=$(curl --fail --silent --show-error --location "$base/SHA512SUMS" |
    awk -v file="$filename" '$2 == file { print $1 }')
test "${#expected}" -eq 128 || { echo 'Missing or invalid upstream checksum.' >&2; exit 1; }
curl --fail --silent --show-error --location --retry 3 \
    --output "$destination/$filename.part" "$base/$filename"
actual=$(sha512sum "$destination/$filename.part" | cut -d ' ' -f 1)
test "$actual" = "$expected" || { echo 'Checksum mismatch; partial file retained, not published.' >&2; exit 1; }
qemu-img check -q "$destination/$filename.part"
mv "$destination/$filename.part" "$destination/$filename"
printf '%s  %s\n' "$expected" "$filename" > "$destination/$filename.sha512"
printf 'Verified Debian 13 stable amd64 cloud image: %s/%s\n' "$destination" "$filename"
qemu-img info "$destination/$filename"
