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

Seerr is initialized with Jellyfin and default Sonarr/Radarr servers using their API keys and existing HD-1080p profiles. Prowlarr has both applications registered for full sync. Bazarr has both applications connected. No indexers, subtitle providers, or downloads were added on the owner's behalf; add only sources you are authorized to use. Any request to Seerr needs functioning indexers before it can find releases.

## Operations

Manage updates and restarts through Portainer stack `arr`. Keep `compose.yaml` in Git aligned with the Portainer Stackfile before redeployment. Do not run a second Compose project for the same service names.

```bash
ssh ctr 'docker ps --format "{{.Names}} {{.Status}}" | grep -E "sonarr|radarr|prowlarr|bazarr|seerr|qbittorrent"'
ssh ctr 'mountpoint /mnt/AV; free -h; docker stats --no-stream'
ssh px20 'qm config 204 | grep -E "^(memory|balloon):"'
```

The AV share is a boot dependency for downloads and library imports. If it is not mounted, stop the stack and repair the SMB mount before allowing qBittorrent or either library manager to write; otherwise data could land on the VM root disk. The six Caddy endpoints should return Tinyauth `401` to unauthenticated API clients from the LAN. An unauthenticated direct call to each application's settings API should also be denied.

Back up `/data/apps/arr` through the VM backup schedule and the AV share separately; the VM's local ZFS replication and HA are not a substitute for a historical backup of the external share. API keys and passwords are intentionally absent from this repository.
