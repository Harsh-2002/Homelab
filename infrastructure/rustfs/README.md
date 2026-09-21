# RustFS S3

RustFS runs natively under systemd in unprivileged Debian LXC CT 105 (`s3`), not in Docker. It is a single-node, single-disk deployment: this is intentional. Do not claim erasure-coded or multi-node storage availability for this service.

## Topology

| Item | Value |
| --- | --- |
| Guest | `s3` / CT 105 |
| Address | `10.1.1.8` |
| Primary node | `px30` |
| HA target | `px10` |
| Replication | `105-0`, every 5 minutes |
| Placement rule | strict `px30` preferred, `px10` permitted |
| Resources | 2 vCPU, 4 GiB RAM, 512 MiB swap |
| Root filesystem | 100 GiB thin-provisioned `data:subvol-105-disk-0` |
| Object path | `/data/rustfs` |
| Runtime | RustFS v1.0.0 native package and systemd |
| Service ports | `10.1.1.8:9000` API, `10.1.1.8:9001` console |

The root filesystem is on Proxmox's `data` ZFS storage, so `/data/rustfs` is persisted and replicated with CT 105. The 100 GiB allocation is thin-provisioned; it does not reserve 100 GiB of physical space until objects consume it. Increase it online with `pct resize 105 rootfs +<size>G` on the current Proxmox host. Do not shrink it without an offline filesystem and data-capacity plan.

Proxmox HA can restart the guest on `px10` after a host failure once the most recent replication is available. It cannot make the single RustFS instance continuously available during a failover, and the five-minute replication interval is the possible data-loss window.

## Access and identity

| Purpose | Address | Exposure |
| --- | --- | --- |
| S3 API | `https://s3.l3b.cc.cd` | LAN/Tailscale only |
| Console | `https://rustfs.l3b.cc.cd` | LAN/Tailscale only |
| Native health check | `http://10.1.1.8:9000/health/ready` | LXC network only |

Caddy terminates TLS and proxies both private routes. The API intentionally remains private and is not compressed by Caddy so S3 object-transfer and signature behavior stays transparent. Do not add a public Cloudflare A record for `s3.l3b.cc.cd` unless public S3 write/read exposure is explicitly designed and approved.

Pocket ID is the native console OIDC provider. Its exact callback is `https://rustfs.l3b.cc.cd/rustfs/admin/v3/oidc/callback/default`. RustFS maps the flat `groups` claim directly to RustFS policy names, so the custom `infrastructure-admins` policy is the full equivalent of RustFS's built-in `consoleAdmin` policy. This permits only the existing Pocket ID `infrastructure-admins` group; no fixed OIDC role policy is used.

`HomeLab` → `RustFS - S3` is the sole credential item. It holds the root break-glass key, Pocket ID client secret, and dedicated `s3-admin` access key. Do not create a second item. The root key is used only by systemd/bootstrap recovery; `rc` and AWS CLI use `s3-admin`.

## Paths and commands

| Item | Path |
| --- | --- |
| Service unit | `/usr/lib/systemd/system/rustfs.service` |
| Real environment | `/etc/default/rustfs` (root, `0600`) |
| Data | `/data/rustfs` (`rustfs:rustfs`, `0750`) |
| RustFS binary | `/usr/bin/rustfs` |
| RustFS CLI | `/usr/local/bin/rc` |
| AWS CLI profile | `/root/.aws/{config,credentials}`, profile `s3` |

```bash
ssh s3 'systemctl status rustfs'
ssh s3 'journalctl -u rustfs -f'
ssh s3 'curl -fsS http://10.1.1.8:9000/health/ready | jq'
ssh s3 'rc ready s3'
ssh s3 'aws --profile s3 --endpoint-url http://10.1.1.8:9000 s3api list-buckets'
```

The `s3-admin` identity has RustFS's built-in `consoleAdmin` policy. Create limited application identities or service accounts for each actual workload instead of sharing this operator credential.

## Upgrade and recovery

Pin and verify a stable RustFS release before changing it. Do not deploy preview builds automatically. Take a Proxmox backup or confirm a recent `105-0` replication first, download the matching release checksum, verify it, install the package, and restart only after reviewing release notes:

```bash
ssh s3 'systemctl stop rustfs'
# Download the selected stable rustfs_<version>_amd64.deb and its SHA256SUMS, then verify with sha256sum -c.
ssh s3 'dpkg -i rustfs_<version>_amd64.deb && systemctl start rustfs && systemctl is-active rustfs'
```

Validate the native health endpoint, Caddy API health route, and an authenticated `aws s3api list-buckets` request after every upgrade. CT failover and restore tests should be scheduled separately; never start two RustFS instances against the same data tree.
