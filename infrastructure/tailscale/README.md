# Tailscale HA gateway

Tailscale `1.102.4` and Keepalived `2.3.3` run directly on all three Proxmox hosts. Tailscale provides HA access from the tailnet to LAN `10.1.1.0/24`. Keepalived provides floating gateway `10.1.1.9` for selected LAN guests that need to initiate connections to Tailscale addresses.

## Topology

| Host | LAN | Tailscale | VRRP priority |
| --- | --- | --- | ---: |
| px10 | `10.1.1.10` | `100.100.202.88` | 150 |
| px20 | `10.1.1.20` | `100.115.39.43` | 120 |
| px30 | `10.1.1.30` | `100.101.22.38` | 90 |
| Floating gateway | `10.1.1.9` | — | — |

All nodes advertise exactly `10.1.1.0/24`. They deliberately use `accept-dns=false` and `accept-routes=false`: Proxmox retains AdGuard/Cloudflare DNS, and an HA subnet router must not learn its directly attached LAN through another router. They are not exit nodes and Tailscale SSH is disabled. Tailscale manages its netfilter chains, subnet-route SNAT retains its safe default, and Tailscale's native auto-update is enabled.

Inbound tailnet-to-LAN traffic uses Tailscale's native subnet-router election. Outbound LAN-to-tailnet traffic uses Keepalived's VIP. A narrow nftables rule masquerades only `10.1.1.0/24` traffic leaving `tailscale0` for `100.64.0.0/10`; this makes the outbound path follow the VIP owner independently of Tailscale's inbound-primary selection.

The enrollment key is temporary. It is read from 1Password only during enrollment, written to `/run/tailscale-auth-key`, and deleted immediately. It is never stored in this repository or on a host.

## Persistent host files

| Repository file | Host path |
| --- | --- |
| `99-tailscale.conf` | `/etc/sysctl.d/99-tailscale.conf` |
| `tailscale-gro.service` | `/etc/systemd/system/tailscale-gro.service` |
| `tailscale-gateway.nft` | `/etc/tailscale-gateway.nft` |
| `tailscale-gateway.service` | `/etc/systemd/system/tailscale-gateway.service` |
| `check-tailscale` | `/usr/local/libexec/check-tailscale` |
| `keepalived-pxNN.conf` | `/etc/keepalived/keepalived.conf` |

The health script checks only local forwarding capability: `tailscaled`, `tailscale0`, the gateway NAT rule, backend state, and node-online state. Remote application availability belongs in Uptime Kuma and must not remove the gateway VIP from every node.

Keepalived uses unicast VRRP over `vmbr0`. The Proxmox host firewall was disabled when deployed, so no VRRP rule was necessary. If that firewall is enabled later, allow IP protocol 112 between `10.1.1.10`, `10.1.1.20`, and `10.1.1.30` before enabling it.

## Tailscale control plane

`10.1.1.0/24` is approved on all three machines. Identical approved prefixes are required for Tailscale subnet-router failover. All three machines use the non-user identity `tag:subnet-router`, and their device-key expiry is disabled. The tailnet policy declares the tag with an empty owner list; tailnet Owners and Admins retain implicit authority to assign it:

```json
"tagOwners": {
  "tag:subnet-router": []
}
```

The reusable enrollment key was revoked through the Tailscale API after tagging. Revocation did not disconnect the enrolled nodes. The separate short-lived API access token remains in 1Password for administration and must be replaced when it expires.

For tailnet DNS, prefer split DNS for `l3b.cc.cd` through `10.1.1.2`. Do not enable Tailscale DNS acceptance on the Proxmox hosts. Make AdGuard a global tailnet resolver only after remote clients can reach it reliably through the approved subnet routers.

## External monitoring node

GCP free-tier VM `slate` is online at Tailscale address `100.122.33.37` and offers an exit node. It currently accepts the tailnet DNS configuration, whose only global nameserver was `10.1.1.2` when reviewed on 2026-09-22. This makes ordinary DNS on the external notification node dependent on the home internet, subnet routers, and AdGuard, so it is not the desired final state.

The planned DNS design is:

- keep MagicDNS enabled;
- keep `accept-dns=true` on `slate` so MagicDNS and split DNS work;
- do not override each device's local resolver for ordinary public DNS;
- remove `10.1.1.2` as a global tailnet nameserver;
- configure `10.1.1.2` only as the restricted resolver for `l3b.cc.cd`;
- let `slate` use its local GCP resolver for public domains;
- do not maintain Homelab names in `/etc/hosts`.

Do not model `10.1.1.2` followed by `1.1.1.1` as ordered primary/fallback DNS. Tailscale or the operating system can query multiple global resolvers in parallel, reorder them, or use whichever responds first. Split DNS is deterministic when private and public answers differ.

A future Uptime Kuma instance on `slate` should complement, not replace, the internal instance. Its scope is the external viewpoint: home internet, Tailscale and subnet routing, AdGuard DNS, public endpoints, and selected private endpoints. Keep ordinary DNS and ntfy delivery independent of the home network so an AdGuard or home outage cannot suppress the alert. Avoid duplicate monitors and notifications between the internal and external Kuma instances.

This section records an approved design only. The tailnet DNS change and external Uptime Kuma deployment have not yet been applied.

## Guest routing

Only guests that need to initiate traffic toward Tailscale require a persistent route:

```text
100.64.0.0/10 via 10.1.1.9
```

For a systemd-networkd guest, add this to its existing `.network` file:

```ini
[Route]
Destination=100.64.0.0/10
Gateway=10.1.1.9
```

Do not add three weighted routes or guest-side health scripts. Keepalived owns failover, and the route remains valid when Proxmox HA relocates a guest to another host on the same LAN.

## Deployment and recovery

Enroll a replacement node with `scripts/ts.sh`, then copy the tracked files and enable the services. Example for px10:

```bash
scp infrastructure/tailscale/99-tailscale.conf px10:/etc/sysctl.d/99-tailscale.conf
scp infrastructure/tailscale/tailscale-gro.service px10:/etc/systemd/system/tailscale-gro.service
scp infrastructure/tailscale/tailscale-gateway.nft px10:/etc/tailscale-gateway.nft
scp infrastructure/tailscale/tailscale-gateway.service px10:/etc/systemd/system/tailscale-gateway.service
scp infrastructure/tailscale/check-tailscale px10:/usr/local/libexec/check-tailscale
scp infrastructure/tailscale/keepalived-px10.conf px10:/etc/keepalived/keepalived.conf
ssh px10 'chmod 755 /usr/local/libexec/check-tailscale && sysctl --system && systemctl daemon-reload && systemctl enable --now tailscaled tailscale-gro tailscale-gateway keepalived'
```

Substitute the correct hostname and host-specific Keepalived file. Validate before restarting Keepalived:

```bash
keepalived -t -f /etc/keepalived/keepalived.conf
```

## Verification

```bash
tailscale debug prefs | jq '{RouteAll,CorpDNS,RunSSH,AdvertiseRoutes,NoSNAT,AutoUpdate}'
systemctl is-active tailscaled tailscale-gro tailscale-gateway keepalived
nft list table ip tailscale_gateway
ip -4 -br address show vmbr0
journalctl -u keepalived -n 30 --no-pager
```

Exactly one host must own `10.1.1.9/24`. Controlled tests moved the VIP from px10 to px20 in under five seconds and back. A guest route was temporarily installed on dev and successfully reached remote tailnet node `slate` through both px10 and px20. The temporary dev route was removed after testing.

## Removal

Remove persistent guest routes first. Then stop Keepalived on all nodes before removing Tailscale so the VIP cannot remain available without a tailnet path:

```bash
systemctl disable --now keepalived tailscale-gateway tailscale-gro tailscaled
tailscale logout
```
