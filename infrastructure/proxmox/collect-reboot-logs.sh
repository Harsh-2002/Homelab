#!/bin/bash
set -uo pipefail
export LC_ALL=C SYSTEMD_PAGER=cat
umask 077
work=$(mktemp -d /run/px30-snapshot.XXXXXX)
trap 'rm -rf -- "$work"' EXIT
started=$SECONDS
{
 echo '=== FAST READ-ONLY SNAPSHOT ==='; date -u; hostname; uptime
 cat /proc/sys/kernel/random/boot_id /proc/cmdline
 echo '=== CURRENT KERNEL RING BUFFER ==='; dmesg --color=never
 echo '=== BOOT INDEX ==='; journalctl --list-boots --no-pager
 echo '=== RECENT BOOT JOURNALS ==='
 for boot in 0 -1 -2 -3; do echo "=== BOOT $boot ==="; journalctl -b "$boot" --no-pager -o short-monotonic; done
 echo '=== INPUT AND POWER CONFIGURATION ==='; cat /proc/bus/input/devices
 systemd-analyze cat-config systemd/logind.conf
 systemd-inhibit --list --no-pager
 echo '=== SERVICE STATE ==='; systemctl --failed --no-pager
 systemctl show systemd-logind pve-ha-lrm pve-ha-crm watchdog-mux --property=ActiveState,SubState,Result,ExecMainStatus
 echo '=== HARDWARE / NETWORK / STORAGE ==='; uname -a; lscpu; free -h
 for entry in product_name bios_version bios_date; do echo "$entry"; cat "/sys/class/dmi/id/$entry"; done
 ip -brief address; ip route; ip -s link; lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
 timeout 2s zpool status -v
 for entry in /sys/class/watchdog/watchdog*/{identity,state,status,timeout,bootstatus}; do test ! -r "$entry" || { echo "$entry"; cat "$entry"; }; done
} > "$work/snapshot.txt" 2>&1
paths=()
for path in /var/log/journal /run/log/journal /var/lib/systemd/pstore /sys/fs/pstore /var/log/{syslog,kern.log,daemon.log,dmesg}*; do
 test ! -e "$path" || paths+=("${path#/}")
done
# Native journal files preserve every retained boot without formatting history.
# Live files may change; snapshot.txt contains an independent recent-boot export.
tar --ignore-failed-read --warning=no-file-changed -C "$work" -cf - snapshot.txt -C / "${paths[@]}" 2> "$work/tar-errors.txt" |
 zstd -q -1 -T2 |
 curl --http1.1 -fsS -H 'Expect:' -H 'Content-Type: application/zstd' --upload-file - -w '\nTransfer: %{size_upload} bytes in %{time_total}s\n' "$PX30_UPLOAD_URL"
result=$?
echo "Collection and upload elapsed: $((SECONDS-started)) seconds"
exit "$result"
