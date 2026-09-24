# Cairn

Cairn is a fresh native deployment on the `s3` LXC at `10.1.1.8`, alongside RustFS. It runs as a static Rust binary under systemd; it is not a Docker or Portainer workload.

## Topology

| Service | Listener | URL | Exposure |
| --- | --- | --- | --- |
| Cairn S3/API | `10.1.1.8:7373` | `https://cairn-s3.l3b.cc.cd` | Public; S3 auth/policies apply |
| Cairn console | `10.1.1.8:7374` | `https://cairn.l3b.cc.cd` | LAN/Tailscale only |
| RustFS S3/API | `10.1.1.8:9000` | `https://s3.l3b.cc.cd` | LAN/Tailscale only |
| RustFS console | `10.1.1.8:9001` | `https://rustfs.l3b.cc.cd` | LAN/Tailscale only |

Caddy at `10.1.1.3` terminates TLS. Cairn binds only the LXC LAN address and trusts only `10.1.1.3/32` as its reverse proxy.

The API hostname has an explicit DNS-only Cloudflare A record to `150.129.31.154`, and Caddy does not apply its LAN/Tailscale source filter to that API route. The console retains the source filter and has no public DNS exception. The existing `public` Cairn bucket is currently empty and has no anonymous-read policy: the temporary DNS-guide object and policy were removed when the guide moved to Notion. Do not assume a bucket name alone makes objects public. Public API clients must use valid S3 credentials unless a specific bucket/object policy is deliberately added.

## Installation

The installed version is `v2026.09.13`, deployed with Cairn's official verified host installer:

```bash
curl -fsSL https://raw.githubusercontent.com/Harsh-2002/Cairn/main/install.sh -o /tmp/cairn-install.sh
sudo sh /tmp/cairn-install.sh \
  --host --yes --version v2026.09.13 \
  --data-dir /data/cairn \
  --expose-api --expose-console --acknowledge-public-http \
  --api-public-url https://cairn-s3.l3b.cc.cd \
  --console-public-url https://cairn.l3b.cc.cd
```

After installation, both listeners are restricted from `0.0.0.0` to `10.1.1.8` in `/etc/cairn/cairn.env`. The file also sets:

```text
CAIRN_TRUSTED_PROXIES=10.1.1.3/32
CAIRN_LOG_FORMAT=json
```

## Persistent state and secrets

- Binary: `/usr/local/bin/cairn`
- Service: `/etc/systemd/system/cairn.service`
- Environment and keys: `/etc/cairn/cairn.env`, mode `0600`
- Data, staging, and SQLite metadata: `/data/cairn`
- Database: `/data/cairn/cairn.db`

The database, staging tree, and object blobs must stay on the same filesystem because Cairn's durability protocol relies on atomic rename. The service runs as the dedicated `cairn` user and is enabled at boot.

The canonical `Cairn S3` item in the `HomeLab` 1Password vault contains the root access key, root secret key, console URL, and master key. These three secret values were recovered together from the latest historical Portainer Compose revision (`146/v6`) so the native service retains the original Cairn identity. The console username/access key is `iam.anuragvishwakarma@gmail.com`; Cairn uses the S3-style access key rather than a separate username. Do not change or lose the master key after data or sealed credentials exist.

## Validation

```bash
ssh s3 'systemctl is-enabled cairn; systemctl is-active cairn'
ssh s3 'curl -fsS http://10.1.1.8:7373/healthz'
ssh s3 'curl -fsS http://10.1.1.8:7373/readyz'
ssh s3 'set -a; . /etc/cairn/cairn.env; set +a; cairn validate-config'
```

The initial deployment was validated with an authenticated AWS CLI create/upload/download/delete round trip. The temporary validation bucket was removed afterward.

## Upgrade

Read the release notes and Cairn upgrade/rollback guide first. Keep `/etc/cairn/cairn.env` and `/data/cairn` together with the required offline backup, then use the official updater:

```bash
curl -fsSL https://raw.githubusercontent.com/Harsh-2002/Cairn/main/install.sh -o /tmp/cairn-install.sh
sudo sh /tmp/cairn-install.sh --host --update --yes
```

Confirm the listener remains bound to `10.1.1.8`, then repeat configuration, readiness, S3 round-trip, and public TLS checks.

References: [Cairn documentation](https://harsh-2002.github.io/Cairn/), [operations guide](https://github.com/Harsh-2002/Cairn/blob/main/docs/operations.md), and [upgrade/rollback guide](https://github.com/Harsh-2002/Cairn/blob/main/docs/upgrade-rollback.md).
