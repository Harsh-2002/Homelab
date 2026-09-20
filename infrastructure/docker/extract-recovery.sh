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

while loopdev=$(losetup -j "$image" | cut -d: -f1 | head -n1) && [ -n "$loopdev" ]; do
    if losetup --detach "$loopdev"; then
        break
    fi
    sleep 10
done

mkfs.ext4 -F -E nodiscard,lazy_itable_init=1,lazy_journal_init=1 -m 0 -L linux-recovery "$image"
loopdev=$(losetup --find --show "$image")
install -d -o root -g root -m 0755 "$target"
mount -o noatime "$loopdev" "$target"

pv -f -s 502214830080 "$archive" \
    | tar --acls --xattrs --numeric-owner -xpf - -C "$target"

sync
test -f "$target/2026-09-15/metadata/COMPLETED"
umount "$target"
losetup --detach "$loopdev"
mount -o remount,ro /EX
loopdev=$(losetup --find --show --read-only "$image")
mount -o ro,noatime "$loopdev" "$target"
