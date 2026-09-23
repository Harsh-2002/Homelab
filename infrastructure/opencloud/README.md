# OpenCloud

OpenCloud is the file-sync and sharing service at `https://drive.l3b.cc.cd`. It replaces the unfinished restored Nextcloud deployment and runs as Portainer stack `opencloud` on `ctr`.

## Topology

| Component | Location | Persistence |
| --- | --- | --- |
| OpenCloud `7.2.4` production release | `ctr`, `10.1.1.4:9200` | `/data/apps/opencloud/{config,data}` |
| OpenCloud built-in user directory | Inside the OpenCloud service | `/data/apps/opencloud/data` |
| File blobs | RustFS bucket `opencloud` | `s3` LXC replicated by Proxmox |
| File metadata and system data | OpenCloud data directory | `/data/apps/opencloud/data` |

OpenCloud uses its supported `decomposeds3` driver. File blobs are stored in RustFS, but metadata remains on the POSIX data volume; the deployment is not recoverable from the S3 bucket alone. Back up both the RustFS bucket and `/data/apps/opencloud`.

The RustFS identity `opencloud` has only the repository policy in `rustfs-policy.json`, scoped to the `opencloud` bucket. Runtime secrets and the initial break-glass password are stored only in the existing `HomeLab` 1Password vault item `OpenCloud` and in Portainer's protected stack environment.

## Authentication

Pocket ID is the native OIDC provider. Four public PKCE clients cover the web, iOS, Android, and desktop applications: `opencloud-web`, `OpenCloudIOS`, `OpenCloudAndroid`, and `OpenCloudDesktop`. They are restricted to the Pocket ID group `infrastructure-admins`.

OpenCloud auto-provisions authenticated users into its built-in private directory by `preferred_username`. Pocket ID's `opencloud_role` custom claim maps the existing `infrastructure-admins` group to OpenCloud's `opencloudAdmin` role. Basic authentication is disabled; third-party WebDAV clients should use revocable OpenCloud app tokens.

The service is private to LAN and Tailscale. Caddy terminates TLS and does not place Tinyauth in front of OpenCloud because native web/mobile OIDC and WebDAV must reach the application directly.

## Operations

```bash
ssh ctr 'sudo docker compose -p opencloud -f /data/apps/opencloud/compose.yaml ps'
ssh ctr 'curl -fsS http://10.1.1.4:9200/healthz'
ssh s3 'rc bucket list s3/ | grep opencloud'
curl --resolve drive.l3b.cc.cd:443:10.1.1.3 https://drive.l3b.cc.cd/healthz
```

Import files through OpenCloud/WebDAV; never copy them directly into OpenCloud's internal metadata or S3 layout.

## Nextcloud migration and retirement

The transient `nextcloud-opencloud-migration` systemd job finished on
2026-09-22. The source contained 706 live files totaling 37,731,309,207 bytes.
On 2026-09-23, `rclone check --download --one-way` compared every live source
file with OpenCloud WebDAV and reported **706 matching files, zero differences**.
The single contact was copied to `contacts.vcf` in the OpenCloud Personal Space
and verified by SHA-256. OpenCloud then contained 707 files: the 706 live files
and that contact.

The old Nextcloud database had two public links, three empty calendars, one
contact, and no notes, comments, or tags. The owner chose to retire the links
and discard the 279 files in Nextcloud's deleted-items bin; no migration archive
or replacement public links were retained. The old Nextcloud Portainer stack,
containers, images, and staged host data were removed after verification. The
two extracted Nextcloud folders on the external SSD were also removed.
Migration-only runtime files and `rclone` were removed from `ctr`; the transient
cleanup unit completed successfully. Later on 2026-09-23, the owner requested
reformatting the entire external SSD as ext4. That erased the original
whole-system `linux-recovery.tar`; it is no longer a backup source.

OpenCloud application health and WebDAV content were verified. Sign-in and iOS
Files integration still require owner acceptance testing. Back up both the
OpenCloud metadata directory and RustFS bucket; neither is sufficient alone.
