# Jellyfin

Portainer stack **94** `jellyfin`, running as a container on the `l3b` Docker
network on the single Debian host. The image is the official
`jellyfin/jellyfin:12.4` pinned by digest in [compose.yaml](compose.yaml).

There is no host port: Jellyfin listens on `8096` inside `l3b` and Caddy
reverse-proxies `https://media.l3b.cc.cd` to it. Caddy's source gate keeps the
service LAN/WireGuard-only; Jellyfin's own login stays enabled as a break-glass
path.

## Runtime

| Item | Value |
| --- | --- |
| Image | `jellyfin/jellyfin:12.4` |
| User | `1000:1000`, plus render GID `991` |
| Device | `/dev/dri/renderD128` (Intel iGPU, VAAPI transcoding) |
| Published port | none — `expose: 8096` only |
| Health | `curl -fsS http://127.0.0.1:8096/health` every 30 s |
| Updates | Watchtower, daily at 04:00 IST |

## Mounts

| Container | Host | Size | Purpose |
| --- | --- | --- | --- |
| `/config` | `/data/apps/jellyfin/config` | 158 MB | database, metadata, images, plugins, `sso.json` |
| `/cache` | `/data/apps/jellyfin/cache` | 762 MB | transcode scratch and image cache |
| `/media` | `/data/apps/smb` | 70 GB | `movies/`, `shows/`, `downloads/` |

All three host paths are on the internal 1.92 TB SATA SSD (`/data`, XFS). The
USB backup disk at `/BACKUP` is never mounted into Jellyfin.

The media bind is read-write so an administrator can delete media from the UI.
The share is the same tree served by Samba; see
[../smb/README.md](../smb/README.md) for the folder policy and permissions.

## Libraries

| Library | Path | Notes |
| --- | --- | --- |
| Movies | `/media/movies` | |
| TV Shows | `/media/shows` | |

The **Music** library was removed on 4 November 2026 together with its
`/media/music` folder; the media share intentionally has no music directory.
`downloads/` is not a library.

## Transcoding

Hardware transcoding uses the Intel iGPU through `/dev/dri/renderD128`, with
`group_add: 991` so the non-root container user can open the render node. No
`privileged`, host networking, or whole-GPU device passthrough is used.

## Pocket ID SSO

`JELLYFIN_SSO_CONFIG_FILE` points at `/config/sso.json` and the SSO plugin
redirects to `https://auth.l3b.cc.cd`. The redirect URI registered in Pocket ID
must stay `https://media.l3b.cc.cd/sso/OID/redirect/pocketid`.

Jellyfin only honours `X-Forwarded-Proto` from known proxies. `network.xml` must
list Caddy's sources:

```xml
<KnownProxies>
  <string>10.1.1.3</string>
  <string>10.1.3.0/24</string>
</KnownProxies>
```

Without `10.1.3.0/24` the plugin builds an `http://` callback, Pocket ID rejects
the pushed authorization request, and the start endpoint shows
**"Error preparing login. Return to login."** That exact failure was fixed on
2 November 2026 this way. Native password login was never disabled.

## Operations

```sh
sudo docker logs jellyfin --tail 50
sudo docker inspect jellyfin --format '{{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8096/health
```

Restart with `docker restart jellyfin`, or redeploy Portainer stack 94. The
health check needs `start_period: 60s`; Jellyfin is slow to open the port after
a restart.

## History

- 2026-10-05 — the container failed to start because the old SMB media mount
  (`/mnt/AV/media`) was unavailable (`no such device`). Media now lives on the
  local `/data` disk, so startup no longer depends on a network mount.
- 2026-10-22 — the ARR automation stack (Radarr, Sonarr, Prowlarr, Bazarr and
  others) was retired. Jellyfin's library is no longer driven by those tools.
- 2026-11-02 — Pocket ID SSO redirect fix, described above.
- 2026-11-04 — media consolidated to `/data/apps/smb`; Music library removed.
