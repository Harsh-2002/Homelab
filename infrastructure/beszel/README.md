# Beszel monitoring

Beszel `v0.20.0` provides lightweight host, disk, ZFS, SMART, systemd, and Docker monitoring. The hub and agents use pinned native binaries managed by systemd; automatic application updates are disabled.

CT 104 also hosts the independent native Uptime Kuma service documented under `infrastructure/uptime-kuma/`. The services have separate Unix users, data directories, environment files, listeners, and systemd units, but intentionally share the LXC's HA and replication failure domain.

## Topology

| Item | Value |
| --- | --- |
| URL | `https://beszel.l3b.cc.cd` |
| Hub | CT 104 `beszel`, `10.1.1.7:8090` |
| Hub resources | 1 vCPU, 1 GiB RAM, 512 MiB swap, 10 GiB `local-zfs` |
| Primary node | `px10` |
| Replica node | `px30` |
| Agent transport | SSH-key pull mode on TCP `45876` |
| Monitored systems | `px10`, `px20`, `px30`, `dev`, `proxy`, `dns`, `auth`, `beszel`, `s3`, `orva`, `store`, `ctr` (12 total) |

Caddy terminates TLS and applies the private LAN/Tailscale policy. Pocket ID is configured as Beszel's native OIDC provider with callback `https://beszel.l3b.cc.cd/api/oauth2-redirect`.

## Hub paths

```text
binary:       /usr/local/bin/beszel
data:         /var/lib/beszel/beszel_data
environment:  /etc/beszel/beszel.env
service:      /etc/systemd/system/beszel.service
```

The hub runs as the dedicated `beszel` system account. Pocket ID must emit both `email` and `email_verified=true`: PocketBase deliberately ignores an unverified OIDC email, which makes Beszel reject the record as having a blank email. The owner's address was verified in Pocket ID, `USER_CREATION=true` was enabled only for the first successful link, and the persisted external-auth record was validated before returning `USER_CREATION=false`. New users therefore cannot self-create Beszel accounts. Password login remains available as a break-glass path.

## Agent design

Every agent runs as the dedicated `beszel` account. The hub initiates the connection using the public key tracked in `hub-key.pub`; there is no shared registration token or outbound management channel.

```text
binary:       /usr/local/sbin/beszel-agent
key:          /etc/beszel-agent/key
environment:  /etc/beszel-agent/agent.env
state:        /var/lib/beszel-agent
service:      /etc/systemd/system/beszel-agent.service
```

The agents receive `CAP_SYS_RAWIO` and `CAP_SYS_ADMIN` so `smartctl` can read SATA and NVMe health where the guest/host exposes the hardware, without running the whole process as root. Unprivileged LXC agents cannot see host physical disks merely because the service has these capabilities. Proxmox agents are members of `disk`; the `ctr` agent is additionally a member of `docker` for read access to `/var/run/docker.sock`.

On 2026-09-24, the missing agents were installed on `dev`, `proxy`, `dns`, `auth`, hub LXC `beszel`, `s3`, `orva`, and `store`; `ctr` and the three Proxmox hosts already ran the same current `v0.20.0` release. The new agent binary came from the pinned official `beszel-agent_linux_amd64.tar.gz` release and its published SHA-256 was verified before installation. Each guest has a dedicated `beszel` system account, LAN-IP-bound listener on port 45876, the hub public key at `/etc/beszel-agent/key`, and an enabled native systemd unit. All 12 records were registered in the hub for the existing owner and returned `up`. The three Talos K8s VMs (201–203) are intentionally excluded.

Beszel monitors the Proxmox hosts as Linux systems. It does not replace the Proxmox UI for cluster quorum, VM/LXC inventory, replication, or HA state. Kubernetes operations remain in Headlamp, Argo CD, Longhorn, and Metrics Server; no Beszel agent is installed in Talos.

## Authentication

Normal access uses the **Pocket ID** button on the Beszel login page. The OIDC client is restricted to the `infrastructure-admins` Pocket ID group. The matching verified Beszel user is `iam.anuragvishwakarma@gmail.com`.

The existing `HomeLab` 1Password items `Beszel Monitoring` and `Beszel PocketBase Superuser` contain the break-glass credentials; do not duplicate them. The existing PocketBase superuser password was set to its vault-stored value during the 2026-09-24 guest rollout and authentication was verified. Pocket ID OIDC and the owner user are unchanged. Never commit these values.

## Operations

Hub checks:

```bash
ssh root@10.1.1.7 'systemctl is-enabled beszel; systemctl is-active beszel; /usr/local/bin/beszel --version'
curl -fsS https://beszel.l3b.cc.cd/api/health
```

Agent checks:

```bash
for host in px10 px20 px30 proxy dns auth s3 store; do
  ssh "$host" 'systemctl is-enabled beszel-agent; systemctl is-active beszel-agent; /usr/local/sbin/beszel-agent --version'
done
systemctl is-active beszel-agent # dev, run locally
ssh orva 'systemctl is-active beszel-agent'
ssh root@10.1.1.7 'systemctl is-active beszel-agent'
```

Agent logs should show an SSH connection from `10.1.1.7`. All 12 systems must show `up` in the Beszel UI. The three Proxmox nodes should expose six `ONLINE` ZFS pools in total and physical devices under SMART.

## High availability

CT 104 is managed by Proxmox HA with failback enabled, two local restart attempts, and one relocation attempt. Strict rule `ct104-replica-nodes` permits px10 and px30, preferring px10. Replication job `104-0` copies the 10 GiB local-ZFS disk from px10 to px30 every five minutes.

```bash
ssh px10 'ha-manager status; ha-manager config | sed -n "/ct:104/,+8p"'
ssh px10 'ha-manager rules config --resource ct:104'
ssh px10 'pvesr status | grep -E "(^Job|104-0)"'
```

Beszel/PocketBase is single-writer. Never run the primary and replicated CT simultaneously. HA and replication improve availability but are not backups.

## Backup

Everything required to restore the hub is under `/var/lib/beszel/beszel_data`. Stop the service for a consistent filesystem copy or use Beszel's built-in backup function. Preserve file ownership and modes and keep a copy outside the Proxmox cluster.

```bash
ssh root@10.1.1.7 'systemctl stop beszel && tar --xattrs --acls -C / -czf /root/beszel-data-backup.tgz var/lib/beszel/beszel_data && systemctl start beszel'
scp root@10.1.1.7:/root/beszel-data-backup.tgz ./
```

Remove the temporary archive from the LXC after validating and storing the encrypted backup.

## Upgrade

Read the release notes, take a backup, and verify the release checksum. Install an explicit version on the hub and all agents; do not use `latest` or enable automatic updates on Proxmox hosts. After upgrading, verify versions, 12 `up` systems, ZFS/SMART collection, Docker collection, OIDC, and a new replication cycle.
