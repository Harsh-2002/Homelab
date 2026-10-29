# Tailscale reachability audit, 2026-10-29

## Scope and results

Upgraded the three Proxmox subnet routers and `dev` to Tailscale **1.104.4**.
The daemons rejoined individually; the existing subnet/SNAT/DNS preferences were
preserved. See [upgrade procedure and exclusions](README.md#upgrade-and-access-audit-2026-10-29).

Tested the existing HTTPS service names from LAN and from native Uptime Kuma
2.5.5 on the external `slate` host. The external run observed **46 of 47** checks
UP: **43/44 HTTPS** targets and **3/3 TCP** targets. Of the HTTPS targets,
**33/34 private** targets passed, including OpenCode. Public targets passing from
slate establish availability from that host, not a separate general-internet audit.

Argo CD is the exception: LAN HTTP 200; external HTTP 403. Public DNS points its
hostname at the home WAN address for the public webhook, but the UI remains
private in Caddy. The external host's public DNS therefore takes a different path
from internal DNS. The shared private proxy path itself worked for other private
services. Use internal DNS over Tailscale for the UI; do not broaden its Caddy
allowlist or replace the public record without preserving webhook delivery.
No client-specific fault on the owner's offline phone/Mac was established.

The additional `metrics.l3b.cc.cd` check is **not a health test**: Caddy matches only
POST `/api/v1/write`. GET has no matching route and closes the connection, on LAN
and externally. No samples or synthetic write requests were sent. This says
nothing about remote-write ingestion health.

Checks verified DNS, connection and expected HTTP/auth responses, not complete
application workflows. HTTP redirects and native 401/404/415 responses count as
endpoint reachability. S3/registry health paths distinguish native authentication
from the private proxy's 403 gate. TLS verification stayed enabled. No login or
application data was changed.

## External observations

Observed around 02:38–02:39 UTC; Argo CD was rechecked at 02:44 UTC.

| Hostname | Probe | External result |
| --- | --- | --- |
| `argocd.l3b.cc.cd` | `HTTPS /` | HTTP 403; private UI via public address |
| `auth.l3b.cc.cd` | `HTTPS /` | Reachable |
| `beszel.l3b.cc.cd` | `HTTPS /` | Reachable |
| `cairn-s3.l3b.cc.cd` | `HTTPS /` | Reachable |
| `cairn.l3b.cc.cd` | `HTTPS /` | Reachable |
| `dev.l3b.cc.cd` | `HTTPS /` | Reachable |
| `dns.l3b.cc.cd` | `HTTPS /` | Reachable |
| `docs.l3b.cc.cd` | `HTTPS /` | Reachable |
| `downloads.l3b.cc.cd` | `HTTPS /` | Reachable |
| `drive.l3b.cc.cd` | `HTTPS /` | Reachable |
| `frigate.l3b.cc.cd` | `HTTPS /` | Reachable |
| `grafana.l3b.cc.cd` | `HTTPS /` | Reachable |
| `headlamp.l3b.cc.cd` | `HTTPS /` | Reachable |
| `hermes.l3b.cc.cd` | `HTTPS /` | Reachable |
| `home.l3b.cc.cd` | `HTTPS /` | Reachable |
| `l3b.cc.cd` | `HTTPS /` | Reachable |
| `login.l3b.cc.cd` | `HTTPS /` | Reachable |
| `longhorn.l3b.cc.cd` | `HTTPS /` | Reachable |
| `media.l3b.cc.cd` | `HTTPS /` | Reachable |
| `memory.l3b.cc.cd` | `HTTPS /` | Reachable |
| `n8n.l3b.cc.cd` | `HTTPS /` | Reachable |
| `notes.l3b.cc.cd` | `HTTPS /` | Reachable |
| `oc.l3b.cc.cd` | `HTTPS /` | Reachable |
| `omni-api.l3b.cc.cd` | `HTTPS /` | Reachable |
| `omni-kube.l3b.cc.cd` | `HTTPS /` | Reachable |
| `omni.l3b.cc.cd` | `HTTPS /` | Reachable |
| `orva.l3b.cc.cd` | `HTTPS /` | Reachable |
| `photos.l3b.cc.cd` | `HTTPS /` | Reachable |
| `pin.l3b.cc.cd` | `HTTPS /` | Reachable |
| `portainer.l3b.cc.cd` | `HTTPS /` | Reachable |
| `px.l3b.cc.cd` | `HTTPS /` | Reachable |
| `px10.l3b.cc.cd` | `HTTPS /` | Reachable |
| `px20.l3b.cc.cd` | `HTTPS /` | Reachable |
| `px30.l3b.cc.cd` | `HTTPS /` | Reachable |
| `registry.l3b.cc.cd` | `HTTPS /v2/` | Reachable |
| `router.l3b.cc.cd` | `HTTPS /` | Reachable |
| `rustfs.l3b.cc.cd` | `HTTPS /health` | Reachable |
| `s3.l3b.cc.cd` | `HTTPS /minio/health/live` | Reachable |
| `sb.l3b.cc.cd` | `HTTPS /auth/v1/health` | Reachable |
| `status.l3b.cc.cd` | `HTTPS /` | Reachable |
| `store.l3b.cc.cd` | `HTTPS /` | Reachable |
| `supabase.l3b.cc.cd` | `HTTPS /` | Reachable |
| `theking.l3b.cc.cd` | `HTTPS /` | Reachable |
| `torrent.l3b.cc.cd` | `HTTPS /` | Reachable |
| `smb.l3b.cc.cd` | `TCP 445` | Reachable |
| `k8s.l3b.cc.cd` | `TCP 6443` | Reachable |
| `sb.l3b.cc.cd` | `TCP 5432` | Reachable |

## Monitoring preservation and limits

Temporary probes had empty notification mappings, sent no alerts, and were all
removed after each run (47 initial, two rechecks). A final authenticated read
confirmed exactly the original six monitors remained, all UP: public web,
private proxy, home DNS, and three Proxmox APIs. Existing notification settings
and monitors were not edited. No permanent audit monitors were added.

The external probes used the existing monitoring API and saved vault login, not
SSH access or a new service. No credentials, API responses containing tokens,
one-time approval URLs or expanded configurations are retained here.

No ACL/DNS/firewall/proxy changes, new public exposure, service placement changes,
or architecture relationship changes were made. The owner deferred admin/SSH
access; slate and offline mobile/desktop clients remain outside this upgrade.
