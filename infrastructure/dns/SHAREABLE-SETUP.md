# AdGuard Home + Unbound: my DNS setup

This is a sanitized description of a small home-lab DNS stack, checked against the running services on 2026-09-24. Replace every `<PLACEHOLDER>` with your own addresses and domain. It is a description of what I run, not a drop-in copy of my protected configuration.

## Architecture

```text
LAN / Kubernetes / Tailscale clients
        │ DNS, TCP/UDP 53
        ▼
AdGuard Home (systemd service, dedicated Debian LXC)
  ├─ local rewrites and HaGeZi blocklists
  ├─ 128 MiB DNS cache
  └─ upstream 127.0.0.1:5335
        ▼
Unbound (systemd service, recursive resolver + DNSSEC validator)
        ▼
DNS root, TLD and authoritative servers
```

The DNS container has 2 vCPU and 2 GiB RAM. AdGuard Home `v0.107.79` and Unbound `v1.26.1` are installed as native systemd services, both enabled and running. AdGuard listens on its LAN address and loopback for plain DNS; its management UI listens on a separate LAN port behind a private reverse proxy. Unbound is reached only over loopback. There is no Docker or public DNS listener.

Clients use the AdGuard LAN IP. The router and infrastructure point to it as primary DNS; a public resolver may be configured as a *client-side* fallback, but that can bypass local names and filtering when selected. AdGuard itself has **no fallback upstream**: recursive queries go to Unbound. The public bootstrap resolvers in the AdGuard settings are for resolving hostname-based encrypted upstreams if needed; they are not the normal recursive path.

## AdGuard Home settings

These are the relevant, sanitized fields from `/opt/AdGuardHome/AdGuardHome.yaml`:

```yaml
http:
  address: <DNS_LAN_IP>:3000
dns:
  bind_hosts:
    - 127.0.0.1
    - <DNS_LAN_IP>
  port: 53
  upstream_dns:
    - 127.0.0.1:5335
  fallback_dns: []
  allowed_clients:
    - 127.0.0.0/8
    - <LAN_CIDR>
    - <K8S_POD_CIDR>
    - <TAILSCALE_CIDR>
  ratelimit: 100
  refuse_any: true
  cache_enabled: true
  cache_size: 134217728 # 128 MiB, in bytes
  cache_ttl_min: 0
  cache_ttl_max: 0
  cache_optimistic: true
  cache_optimistic_answer_ttl: 30s
  cache_optimistic_max_age: 12h
  enable_dnssec: true
  edns_client_subnet:
    enabled: false
querylog:
  enabled: true
  interval: 7d
statistics:
  enabled: true
  interval: 90d
tls:
  enabled: false
```

The zero TTL overrides mean authoritative TTLs are respected; the cache does not forcibly extend every record. Optimistic caching can answer from an expired AdGuard entry while refreshing it, for up to the configured maximum age. This favors availability and latency, but a recently changed DNS record can briefly appear stale. DNSSEC validation is also performed by Unbound. DNS-over-TLS/HTTPS is not exposed directly by AdGuard; the admin UI is protected separately by the reverse proxy. I do not publish the active YAML because it also contains an administrator password hash and operational state.

### Blocklists

Only two general-purpose lists are enabled, to avoid stacking heavily overlapping lists:

| Purpose | List | URL |
| --- | --- | --- |
| General ads, trackers and nuisance domains | HaGeZi Multi PRO | `https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/pro.txt` |
| Threat intelligence / malicious domains | HaGeZi TIF Medium | `https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/tif.medium.txt` |

I use the default blocking mode, with no custom allowlist or user rules in the shared baseline. DNS blocking is not a substitute for endpoint/browser security, and the aggressive HaGeZi Pro++ or Ultimate tiers are not automatically “better” for a mixed-device household: false positives and support effort matter more than available RAM.

### Local DNS and split horizon

An apex A rewrite points `<INTERNAL_DOMAIN>` to `<PROXY_LAN_IP>`, and a wildcard CNAME rewrite points `*.<INTERNAL_DOMAIN>` back to that apex. New reverse-proxy services therefore need a proxy route but usually no new local DNS record. A few direct-host names use AdGuard CNAME exceptions and exact A records in Unbound instead. Public DNS is private-by-default; only explicitly published names receive public A records. Keep direct-host, SMB and management names private.

## Unbound settings and an important caveat

The running Unbound process answers recursive queries on `127.0.0.1:5335`, and its Debian systemd unit is enabled. Its trust anchor is managed at `/var/lib/unbound/root.key`. The retained local-zone file is conceptually:

```unbound
server:
    local-zone: "<INTERNAL_DOMAIN>." transparent
    local-data: "<DIRECT_HOST>.<INTERNAL_DOMAIN>. 30 IN A <DIRECT_HOST_LAN_IP>"
```

However, **the current on-disk Unbound files do not declare `interface: 127.0.0.1`, `port: 5335`, or larger cache sizes**. Runtime socket inspection shows port 5335, while querying the current config reports the Unbound defaults (port 53; 4 MiB message and 4 MiB RRset caches). This is configuration drift, not a reproducible tuned resolver. Do **not** copy the local-zone fragment alone or assume a future full restart will recreate the working listener. The persistent listener/cache configuration must be reconciled and restart-tested before treating this as a complete installation recipe. No such live change was made while preparing this shareable note.

For a new installation, explicitly set the loopback listener and port, then size Unbound's caches deliberately for the machine. The official Unbound manual explains `msg-cache-size`, `rrset-cache-size`, `prefetch`, `serve-expired`, DNSSEC and qname minimisation. Avoid claiming “max cache” without measuring hit rate and memory; the 128 MiB AdGuard cache is currently the main intentionally sized cache in this stack.

## Operational checks

```sh
systemctl is-enabled AdGuardHome unbound
systemctl is-active AdGuardHome unbound
ss -lntup | grep -E ':(53|5335)\b'
dig @<DNS_LAN_IP> example.org A
dig @127.0.0.1 -p 5335 example.org A
unbound-control stats_noreset | grep -E 'total.num.(queries|cachehits|cachemiss)='
```

Keep the management UI off the open Internet, limit DNS clients to intended networks, and monitor resolution after reboots—not just while the services happen to be running.

Official references: [AdGuard Home configuration](https://github.com/AdguardTeam/AdGuardHome/wiki/Configuration), [Unbound configuration manual](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html).
