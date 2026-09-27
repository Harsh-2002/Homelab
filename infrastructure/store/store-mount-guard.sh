#!/bin/sh
set -eu

[ "$1" = 109 ] || exit 0
[ "$2" = pre-start ] || exit 0

check_volume() {
    path=$1
    expected=$2
    actual=$(findmnt -rn -M "$path" -o UUID) || actual=
    if [ "$actual" != "$expected" ] || [ ! -f "$path/.store-volume" ]; then
        echo "Store CT 109: $path is not the expected mounted data volume" >&2
        exit 1
    fi
}

check_volume /mnt/external/AV 2489f3c3-bbaa-4f4b-bdf5-69d240a6bdab
check_volume /mnt/external/BACKUP c21cf584-1056-4d9c-8d52-ba2c72d92379
check_volume /mnt/external/ISO a19cf10d-4e36-4e00-94ce-bacc9381b30b
