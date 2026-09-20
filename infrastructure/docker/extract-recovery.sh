#!/bin/bash
set -euo pipefail

archive=/EX/linux-recovery.tar
target=/EX/RECOVERY
member=./2026-09-15/SSD
error_log=/EX/linux-recovery-direct-errors.log
status_file=/EX/linux-recovery-direct-status.txt

test -f "$archive"
test "$(stat -c %s "$archive")" = 502214830080
findmnt -no OPTIONS /EX | grep -qw rw
install -d -m 0755 "$target"

set +e
pv -f -s 502214830080 "$archive" \
    | tar --no-same-owner --no-same-permissions --no-acls --no-xattrs \
        --overwrite -xf - -C "$target" "$member" 2>"$error_log"
pipeline_status=("${PIPESTATUS[@]}")
set -e

sync
printf 'pv_status=%s\ntar_status=%s\ncompleted_at=%s\n' \
    "${pipeline_status[0]}" "${pipeline_status[1]}" "$(date --iso-8601=seconds)" \
    >"$status_file"

test "${pipeline_status[0]}" -eq 0
