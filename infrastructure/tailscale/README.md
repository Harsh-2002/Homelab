# Tailscale

Tailscale runs directly on Proxmox hosts `px10`, `px20`, and `px30` as three approved, redundant subnet routers for `10.1.1.0/24`. Devices that need to initiate tailnet connections run their own Tailscale client; `dev` is the first such guest. There is no outbound gateway VIP, Keepalived, or custom NAT service.

| Device | LAN address | Tailnet address | Role |
| --- | --- | --- | --- |
| `px10` | `10.1.1.10` | `100.100.202.88` | Subnet router |
| `px20` | `10.1.1.20` | `100.115.39.43` | Subnet router |
| `px30` | `10.1.1.30` | `100.101.22.38` | Subnet router |
| `dev` | `10.1.1.5` | `100.70.45.76` | Direct tailnet client |
| `slate` | GCP | `100.122.33.37` | External monitoring host |

All three Proxmox hosts advertise exactly `10.1.1.0/24`, use `tag:subnet-router`, and have the route approved in Tailscale. Device-key expiry is disabled for the tagged subnet routers. Tailscale's own subnet-route SNAT and netfilter integration remain enabled. The hosts and `dev` have `accept-dns=false`, `accept-routes=false`, Tailscale SSH disabled, and native auto-update enabled. `dev` advertises no subnet and uses internal AdGuard `10.1.1.2` through its ordinary network configuration. Tailscale does not manage its DNS. The Proxmox hosts also retain their ordinary internal DNS and do not learn the LAN route from another subnet router.

## Why the gateway VIP was retired

The former `10.1.1.9` Keepalived VIP attempted to route guest traffic to the tailnet through the active Proxmox host. On 2026-09-28, a targeted nft trace showed that traffic from firewall-enabled VM 100 reached NAT postrouting first on Proxmox firewall bridge `fwbr100i0`, not on `tailscale0`. The custom masquerade rule did not match; conntrack recorded an untranslated, unreplied flow. Proxmox [documents this firewall-bridge NAT interaction](https://github.com/proxmox/pve-docs/blob/master/pve-network.adoc). Rather than add conntrack-zone rules on every host for a small number of clients, the owner chose direct Tailscale clients where outbound access is needed. The VIP, Keepalived package/configuration, custom nft table/service, health-check script, and `dev`'s route via `10.1.1.9` were removed from all three hosts and `dev`. The three inbound subnet routers remain.

Do not reintroduce the old VIP route, router static route to `10.1.1.9`, or the deleted Keepalived files. The TP-Link XC220-G3v supports static routing, but no router route is needed in this design. Guests without their own Tailscale client do not initiate connections to tailnet-only addresses. The `orva` VM intentionally blocks outbound `100.64.0.0/10` and must remain isolated.

## Deployment and recovery

The host-only files retained in this repository are:

| Repository file | Host path | Purpose |
| --- | --- | --- |
| `99-tailscale.conf` | `/etc/sysctl.d/99-tailscale.conf` | IP forwarding for subnet routing |
| `tailscale-gro.service` | `/etc/systemd/system/tailscale-gro.service` | Persistent GRO performance setting |

For a replacement Proxmox host, install Tailscale from its official Debian repository, enroll using `scripts/ts.sh` and a short-lived tagged key from 1Password, apply the two host files, and enable `tailscaled` and `tailscale-gro`. Advertise `10.1.1.0/24` with `accept-dns=false`, `accept-routes=false`, Tailscale SSH disabled, and auto-update enabled. Approve the new subnet route in the Tailscale admin console. Do not reuse the revoked historical enrollment key. The tag policy is:

```json
"tagOwners": {
  "tag:subnet-router": []
}
```

On `dev` (Debian 13), Tailscale `1.102.4` was installed from the official stable APT repository and authenticated through the one-time device sign-in. Its persistent daemon is `tailscaled.service`; no route through a Proxmox host is needed. The `~/.ssh/config` alias `slate` pins `HostName 100.122.33.37`, `User root`, and `HostKeyAlias 100.122.33.37`. The IP's ED25519 host key was verified against the existing known-hosts entry before this alias was used. Do not rely on bare `slate` DNS: the LAN search suffix plus wildcard DNS sends unknown short names to the proxy.

## External monitoring on slate

`slate` is reachable over Tailscale from `dev` and reaches `10.1.1.2` through the approved subnet routers. As checked on 2026-09-28, it has `accept-dns=false`, `accept-routes=true`, and auto-update enabled. Neither ntfy nor Uptime Kuma is installed yet. The planned deployment is independent of the home network: ntfy handles alerts, and Uptime Kuma monitors home availability from outside. Keep its ordinary public DNS independent of AdGuard so a home outage cannot suppress alerts. If private `l3b.cc.cd` names are needed, configure split DNS deliberately instead of making AdGuard the global resolver for `slate`.

The owner chose native services on `slate`, not Docker or a Portainer Agent. A briefly tested Docker/Agent installation on 2026-09-28 was fully removed, including its images, runtime data, and APT repository. `ctr` was never enrolled in Tailscale; the interrupted package download and temporary repository files were removed. Keep its existing Portainer installation unchanged. ntfy supports a native Debian package and systemd unit. Uptime Kuma is a Node.js application (not a Go binary); a native install needs Node.js, its application dependencies, and a managed service. Neither has been deployed on `slate` yet.

For private web access, bind a future reverse proxy to `slate`'s Tailscale address and leave the public cloud firewall closed. Caddy DNS-01 can obtain a certificate without opening public ports 80/443, but certificate issuance alone does not expose a service. Decide how home services without a Tailscale client will publish ntfy alerts before locking down its API. Self-hosted ntfy on iOS also needs its documented upstream push configuration for prompt background notifications; test this end to end before relying on it for outages.

## Verification

```bash
for node in px10 px20 px30; do
  ssh "$node" 'systemctl is-active tailscaled tailscale-gro; tailscale debug prefs | jq "{CorpDNS,RouteAll,RunSSH,AdvertiseRoutes,AutoUpdate}"'
done
systemctl is-active tailscaled
sudo tailscale debug prefs | jq '{CorpDNS,RouteAll,RunSSH,AdvertiseRoutes,AutoUpdate}'
ip route get 100.122.33.37
tailscale ping slate
ssh slate 'hostname; id -un'
```

Expected: all four local Tailscale daemons active; `accept-dns` and `accept-routes` false; auto-update true; each Proxmox host advertises `10.1.1.0/24`; `dev` advertises nothing and routes `slate` via `tailscale0`. `ssh slate` reaches `root@slate`. The retired `10.1.1.9` address, Keepalived, and `tailscale_gateway` nft table must remain absent.
