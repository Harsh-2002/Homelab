# Watchtower

Portainer Stack **62** `watchtower` on endpoint 2. It is the only automated
image updater on `l3b`; nothing else pulls or replaces images on a schedule.

Current state (3 November 2026): **running**, `nickfedor/watchtower:latest`
(Watchtower 1.23.2), container `watchtower`, `restart: always`, healthy.

The `containrrr/watchtower` image is retired upstream; `nickfedor/watchtower`
is the maintained replacement and is the image pinned in the stack.

## Configuration

| Setting | Value | Meaning |
| --- | --- | --- |
| `TZ` | `Asia/Kolkata` | schedule is evaluated in IST |
| `WATCHTOWER_SCHEDULE` | `0 0 4 * * *` | daily at **04:00 IST** |
| `WATCHTOWER_CLEANUP` | `true` | delete the replaced image after a successful update |
| `WATCHTOWER_RUNNING_ONLY` | `true` | only running containers are considered |
| `WATCHTOWER_INCLUDE_STOPPED` | `false` | stopped stacks (Forgejo) are never started |
| `WATCHTOWER_INCLUDE_RESTARTING` | `true` | restarting containers are included |
| `WATCHTOWER_RETRY_COUNT` | `3` | retry failed updates |

Label filtering is **off** (no `WATCHTOWER_LABEL_ENABLE`), so every running
container is monitored, including containers created by other Portainer stacks.
The `com.centurylinklabs.watchtower.enable` labels in service Compose files have
no effect while filtering is off.

## Verification

```sh
sudo docker ps --filter name=watchtower
sudo docker logs watchtower --tail 20
```

The startup log must contain a line such as:

```text
Next scheduled run: 2026-11-04 04:00:00 IST
```

A read-only capability check, without changing anything:

```sh
sudo docker run --rm --network l3b \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e TZ=Asia/Kolkata nickfedor/watchtower:latest \
  --monitor-only --run-once
```

`--monitor-only` reports images with a newer digest and never replaces a
container. On 3 November 2026 it reported `searxng` as the only outdated image,
which also proves label filtering is off.

## Behaviour and limits

- Updates are per-container, not per-stack: Portainer redeploys later will
  reconcile the stack definition, but the running container may be newer than
  the Compose file until then.
- A major-version tag change is still possible for `:latest` images. Services
  pinned to an exact tag (`jellyfin/jellyfin:12.4`, `immich-server:v3.3.5`)
  only move within that tag's digest.
- Databases are included because monitoring is global. A failed update leaves
  the previous container running; check `docker logs watchtower` after 04:00 if
  a service misbehaves.
- The stack file still carries a commented-out Slack webhook URL. It is inert
  while commented, but it is a live credential in the stack definition and
  should be revoked or removed if Slack notifications are not used.
