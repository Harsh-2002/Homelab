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
ssh s3 'rc bucket stat s3/opencloud'
curl --resolve drive.l3b.cc.cd:443:10.1.1.3 https://drive.l3b.cc.cd/healthz
```

Keep the staged Nextcloud recovery data until OpenCloud login, iOS Files integration, uploads, downloads, and the final data migration have been verified. Import files through OpenCloud/WebDAV; never copy them directly into OpenCloud's internal metadata or S3 layout.
