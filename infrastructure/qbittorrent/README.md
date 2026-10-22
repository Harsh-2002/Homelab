# qBittorrent

Standalone Portainer stack **qbittorrent**, ID160/endpoint2, on CTR. It was moved
out of the retired ARR stack153 on2026-10-22 without changing its running image,
credentials, torrents, categories or download paths. Motrix and Jellyfin remain
independent stacks and were not restarted during this migration.

- Web UI: https://torrent.l3b.cc.cd (private LAN/Tailscale + Tinyauth/Pocket ID).
- LAN UI: 10.1.1.4:8081, native authentication retained.
- Peer ports: 10.1.1.4:6881 TCP/UDP, unchanged.
- Configuration: /data/apps/qbittorrent mounted at /config.
- Media/downloads: existing /mnt/AV mounted at /data; never delete this share
  when retiring the container. Existing download categories are preserved.
- Credentials: existing HomeLab item `qBittorrent`, not regenerated or deleted.

The stopped configuration directory moved from /data/apps/arr/qbittorrent with a
byte-for-byte manifest check before restart. New container runs the same image
ID; all two existing torrent hashes matched after startup. No config backup was
created at owner request. Authenticated qBittorrent5.2.4 login may return204 with
an empty body; verify authenticated API access rather than expecting only `Ok.`.

Manage through Portainer using docker-compose.yaml. The AV mount must be healthy
before starting. Proxy snippet `qbittorrent` and standalone Tinyauth rule/drop-in
under this directory preserve access. Homepage retains qBittorrent, Motrix and
Jellyfin, without ARR service cards. Automatic acquisition/import/subtitles and
music/book automation are no longer deployed; use these retained tools directly.
