# Media automation

Portainer stack `arr` (ID 153, endpoint 2) runs on `ctr` at `10.1.1.4`. Its tracked source is [`compose.yaml`](compose.yaml). The stack contains Sonarr, Radarr, Lidarr, Readarr, Prowlarr, Bazarr, Seerr, qBittorrent, Cleanuparr, and Unpackerr. Each service has its own persistent configuration under `/data/apps/arr/<service>` and shares only the paths it needs from the encrypted SMB AV mount. No service uses the old `docknet` network.

`ctr` is Proxmox VM 204. It has four vCPUs and ballooned RAM with an 8 GB minimum and 16 GB maximum (`balloon: 8192`, `memory: 16384`), selected by the owner on 2026-09-30 after a guest-global OOM killed OpenViking. This supersedes the briefly applied fixed 16 GB configuration. Host pressure can reclaim RAM toward 8 GB, so the maximum is not guaranteed and guest OOM remains possible under pressure. There is no swapfile or active swap. Do not re-create the temporary `/data/swapfile` or its systemd unit. The VM reboot on 2026-09-29 confirmed that Docker and the AV mount returned and all six containers restarted. Check memory after changing this stack because it shares the VM with other applications.

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

For *The Drama* on 2026-09-29, Radarr's interactive search showed a same-quality 6.43 GB Blu-ray candidate reporting 195 seeds. It was manually grabbed while the old torrent was paused, then the **live** swarm was measured: six connected seeds and an initial 4.8–5.9 MB/s, versus the old torrent's two seeds and roughly 2 MB/s. Only after that comparison was the old queue item removed from Radarr with `removeFromClient=true` and `blocklist=true`, which also removed its partial download. The replacement remained the sole active queue item. Its speed and ETA subsequently fluctuated with peer availability; do not treat the initial estimate as a completion guarantee. This was a one-off source replacement, not an automatic live-swarm selection feature. The replacement later reached 100% and Radarr imported the full movie at 17:56 UTC. qBittorrent's subsequent `stalledUP` state means seeding with no peers currently requesting data, not a stopped or failed download.

Bazarr has an **English + Hindi** subtitle language profile, applied by default to new Radarr movies and Sonarr series. Enabled account-free providers are Subtitle Cat (English/Hindi), Embedded Subtitles, and YIFY Subtitles (English movies); machine translation is disabled. Bazarr connected to both library managers. For *The Drama*, it recognized embedded English subtitles, downloaded a Hindi `.srt`, and reported no missing subtitles. Subtitle language does not change the media's spoken audio: an English-only release will not become Hindi-dubbed. Check the audio tracks and subtitle results for any title that specifically needs Hindi.

The Radarr `HD-1080p` profile used by Seerr allows only 1080p WEB and Blu-ray. HDTV and Remux are disabled. The owner's `Spider-Man: Brand New Day` request is monitored in Radarr. Search returns theatrical copies and suspiciously labeled HDTV results, but no approved WEB/Blu-ray release as of 2026-09-29, so the queue is correctly empty. Do not force-grab an unverified release to make the pipeline appear successful. Normal RSS/search automation should pick up an acceptable release when one appears; check the release list and queue if it remains unavailable after a confirmed digital release.

For this stack, the operational path is Seerr request → Radarr/Sonarr → Prowlarr-managed indexer → qBittorrent → `/data/downloads/{movies,shows}` → hardlink/import to `/data/media/{movies,shows}` → Jellyfin. Radarr's qBittorrent test returned HTTP 200, and an actual hardlink test between the SMB download and movie directories succeeded with the same inode and link count 2. Keep the common `/data` mapping and category-specific paths intact. Review indexer health and release quality periodically; public indexer results are not trustworthy just because their tests pass. Use sources only for media you are authorized to obtain. qBittorrent currently uses the host's direct network connection, not a VPN; consider that before downloading or sharing media.

Validation on 2026-09-29 used the legally distributable Blender *Big Buck Bunny* sample. Radarr recognized and manually imported it from the AV downloads path, Jellyfin's Movies library indexed it, and Bazarr found the Radarr movie with the English + Hindi profile. This proves the download-path → Radarr import → Jellyfin/Bazarr path, **not** an automatic torrent acquisition. After validation, the test title, its library file, and the download-staging copy were removed; Jellyfin's stale item was removed through its API. Jellyfin's media bind was changed from read-only to read-write after the UI could not delete files. A direct create/delete probe and Jellyfin item deletion both succeeded. Keep Radarr/Sonarr and Jellyfin library state in sync when deleting a real title.

The completed *The Drama* request proves the automatic qBittorrent → Radarr import path with a real download. Jellyfin initially did not discover the new file on the SMB-mounted library; its scheduled scan had been every 12 hours. The five-minute fallback scan (`IntervalTicks: 3000000000`) remains persisted under `/data/apps/jellyfin/config/config/ScheduledTasks/`. The follow-up browser test then exposed a separate SMB hardlink/lease problem that prevented opening the video. This was repaired and actual playback was verified; see the [2026-09-29 playback RCA](RCA-2026-09-29.md).

## Audited automation baseline, 2026-09-29

- AV uses persistent SMB `nolease` to avoid the concurrent hardlink-open failure. Encryption, UID/GID 1000 and hardlink imports remain enabled. Source and library still have inode 7077894/link count 2 for the verified movie. A 100-iteration concurrent source/hardlink-read probe passed.
- Radarr and Sonarr native `MediaBrowser` connections named `Jellyfin` update its library on import, upgrade, rename and deletion. Backend `10.1.1.4:8096`, path mapping `/data/media` → `/media`, `updateLibrary=true`, `notify=false`. Both connection tests passed. A real Radarr rename automatically reached Jellyfin; no manual scan was invoked for that rename.
- Movie/episode renaming is enabled using the existing readable formats. Subtitle sidecar import is enabled for `srt,ass,ssa,vtt`; minimum free space before importing is 1024 MB. The current movie and its `.hi.srt` were renamed together, and Bazarr followed the change with no missing subtitles.
- Completed download handling, one-minute queue checks and automatic retry of failed downloads are enabled in both managers. All three Prowlarr indexer tests, both full-sync application tests, both download-client tests and Seerr's Radarr/Sonarr tests passed. The selected profiles remain HD-1080p; no new media was requested during this audit.
- Seerr had **zero selected libraries**. Movies and TV Shows are now enabled, full sync succeeded, and the movie/request report status 5 (available). Recently-added scanning runs every five minutes; full Jellyfin scanning is daily. Seerr's application URL and external Radarr/Sonarr/Jellyfin URLs now use their Caddy HTTPS hostnames instead of Docker/LAN URLs.
- qBittorrent now defaults new downloads to automatic torrent management, using category paths `/data/downloads/movies` and `/data/downloads/shows`, with `/data/downloads/incomplete` for unfinished data. The existing movie source was moved into its category by qBittorrent without breaking its library hardlink. Download/upload limits remain unlimited, DHT/PeX enabled and up to three downloads active.
- qBittorrent seeding stops at ratio 1 or 1440 minutes. The existing Radarr/Sonarr `removeCompletedDownloads=true` setting removes completed staging torrents/files only after import and the client's seeding target is satisfied. This cleanup is configured; the 24-hour threshold was not artificially triggered during validation. Do not enable qBittorrent's direct delete-data action, which could race an import.
- Native API/HTTP health checks are defined for all six containers in Portainer stack 153's Compose. Stack 153 was updated through Portainer's API without pulling new images. All six returned healthy after recreation; Jellyfin remained healthy. Health checks do not automatically restart an unhealthy running process.
- Real browser playback through Caddy was tested before and after rename, including seeking: HEVC → Intel QSV H.264, E-AC-3 → AAC, no player error, zero dropped frames in the observed test. English embedded and Hindi external subtitle streams are detected. A successful container health check or library entry alone is never a playback test.

Normal use is to request in Seerr and wait for an approved available release. No manual import, scan, rename or subtitle search is required on the tested path. An unavailable release, unhealthy public swarm, source outage or missing subtitle still requires waiting or investigation; no configuration can guarantee peers or Hindi audio for every title. Sonarr's connections/settings were tested, but there is no TV episode in this empty Shows library to claim an actual series playback test.

## Request and download checks

Seerr cannot show an exact download size at request time because the release has not been chosen. After selection, open **Radarr/Sonarr → Activity → Queue** or **qBittorrent** for the chosen file size, progress, live seed/peer count, speed, and ETA. Use **Radarr/Sonarr → Interactive Search** to compare sizes, reported seeds, language, quality, and rejection reasons. Indexer seed counts can be stale or inflated; qBittorrent's live peer/trackers view is the decisive transfer-health check. A selected release can be slower than a smaller WEB or Blu-ray option even if its quality rank is higher.

If a requested movie has no approved release, first check whether a genuine digital/physical release exists. The monitored *Spider-Man: Brand New Day* request had no verified approved WEB/Blu-ray candidate on 2026-09-29; a metadata digital-release date or a mislabeled search result is not proof of availability. Do not force a CAM or suspiciously labeled file to make the request appear complete.

The setup follows the [Servarr Docker guide](https://wiki.servarr.com/docker-guide), [Prowlarr quick-start](https://wiki.servarr.com/prowlarr/quick-start-guide), [Seerr service settings](https://docs.seerr.dev/using-seerr/settings/services/), and [TRaSH hardlink guide](https://trash-guides.info/File-and-Folder-Structure/Hardlinks-and-Instant-Moves/): one shared filesystem/mount for atomic imports and hardlinks, one indexer manager, separate qBittorrent categories, and quality profiles that reject poor sources. No FlareSolverr or extra database is required for the three working indexers.

## Operations

### Lidarr and Readarr, added 2026-09-30

Stack 153 now also owns Lidarr 3.1.0.4875 and owner-approved community fork `ghcr.io/faustvii/readarr:0.10.0`. Private URLs: `https://lidarr.l3b.cc.cd` and `https://readarr.l3b.cc.cd`. Existing Caddy/Tinyauth/Pocket ID and app-specific ACLs protect them; native Forms login protects direct LAN ports 8686/8787. Single HomeLab vault items `Lidarr` and `Readarr` hold the email username, strong passwords and concealed API keys. No secrets belong in Git.

Each service is limited to 512 MiB and one CPU, uses the stack's default network, and persists SQLite/config in `/data/apps/arr/{lidarr,readarr}`. The fork runs explicitly as UID/GID 1000 and uses its installed `wget` for health checks. Watchtower updates are disabled for pinned Readarr; back up configuration and inspect migration changes before upgrading. No new database, privileged container or Docker socket was added.

The original Readarr retired in June 2025. Its archived LinuxServer image failed two verified tests: qBittorrent 5.2.4 returns successful HTTP 204 with a SID cookie, which original Readarr rejects; original Goodreads lookup also failed. The approved Faustvii fork contains the login fix and working community search. It uses external metadata `https://api.bookinfo.pro`, a community dependency rather than an official Servarr service. Do not downgrade qBittorrent or bypass authentication to restore the retired version.

| Purpose | Host path | Container path/category |
| --- | --- | --- |
| Music library | `/mnt/AV/media/music` | `/data/media/music`; Jellyfin `/media/music` |
| Books library | `/mnt/AV/media/books` | `/data/media/books` |
| Music staging | `/mnt/AV/downloads/music` | `/data/downloads/music`, category `music` |
| Books staging | `/mnt/AV/downloads/books` | `/data/downloads/books`, category `books` |

Lidarr's `Music - MP3 and FLAC` profile accepts MP3-256/320, VBR V0/V2 and FLAC, upgrading toward FLAC. Readarr's `Books - EPUB and PDF` profile accepts EPUB/PDF with automatic upgrades disabled. Renaming and hardlink imports are enabled, with a 1 GB free-space floor. Keep the common AV bind so staging and library imports share a filesystem.

Prowlarr owns full-sync connections: music receives TorrentDownload and The Pirate Bay; books receives TorrentDownload's supported ebook category. Existing reported-seeder rules remain unchanged. Add artists/albums in Lidarr and authors/books in Readarr: Seerr handles only movies/TV. Source availability and transfer speed are not guaranteed by passing tests; obtain only content you are authorized to access.

Jellyfin now has a Music library at `/media/music`; Lidarr's tested native connection triggers updates after import/upgrade/rename using its dedicated persistent Jellyfin API key. Readarr is a manager, not a book-reading client. Use an appropriate reader with the AV files; no Calibre service was added.

Cleanuparr connects to both new apps without changing the conservative policy or enabling failed-import deletion. Unpackerr polls all four queues. `LIDARR_API_KEY` and `READARR_API_KEY` are stored alongside existing Radarr/Sonarr keys in Portainer Stack Env, not Git; original archive deletion remains disabled.

Verified: both containers healthy, roots accessible, app health lists empty, native unauthenticated settings APIs rejected, qBittorrent and Prowlarr tests passed, artist search for Arijit Singh and book search for The Little Prince returned results, Lidarr's Jellyfin update test passed, and Unpackerr successfully polled both empty queues. Existing movie/TV services remained healthy. No music/book download was initiated, so no actual acquisition-to-playback/reading test is claimed. Homepage Media cards are GitOps-managed.

Sources: [fork](https://github.com/Faustvii/Readarr), [v0.10.0](https://github.com/Faustvii/Readarr/releases/tag/v0.10.0), [container workflow](https://github.com/Faustvii/Readarr/blob/develop/.github/workflows/docker-build.yml), [metadata](https://github.com/blampe/rreading-glasses), [retired upstream](https://github.com/Readarr/Readarr).

### Cleanuparr and Unpackerr, added 2026-09-30

Both helpers are managed by the existing Portainer stack, using its own default network. Versions are pinned to the verified stable releases: `ghcr.io/cleanuparr/cleanuparr:2.10.8` and `golift/unpackerr:0.16.1`. No extra database, Docker socket, privileged mode, or media-library bind was added. Each has a 256 MiB memory limit; CPU limits are 0.5 for Cleanuparr and 1 for Unpackerr. These limits do not remove the VM's overall memory-pressure risk.

Cleanuparr is private at `https://cleanuparr.l3b.cc.cd`, behind the existing Caddy/Tinyauth/Pocket ID gate, with native authentication also enabled. Its credentials and concealed API key are in the single HomeLab 1Password item `Cleanuparr`. Configuration and SQLite state persist in `/data/apps/arr/cleanuparr`. Caddy routes to LAN port 11011; `/health` is deliberately unauthenticated at the backend, but configuration APIs require authentication. The Homepage Media card links to the private UI.

Its live policy is intentionally conservative:

- Radarr, Sonarr and qBittorrent are connected by Docker service name, and all three connection tests passed.
- QueueCleaner runs every five minutes. The single public-torrent stall rule permits 24 strikes, approximately two hours of repeated stalled checks, and resets strikes when progress resumes. Its completion range is 0–99 percent; completed/seeding downloads are not its target.
- Metadata stalls also allow 24 strikes. Failed-import cleanup/force import, slow-download rules, download/seeding cleanup, orphaned-file cleanup and no-content-ID processing are disabled. Private torrents are not targeted by the public stall rule.
- Seeker replacement searches are enabled, on a ten-minute schedule, but proactive searches are disabled. Existing Radarr/Sonarr quality and seed-count policies remain authoritative. This does not guarantee healthy peers or replace every merely slow download.

Unpackerr is a background worker, not a Web UI. It polls the existing Radarr/Sonarr queues every two minutes, waits one minute before extraction, and extracts one archive at a time. It runs as UID/GID 1000, creates files with mode `0660` and directories with `0770`, and mounts only `/mnt/AV/downloads` at `/data/downloads`. Radarr's path is `/data/downloads/movies`; Sonarr's is `/data/downloads/shows`. Original-archive deletion is disabled. Its own configuration directory is `/data/apps/arr/unpackerr`; runtime configuration is supplied by Compose. Webserver and generic folder watching are disabled in the permanent service.

Portainer stack environment variables `RADARR_API_KEY` and `SONARR_API_KEY` contain the existing native app keys; keep their values out of Git. The scratch Unpackerr image has no shell/curl, so no fabricated HTTP health check is assigned. Verify successful queue polling in its logs rather than confusing “running” with a functional extraction. Cleanuparr has a real HTTP health check.

Sources: [Cleanuparr deployment](https://cleanuparr.github.io/Cleanuparr/docs/installation/docker/), [Cleanuparr release source](https://github.com/Cleanuparr/Cleanuparr/tree/v2.10.8), [Unpackerr configuration for v0.16.1](https://github.com/Unpackerr/unpackerr/blob/v0.16.1/examples/unpackerr.conf.example). Configuration API contracts were verified against Cleanuparr's exact release, not an older configuration format. Live policy resides in its persistent database; recreating an empty `/config` requires repeating app initialization, connections and rules.

Validation: Cleanuparr's real health check passed, all three integration health states were healthy, and both its native settings API and its unauthenticated Caddy route returned 401. Unpackerr successfully polled both app queues. An isolated temporary container using the same image and UID/GID extracted a generated tar.gz archive on the actual AV downloads mount, preserved the original, and produced byte-identical content owned by 1000:1000 with mode 0660. The temporary container and only its generated test directory were removed. This verifies extraction and SMB permissions; no live stalled torrent was deliberately removed and no real archived movie was available to claim a complete archive → import → playback test.

Manage updates and restarts through Portainer stack `arr`. Keep `compose.yaml` in Git aligned with the Portainer Stackfile before redeployment. Do not run a second Compose project for the same service names.

```bash
ssh ctr 'docker ps --format "{{.Names}} {{.Status}}" | grep -E "sonarr|radarr|prowlarr|bazarr|seerr|qbittorrent"'
ssh ctr 'mountpoint /mnt/AV; free -h; docker stats --no-stream'
ssh px20 'qm config 204 | grep -E "^(memory|balloon):"'
```

The AV share is a boot dependency for downloads and library imports. If it is not mounted, stop the stack and repair the SMB mount before allowing qBittorrent or either library manager to write; otherwise data could land on the VM root disk. The six Caddy endpoints should return Tinyauth `401` to unauthenticated API clients from the LAN. An unauthenticated direct call to each application's settings API should also be denied.

Back up `/data/apps/arr` through the VM backup schedule and the AV share separately; the VM's local ZFS replication and HA are not a substitute for a historical backup of the external share. API keys and passwords are intentionally absent from this repository.
