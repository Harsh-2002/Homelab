# Media automation

Portainer stack `arr` (ID 153, endpoint 2) runs on `ctr` at `10.1.1.4`. Its tracked source is [`compose.yaml`](compose.yaml). The stack contains Sonarr, Radarr, Prowlarr, Bazarr, Seerr, and qBittorrent. Each service has its own persistent configuration under `/data/apps/arr/<service>` and shares only the paths it needs from the encrypted SMB AV mount. No service uses the old `docknet` network.

`ctr` is Proxmox VM 204. It has four vCPUs and a fixed 8 GB RAM (`memory: 8192`, `balloon: 0`). There is no swapfile or active swap. Do not re-create the temporary `/data/swapfile` or its systemd unit. The VM reboot on 2026-09-29 confirmed that Docker and the AV mount returned and all six containers restarted. Check memory after changing this stack because it shares the VM with other applications.

## Paths

| Purpose | Host path | Container path |
| --- | --- | --- |
| Movies library | `/mnt/AV/media/movies` | `/data/media/movies` in Radarr/Sonarr/qBittorrent; `/data/media/movies` in Bazarr |
| Shows library | `/mnt/AV/media/shows` | `/data/media/shows` |
| Download staging | `/mnt/AV/downloads` | `/data/downloads` |
| Incomplete downloads | `/mnt/AV/downloads/incomplete` | `/data/downloads/incomplete` |
| Movie downloads | `/mnt/AV/downloads/movies` | `/data/downloads/movies` |
| Show downloads | `/mnt/AV/downloads/shows` | `/data/downloads/shows` |

qBittorrent categories `movies` and `shows` save to those category directories. Sonarr and Radarr use root folders `/data/media/shows` and `/data/media/movies` and connect to qBittorrent by Docker service name on port 8081. The common `/mnt/AV` bind keeps downloads and libraries on the same filesystem for hardlinks and fast imports. Jellyfin reads the media library but is not managed by this stack. Motrix remains a separate general downloader and was not modified.

## Access and identity

All six Caddy routes are private to LAN and Tailscale, protected by Tinyauth/Pocket ID, and not deliberately published in public Cloudflare DNS. They are `sonarr`, `radarr`, `prowlarr`, `bazarr`, `seerr`, and `torrent` under `l3b.cc.cd`. Their backend ports on `10.1.1.4` are reachable directly on the LAN, so app-native authentication is enabled too: Forms for Sonarr/Radarr/Prowlarr/Bazarr, qBittorrent's Web UI login, and Jellyfin sign-in for Seerr. Credentials are in the existing HomeLab 1Password items with the matching service names; Seerr uses the `Jellyfin` account. Use `iam.anuragvishwakarma@gmail.com` where email is accepted and `iam-anuragvishwakarma` for qBittorrent.

Tinyauth's global ACL policy is deny-by-default. The per-app authorization rules for these six hostnames are tracked in `infrastructure/pocket-id/tinyauth-arr.rules` and loaded through a systemd drop-in on `auth`. A valid Pocket ID session is not enough without each app's whitelist and group rule. The 2026-09-29 initial OIDC denial was caused by missing rules, not a Pocket ID token failure.

Seerr is initialized with Jellyfin and default Sonarr/Radarr servers using their API keys and existing HD-1080p profiles. Automatic search on approved requests is enabled. Prowlarr has both applications registered for full sync. Bazarr has both applications connected. Prowlarr manages three account-free indexers: YTS (movies), TorrentDownload (movies and shows), and The Pirate Bay via its API (movies and shows). All passed their live connection tests on 2026-09-29 and synced into the appropriate apps. A Radarr interactive search returned 48 Pirate Bay, 45 TorrentDownload, and 6 YTS results for a test title; the counts include releases subsequently rejected by the quality/seed rules. Do not configure the same indexers separately in Radarr or Sonarr; Prowlarr full sync owns them. EZTV was blocked by Cloudflare. TorrentsCSV passed its own test but did not sync to either app because of its advertised categories, so it was removed. 1337x advertises a FlareSolverr requirement and was not added just to inflate the indexer count.

Prowlarr sets all three torrent indexers' **application minimum seeders to 20**. This value synced into all three Radarr indexers and both Sonarr indexers on 2026-09-29. It filters releases by the indexer's *reported* seed count; it cannot measure the live qBittorrent swarm or guarantee speed. The default was one reported seeder, which let Radarr grab a 17.8 GB Blu-ray release with only two connected seeds. At the time, qBittorrent was connected with no download-rate limit, but most trackers for that torrent failed or timed out. The healthy-indexer count and live-peer count are different signals. If a transfer stalls, inspect qBittorrent's live seeds/trackers and Radarr's interactive release list before replacing it; Radarr does not automatically swap a slow, otherwise healthy download for another release. Avoid changing the global quality profile just to rescue one torrent.

For *The Drama* on 2026-09-29, Radarr's interactive search showed a same-quality 6.43 GB Blu-ray candidate reporting 195 seeds. It was manually grabbed while the old torrent was paused, then the **live** swarm was measured: six connected seeds and about 4.8–5.9 MB/s, versus the old torrent's two seeds and roughly 2 MB/s. Only after that comparison was the old queue item removed from Radarr with `removeFromClient=true` and `blocklist=true`, which also removed its partial download. The replacement remained the sole active queue item, with an ETA around 17 minutes at the last check. This is a one-off source replacement, not an automatic live-swarm selection feature.

Bazarr has an **English + Hindi** subtitle language profile, applied by default to new Radarr movies and Sonarr series. Enabled account-free providers are Subtitle Cat (English/Hindi), Embedded Subtitles, and YIFY Subtitles (English movies); machine translation is disabled. Bazarr connected to both library managers and recognized a test movie as missing both languages. A manual English search completed without an API error, but that silent test film had no matching subtitle, so provider delivery for a real title remains unproven. Subtitle language does not change the media's spoken audio: an English-only release will not become Hindi-dubbed. Check the audio tracks and subtitle results for any title that specifically needs Hindi.

The Radarr `HD-1080p` profile used by Seerr allows only 1080p WEB and Blu-ray. HDTV and Remux are disabled. The owner's `Spider-Man: Brand New Day` request is monitored in Radarr. Search returns theatrical copies and suspiciously labeled HDTV results, but no approved WEB/Blu-ray release as of 2026-09-29, so the queue is correctly empty. Do not force-grab an unverified release to make the pipeline appear successful. Normal RSS/search automation should pick up an acceptable release when one appears; check the release list and queue if it remains unavailable after a confirmed digital release.

For this stack, the operational path is Seerr request → Radarr/Sonarr → Prowlarr-managed indexer → qBittorrent → `/data/downloads/{movies,shows}` → hardlink/import to `/data/media/{movies,shows}` → Jellyfin. Radarr's qBittorrent test returned HTTP 200, and an actual hardlink test between the SMB download and movie directories succeeded with the same inode and link count 2. Keep the common `/data` mapping and category-specific paths intact. Review indexer health and release quality periodically; public indexer results are not trustworthy just because their tests pass. Use sources only for media you are authorized to obtain. qBittorrent currently uses the host's direct network connection, not a VPN; consider that before downloading or sharing media.

Validation on 2026-09-29 used the legally distributable Blender *Big Buck Bunny* sample. Radarr recognized and manually imported it from the AV downloads path, Jellyfin's Movies library indexed it, and Bazarr found the Radarr movie with the English + Hindi profile. This proves the download-path → Radarr import → Jellyfin/Bazarr path, **not** an automatic torrent acquisition. After validation, the test title, its library file, and the download-staging copy were removed; Jellyfin's stale item was removed through its API. Jellyfin's media bind was changed from read-only to read-write after the UI could not delete files. A direct create/delete probe and Jellyfin item deletion both succeeded. Keep Radarr/Sonarr and Jellyfin library state in sync when deleting a real title.

## Request and download checks

Seerr cannot show an exact download size at request time because the release has not been chosen. After selection, open **Radarr/Sonarr → Activity → Queue** or **qBittorrent** for the chosen file size, progress, live seed/peer count, speed, and ETA. Use **Radarr/Sonarr → Interactive Search** to compare sizes, reported seeds, language, quality, and rejection reasons. Indexer seed counts can be stale or inflated; qBittorrent's live peer/trackers view is the decisive transfer-health check. A selected release can be slower than a smaller WEB or Blu-ray option even if its quality rank is higher.

If a requested movie has no approved release, first check whether a genuine digital/physical release exists. The monitored *Spider-Man: Brand New Day* request had no verified approved WEB/Blu-ray candidate on 2026-09-29; a metadata digital-release date or a mislabeled search result is not proof of availability. Do not force a CAM or suspiciously labeled file to make the request appear complete.

The setup follows the [Servarr Docker guide](https://wiki.servarr.com/docker-guide), [Prowlarr quick-start](https://wiki.servarr.com/prowlarr/quick-start-guide), [Seerr service settings](https://docs.seerr.dev/using-seerr/settings/services/), and [TRaSH hardlink guide](https://trash-guides.info/File-and-Folder-Structure/Hardlinks-and-Instant-Moves/): one shared filesystem/mount for atomic imports and hardlinks, one indexer manager, separate qBittorrent categories, and quality profiles that reject poor sources. No FlareSolverr or extra database is required for the three working indexers.

## Operations

Manage updates and restarts through Portainer stack `arr`. Keep `compose.yaml` in Git aligned with the Portainer Stackfile before redeployment. Do not run a second Compose project for the same service names.

```bash
ssh ctr 'docker ps --format "{{.Names}} {{.Status}}" | grep -E "sonarr|radarr|prowlarr|bazarr|seerr|qbittorrent"'
ssh ctr 'mountpoint /mnt/AV; free -h; docker stats --no-stream'
ssh px20 'qm config 204 | grep -E "^(memory|balloon):"'
```

The AV share is a boot dependency for downloads and library imports. If it is not mounted, stop the stack and repair the SMB mount before allowing qBittorrent or either library manager to write; otherwise data could land on the VM root disk. The six Caddy endpoints should return Tinyauth `401` to unauthenticated API clients from the LAN. An unauthenticated direct call to each application's settings API should also be denied.

Back up `/data/apps/arr` through the VM backup schedule and the AV share separately; the VM's local ZFS replication and HA are not a substitute for a historical backup of the external share. API keys and passwords are intentionally absent from this repository.
