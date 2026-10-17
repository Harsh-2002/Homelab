#!/bin/sh
set -eu

unit=${1:?Usage: watch-iso-recovery.sh UNIT MAPFILE}
mapfile=${2:?Usage: watch-iso-recovery.sh UNIT MAPFILE}
source=/dev/disk/by-uuid/a19cf10d-4e36-4e00-94ce-bacc9381b30b

while :; do
    printf '\n%s\n' "$(date -Is)"
    partition=$(readlink -e "$source") || partition=
    if [ -z "$partition" ]; then
        echo 'ALERT: ISO source device disappeared. Recovery needs inspection.'
        exit 1
    fi
    disk=$(lsblk -ndo PKNAME "$partition")
    state=$(cat "/sys/class/block/$disk/device/state")
    active=$(systemctl show "$unit" --property=ActiveState --value)
    printf 'device=%s device_state=%s recovery_unit=%s recovery_state=%s\n' \
        "$disk" "$state" "$unit" "$active"
    if [ "$state" != running ]; then
        echo 'ALERT: ISO source is not running. Recovery needs inspection.'
        exit 1
    fi
    timeout 5s ddrescuelog --show-status "$mapfile" || {
        echo 'ALERT: Recovery map could not be read or validated.'
        exit 1
    }
    case "$active" in
        active|activating) ;;
        *)
            if ddrescuelog --done-status "$mapfile"; then
                echo 'COPY_COMPLETE: map has no unrecovered ranges. Filesystem and guest validation still required.'
                exit 0
            fi
            echo 'ALERT: Recovery stopped with unrecovered data. No automatic restart or repair performed.'
            exit 1
            ;;
    esac
    sleep 30
done
