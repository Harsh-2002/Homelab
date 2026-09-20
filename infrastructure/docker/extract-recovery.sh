#!/bin/bash
set -euo pipefail

archive=/EX/linux-recovery.tar
image=/EX/linux-recovery.ext4
target=/RECOVERY

while pgrep -x mkfs.ext4 >/dev/null; do
    sleep 10
done

test -f "$archive"
test -f "$image"
test "$(stat -c %s "$archive")" = 502214830080

loopdev=$(losetup -j "$image" | cut -d: -f1 | head -n1)
if [ -z "$loopdev" ]; then
    loopdev=$(losetup --find --show "$image")
fi

mkfs.ext4 -F -E nodiscard -m 0 -L linux-recovery "$loopdev"
install -d -o root -g root -m 0755 "$target"
mount "$loopdev" "$target"

pv -f -s 502214830080 "$archive" \
    | tar --acls --xattrs --numeric-owner -xpf - -C "$target"

sync
test -f "$target/2026-09-15/metadata/COMPLETED"
mount -o remount,ro "$target"
