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
    options=$(findmnt -rn -M "$path" -o OPTIONS)
    case ",$options," in
        *,ro,*|*,emergency_ro,*)
            echo "Store CT 109: $path is read-only or in filesystem emergency mode" >&2
            exit 1
            ;;
    esac
    if ! timeout 10s ls -A "$path" >/dev/null; then
        echo "Store CT 109: $path cannot be read" >&2
        exit 1
    fi
}

check_volume /mnt/external/AV 2489f3c3-bbaa-4f4b-bdf5-69d240a6bdab
check_volume /mnt/external/BACKUP c21cf584-1056-4d9c-8d52-ba2c72d92379
if grep -q '^mp2:' /etc/pve/lxc/109.conf; then
    if ! grep -Eq '^mp2: /mnt/external/ISO,mp=/srv/ISO(,|$)' /etc/pve/lxc/109.conf; then
        echo "Store CT 109: mp2 is not the expected ISO bind mount" >&2
        exit 1
    fi
    check_volume /mnt/external/ISO a19cf10d-4e36-4e00-94ce-bacc9381b30b
fi
