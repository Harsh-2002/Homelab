#!/bin/sh
set -eu

state=$(docker inspect jellyfin --format '{{.State.Status}}|{{.State.ExitCode}}|{{.HostConfig.RestartPolicy.Name}}|{{.State.Error}}' 2>/dev/null) || exit 0
case "$state" in
  'exited|128|unless-stopped|'*'failed to fulfil mount request'*'/mnt/AV/media'*) ;;
  *) exit 0 ;;
esac

timeout 10 stat /mnt/AV/media >/dev/null 2>&1 || exit 0
findmnt -rn -t cifs -M /mnt/AV >/dev/null || exit 0
test -d /mnt/AV/media/movies || exit 0
docker start jellyfin
