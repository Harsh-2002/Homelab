# DNS

DNS LXC `10.1.1.2` runs:

- AdGuard Home `v0.107.79` on TCP/UDP 53 and management port 3000.
- Unbound `v1.26.1` on `127.0.0.1:5335` as the recursive upstream.
- HaGeZi Multi PRO and HaGeZi TIF Medium blocklists.

The protected active configuration is `/opt/AdGuardHome/AdGuardHome.yaml`. It is not copied into Git because it contains the administrator password hash and operational state. The safe desired DNS fragments are tracked as `adguard-rewrites.yaml`, `unbound-local.conf`, and `unbound-recursive.conf`.

The sanitized, shareable overview is [SHAREABLE-SETUP.md](SHAREABLE-SETUP.md) and the separate Notion page [AdGuard Home + Unbound: my DNS setup](https://app.notion.com/p/AdGuard-Home-Unbound-my-DNS-setup-3e5d3ccfb520818b8546c4dbca0ecdce). No copy is hosted in S3. On 2026-09-27, the previously missing Unbound loopback/port/cache settings caused a real restart failure: Unbound bound port 53, while AdGuard was configured to query port 5335. The tracked `unbound-recursive.conf` was installed at `/etc/unbound/unbound.conf.d/recursive.conf`; `unbound-checkconf`, a cold service restart, direct port-5335 recursion, and AdGuard port-53 queries all passed.

Proxy-managed DNS uses one apex A rewrite and one wildcard CNAME rewrite:

| Name | Type | Answer |
| --- | --- | --- |
| `l3b.cc.cd` | A | `10.1.1.3` |
| `*.l3b.cc.cd` | CNAME | `l3b.cc.cd` |

Adding a new Caddy hostname requires only a Caddy route; no additional AdGuard rewrite is required.

## Public DNS exposure policy

Cloudflare is intentionally private by default. Its apex A record is DNS-only and points `l3b.cc.cd` to the proxy's private address `10.1.1.3`; the existing wildcard CNAME therefore resolves all otherwise-unlisted public names to that private address. Public clients cannot use private RFC1918 addresses, so a new Caddy hostname is not internet-reachable merely because it exists.

To expose a deliberate exception, add an explicit DNS-only public A record for that hostname in Cloudflare. Current records pointing to `150.129.31.154` are `argocd`, `photos`, `pin`, `registry`, `orva`, `media`, `store`, and `cairn-s3`. External monitoring records `ntfy` and `watch` instead point to slate at `8.235.70.28`; their exact internal exceptions match. Caddy keeps every Argo CD path private except its signed webhook, while the public application routes rely on their native authentication. Do not proxy these records through Cloudflare until Caddy is explicitly configured to trust Cloudflare client-IP headers.

Use `/usr/local/bin/cf` on `dev` to inspect or change Cloudflare records. It defaults to a responsive bordered table; add `--plain` to `list` or `get` for tab-separated script output. Its configuration is `/etc/caddy/cloudflare.env`, with `CF_ZONE=l3b.cc.cd`; the API token remains outside Git.

Direct-host exceptions use AdGuard CNAME-exception entries that pass through to exact local A records in Unbound:

| Name | Answer |
| --- | --- |
| `dev.l3b.cc.cd` | `10.1.1.5` |
| `store.l3b.cc.cd` | `10.1.1.3` (public static storefront via Caddy) |
| `ntfy.l3b.cc.cd` | `8.235.70.28` (external ntfy on slate) |
| `watch.l3b.cc.cd` | `8.235.70.28` (external Uptime Kuma on slate) |
| `smb.l3b.cc.cd` | `10.1.1.12` |
| `k8s.l3b.cc.cd` | `10.1.1.200` |
| `k8s-201.l3b.cc.cd` | `10.1.1.201` |
| `k8s-202.l3b.cc.cd` | `10.1.1.202` |
| `k8s-203.l3b.cc.cd` | `10.1.1.203` |

Do not replace these pass-through entries with exact A rewrites: AdGuard Home v0.107.79 gives the wildcard legacy rewrite precedence. Unbound owns the exception A records. `store.l3b.cc.cd` is the public storefront on Caddy; the storage LXC remains `10.1.1.12`, reachable by the `store` SSH alias and `smb.l3b.cc.cd` for AV, BACKUP, and ISO shares.

Do not configure public DNS as a second resolver on split-horizon infrastructure clients. During the 2026-09-27 DNS outage, `ctr`'s `systemd-resolved` selected `1.1.1.1` and continued returning the public wildcard/proxy address for `smb.l3b.cc.cd` after AdGuard recovered. That broke its SMB automount and Motrix. DNS redundancy requires a second *internal* resolver with the same local records, not a public fallback. This is a single DNS-instance dependency until then.

Router setting reported by the owner: primary DNS `10.1.1.2`, secondary `1.1.1.2`. It is not yet verified whether these are LAN DHCP-advertised servers, WAN DNS for the router itself, or inputs to a DNS relay. If the public address is handed to LAN clients or used by the router relay, it can bypass private records and AdGuard filtering. Recommended LAN DHCP DNS is only `10.1.1.2` until a second internal resolver exists; router-only WAN DNS can be assessed separately. No router setting was changed here.

The three Proxmox hosts, all six running LXCs (`proxy`, `dns`, `auth`, `beszel`, `s3`, `store`), Debian VMs (`dev`, `orva`, `ctr`), and all three Talos nodes now use only `10.1.1.2`. LXC DNS is pinned in Proxmox guest configuration and the live `/etc/resolv.conf`; its tracked template is `lxc-resolv.conf`. The Debian VMs have both Proxmox cloud-init nameserver settings and tracked guest Netplan files (`client-netplan/` and `../ctr/50-cloud-init.yaml`). DHCPv6 and RA DNS are disabled where applicable to prevent unexpected second resolvers. Talos uses the tracked `../../talos-k8s/dns.patch.yaml` and per-node patches; CoreDNS forwards external queries through Talos node resolvers. The stopped, experimental `omarchy` VM (107) has no cloud-init DNS configuration and was not booted or modified; set its guest DNS before using it.

AdGuard sends ordinary DNS to local Unbound `127.0.0.1:5335`, has no fallback upstream, and uses local Unbound for its bootstrap resolver too. Caddy's Cloudflare ACME DNS-01 **propagation check only** retains `1.1.1.1` and `1.0.0.1` inside the Caddy `tls` block; Caddy's host and ordinary lookups use `10.1.1.2`. A temporary Cloudflare TXT record was created, resolved through both the public resolver and the internal stack, and removed. Do not use public DNS as an OS resolver on any guest.

Public resolver research (for devices *outside* the homelab, not an infrastructure fallback): from the DNS LXC on 2026-09-27, five sample cached A lookups took `4/4/9/4/4 ms` on Cloudflare `1.1.1.1`, `7/5/10/6/5 ms` on Cloudflare malware-filtering `1.1.1.2`, and `43/5/21/5/65 ms` on Quad9 `9.9.9.9`. This tiny point-in-time sample favors Cloudflare on this ISP, not a universal ranking. Cloudflare `1.1.1.2` is the practical speed-plus-malware-filtering choice; Quad9 `9.9.9.9` prioritizes privacy and threat blocking. Neither should replace our internal resolver for split-horizon names. See the providers' [Cloudflare setup](https://developers.cloudflare.com/1.1.1.1/setup/) and [Quad9 services](https://docs.quad9.net/services/) pages.

Validation:

```bash
ssh dns 'dig @127.0.0.1 portainer.l3b.cc.cd A +noall +answer'
ssh dns 'dig @127.0.0.1 k8s.l3b.cc.cd A +noall +answer'
ssh dns 'systemctl is-enabled AdGuardHome unbound; systemctl is-active AdGuardHome unbound'
```

Do not commit the active YAML, administrator hash, temporary reset files, or backups.

`px.l3b.cc.cd` is the load-balanced cluster entry point. Caddy uses the `pve_lb` cookie to keep a browser session on one healthy node, selects another node and replaces the cookie if that backend becomes unavailable, actively checks `/` every 10 seconds, and also performs passive failure handling. The node-specific names remain available for deterministic maintenance access.
