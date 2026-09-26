# Infrastructure metrics

Grafana `13.2.2` and single-node VictoriaMetrics `v1.152.0` run as native systemd services in Beszel CT 104. The stack collects metrics only, not logs or traces. The Grafana UI is private at `https://grafana.l3b.cc.cd`. The VictoriaMetrics API is not a browser service; only authenticated `POST /api/v1/write` at `https://metrics.l3b.cc.cd` is proxied for Kubernetes vmagent.

## Topology

| Component | Placement | Purpose |
| --- | --- | --- |
| Grafana | CT 104, `10.1.1.7:3000` | Dashboards and queries |
| VictoriaMetrics | CT 104, `10.1.1.7:8428` | 30-day time-series storage and LAN scrapes |
| Proxmox exporter | CT 104, `127.0.0.1:9221` | Read-only PVE cluster, guest, storage, HA and replication metrics |
| Node Exporter | px10/20/30 and Debian guests: dns, proxy, dev, auth, beszel, ctr, s3, orva, store | Filesystems, CPU, memory, disk and network |
| vmagent | Kubernetes `monitoring` namespace | In-cluster scrape and remote write |
| kube-state-metrics | Kubernetes `monitoring` namespace | Object-state metrics |
| Longhorn managers | Kubernetes `longhorn-system` | Native storage metrics |

CT 104 has 2 vCPU, 3 GiB RAM and a 30 GiB `local-zfs` disk. Proxmox HA and five-minute replication still target px10 (primary) and px30 (replica). Beszel and Uptime Kuma share this CT, so their data and the metrics database share its failure domain. Replication is not an independent backup.

VictoriaMetrics keeps samples for `30d`; the 3 GiB minimum-free-disk guard rejects new writes before the CT fills. This guard is not size-based rotation. Cache allowance is 512 MiB and per-query working memory is limited to 128 MiB. Scrapes run every 30 seconds, except cAdvisor at 60 seconds. Review actual disk growth and active-series count after several days. The database is ZFS-local, not on SMB/NFS.

## Collection and storage interpretation

The central scrape file covers VictoriaMetrics, three Proxmox nodes, nine Debian VM/LXC guests, and three PVE API targets. PVE API access uses dedicated token `metrics@pve!exporter` with `PVEAuditor` at `/`. The exporter disables its per-guest config collector to reduce API calls. Its private config is `/etc/pve-exporter/pve.yml`. The PVE API uses node certificates issued for `px*.local`, not the LAN IPs; this read-only, LAN-only exporter therefore sets `verify_ssl: false`. Its listener is loopback-only.

Node Exporter listens only on each host's `10.1.1.x:9100`, not on Tailscale/public interfaces. Static scrape targets carry a `host` label so tables show names rather than IPs. A five-minute ZFS textfile timer on each Proxmox host publishes pool allocation and dataset usage. The separate daily directory timer on `ctr` and `store` scans only immediate subdirectories under `/data` and `/srv/AV`, respectively; it runs with low CPU and idle I/O priority at 03:15 UTC. Those are snapshots, not real-time file indexes. On `store`, `backup-textfile.timer` scans the protected guests' completed PX backup archives every 15 minutes and exports their latest archive timestamps; it requires both the archive and a log containing `Finished Backup of VM`. A timestamp is evidence of a completed archive, not a verified restore.

Kubernetes vmagent uses bounded local buffering (512 MiB per remote-write URL, 1 GiB `emptyDir`) and sends over HTTPS through Caddy. Its queue survives a short backend outage but not pod replacement. Kubernetes Secret `vmagent-remote-write` comes from the `VictoriaMetrics API` 1Password item; it is intentionally not in Git. kube-state-metrics covers selected object types. Longhorn's existing ingress NetworkPolicy blocks arbitrary pods, so `allow-vmagent-metrics` permits only monitoring vmagent on TCP 9500. Kubelet scraping uses a service-account bearer token; the kubelet certificate is not trusted through the Kubernetes API CA, so that internal scrape connection skips certificate verification. The API server and remote-write connection retain normal TLS verification.

Grafana provisions three linked dashboards, with `Infrastructure Overview` as the home screen:

| Dashboard | SRE question it answers |
| --- | --- |
| Infrastructure Overview | Are the three PVE and K8s nodes healthy, are scrapes failing, are native backups overdue, and how are CPU, memory, PVE storage and Longhorn trending? |
| Compute & Guests | Which guest is running where, which guest or Kubernetes namespace is consuming compute, and which Linux mount or replication job needs attention? |
| Storage & Backups | Which PVE datastore, ZFS pool/dataset, Longhorn disk, ext4 mount, or daily-scanned data directory consumes capacity, and how old is each protected PX backup? |

The backup-age red threshold is 36 hours. Kubernetes VMs are intentionally excluded from the native PX backup job; do not interpret the protected guest count as all cluster guests. `pve_disk_usage_bytes` can be zero for a VM even while its filesystem contains data; use the guest mount panel and ZFS dataset view for actual occupancy. Talos Kubernetes VMs do not run Node Exporter; kubelet/cAdvisor and Longhorn cover their workloads and storage. Do not sum all storage panels together: PVE may advertise the same shared storage on multiple nodes, ZFS parents include child usage, and Longhorn physical use includes replicas. The dashboards show shared PX and ISO storage once. The daily directory inventory provides the next step when an ext4 filesystem such as `/data` grows.

## Authentication and secrets

Grafana uses native Pocket ID Generic OAuth with PKCE and callback `https://grafana.l3b.cc.cd/login/generic_oauth`. The `grafana` client is restricted to Pocket ID group `infrastructure-admins`, which maps to Grafana `Admin`; local `admin` remains break-glass. Caddy applies the private LAN/Tailscale source policy. Normal user sign-up is disabled; OIDC may create a user only after Pocket ID admits the restricted group.

HomeLab 1Password items, one per purpose:

| Item | Purpose |
| --- | --- |
| `Grafana` | Local break-glass login, specific site only |
| `Pocket ID OIDC - grafana` | Confidential OIDC client secret |
| `VictoriaMetrics API` | Basic auth for Grafana queries and vmagent writes |
| `Proxmox Metrics Exporter` | Read-only PVE API token |

Grafana reads secrets from root-only `/etc/grafana/grafana-secret.env`; VictoriaMetrics reads `/etc/victoriametrics/api-password`; vmagent mounts a Kubernetes Secret. None of these values belong in Git or Notion.

## Tracked configuration and deployed paths

| Repository source | Deployed path |
| --- | --- |
| `grafana.ini` | `/etc/grafana/grafana.ini` |
| `grafana-oidc.conf` | `/etc/systemd/system/grafana-server.service.d/oidc.conf` |
| `datasource.yml` | `/etc/grafana/provisioning/datasources/victoria.yml` |
| `dashboards.yml`, `infrastructure.json`, `proxmox-guests.json`, `storage.json` | `/etc/grafana/provisioning/dashboards/infrastructure.yml`, `/etc/grafana/dashboards/` |
| `victoriametrics.service`, `scrape.yml` | `/etc/systemd/system/victoriametrics.service`, `/etc/victoriametrics/scrape.yml` |
| `pve-exporter.service` | `/etc/systemd/system/pve-exporter.service` |
| `zfs-textfile.*`, `directory-textfile.*`, `backup-textfile.*` | `/usr/local/sbin/` and `/etc/systemd/system/` on measured hosts; backup timer only on `store` |
| `gitops/apps/monitoring/` | Argo CD Application `monitoring` |

VictoriaMetrics data is `/var/lib/victoriametrics`; Grafana's SQLite database is `/var/lib/grafana/grafana.db`; Beszel data remains `/var/lib/beszel/beszel_data`. PVE exporter runs from `/opt/pve-exporter`, a Python virtual environment pinned at package version `3.10.0`.

## Verification and maintenance

Native Proxmox backups are stored on the cluster-wide `PX` CIFS storage. A storage-capacity or successful-task metric is not a promise that every guest has a recoverable backup; confirm the backup set and periodically perform a test restore.

```bash
ssh root@10.1.1.7 'systemctl is-enabled grafana-server victoriametrics pve-exporter; systemctl is-active grafana-server victoriametrics pve-exporter; df -h /; free -h'
curl -fsS https://grafana.l3b.cc.cd/api/health
kubectl -n monitoring get deployments,pods
kubectl -n monitoring logs deployment/vmagent --tail=50
kubectl -n longhorn-system get networkpolicy allow-vmagent-metrics
for host in px10 px20 px30; do ssh "$host" 'systemctl is-active prometheus-node-exporter zfs-textfile.timer'; done
ssh ctr 'systemctl is-active prometheus-node-exporter directory-textfile.timer'
ssh store 'systemctl is-active prometheus-node-exporter directory-textfile.timer'
ssh store 'systemctl is-active backup-textfile.timer; systemctl status backup-textfile.service --no-pager'
```

The `up` query in Grafana Explore should return `1` for every target. Query `sum by(job)(up)` for counts and `sum(up == bool 0)` for failures. Check `storage_directory_inventory_timestamp_seconds` and `pve_backup_inventory_timestamp_seconds` for staleness, and vmagent queue/error counters if Kubernetes metrics stop. `pve_backup_latest_timestamp_seconds{vmid="204"}` is the latest completed PX archive for guest 204; a zero value means no matching completed archive. After changing the vmagent scrape ConfigMap, roll its Deployment because the file is mounted through `subPath`.

To rebuild the in-cluster collector, create namespace `monitoring` and its `vmagent-remote-write` Secret from the HomeLab 1Password `VictoriaMetrics API` credential, then sync the `monitoring` Argo CD Application. Do not commit the Secret. If the remote-write password rotates, update the VictoriaMetrics password file, Grafana environment, and Kubernetes Secret together, then restart affected services/pod. Read [VictoriaMetrics single-node](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/), [vmagent](https://docs.victoriametrics.com/vmagent/), [Grafana Generic OAuth](https://grafana.com/docs/grafana/latest/setup-grafana/configure-access/configure-authentication/generic-oauth/), and [Longhorn monitoring](https://longhorn.io/docs/1.12.1/monitoring/prometheus-and-grafana-setup/) before upgrades.
