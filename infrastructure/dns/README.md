# DNS

The authoritative policy is [`../l3b/DNS-POLICY.md`](../l3b/DNS-POLICY.md). This runbook records the current implementation.

## Current layout

- AdGuard Home runs on the `l3b` Docker host and publishes TCP/UDP 53. LAN, WireGuard and Docker clients use **10.1.1.10**.
- AdGuard forwards ordinary queries to the local Unbound recursive resolver. There is no public fallback.
- AdGuard answers internal names through its private wildcard, currently to **10.1.1.10** (Caddy).
- Cloudflare is **DNS-only** and has **no wildcard**. Every deployed hostname has an exact record.
- Caddy is the access-control layer: private hostnames are denied unless the source is LAN, WireGuard, Docker or loopback.

## The rule

| Service type | Public DNS (Cloudflare) | Private DNS (AdGuard) | Caddy |
|---|---|---|---|
| **Private** | Exact DNS-only `A` → **10.1.1.10** | **10.1.1.10** | Private source gate; no public handler |
| **Public** | Exact DNS-only `A` → **150.129.31.154** | **10.1.1.10** | Approved public handler + native auth |
| **Private direct host** | Exact DNS-only `A` → host private IP | Same private IP | Not HTTP |
| **Unknown** | NXDOMAIN | Internal wildcard may resolve | No route |

A device using **public DNS while inside the LAN** must still resolve a private service to `10.1.1.10`. That is why private services have exact public records pointing to the private Caddy address. The record does not make the service internet-reachable; outside the LAN the private IP has no route, and Caddy would deny the source anyway.

Do not use public DNS as an OS resolver on infrastructure guests. Exact records are for client compatibility, not an infrastructure fallback.

## Private HTTPS origins

These require an exact public `A` to `10.1.1.10`:

`l3b.cc.cd`, `auth`, `login`, `portainer`, `dns`, `memory`, `beszel`, `cairn`, `docs`, `downloads`, `frigate`, `git`, `home`, `media`, `motrix`, `n8n`, `orva`, `os`, `registry`, `rustfs`, `s3`, `switch`, `theking`.

## Approved public origins

These use an exact public `A` to `150.129.31.154`, with a matching public Caddy handler and native application authentication:

`notes`, `pin`, `photos`, `drive`, `cairn-s3`, `mdx`, `oc`.

`orva` is private and keeps the private gate. Do not add a public-IP record or public Caddy handler for a private service without explicit owner approval.

## Direct-host and non-HTTP records

| Name | Answer |
|---|---|
| `smb.l3b.cc.cd` | `10.1.1.12` |
| `k8s.l3b.cc.cd` | `10.1.1.200` |
| `k8s-201.l3b.cc.cd` | `10.1.1.201` |
| `k8s-202.l3b.cc.cd` | `10.1.1.202` |
| `k8s-203.l3b.cc.cd` | `10.1.1.203` |
| `wg.l3b.cc.cd` | `150.129.31.154` |
| `ntfy.l3b.cc.cd`, `watch.l3b.cc.cd` | `8.235.70.28` |

AdGuard carries **self-CNAME exception rewrites** for these direct hosts (`smb`, `k8s*`, `ntfy`, `watch`) so the internal wildcard does not override Unbound's exact local-data. Keep those exceptions in sync with `adguard-rewrites.yaml`; removing them makes the wildcard return `10.1.1.10` instead of the direct-host address.

## Add a private hostname

1. Add the Caddy route with the private source gate.
2. Add an exact Cloudflare **DNS-only A** record → `10.1.1.10`, TTL 300.
3. Verify internal resolution and a public resolver from inside the LAN.
4. Do not add a public handler or weaken the source gate without owner approval.

## Stale records

These are not current Caddy hosts and need separate owner approval before removal:

- `argocd`, `dev`, `store` — historical public WAN records.
- `omni`, `omni-api`, `omni-kube` — old `10.1.1.3` proxy records.

The live record inventory is [`cloudflare-records.tsv`](cloudflare-records.tsv).

## Verification

```sh
dig @1.1.1.1 motrix.l3b.cc.cd A +short          # 10.1.1.10
dig @10.1.1.10 motrix.l3b.cc.cd A +short       # 10.1.1.10
dig @1.1.1.1 unknown-name.l3b.cc.cd A +short   # empty / NXDOMAIN
sudo python3 infrastructure/l3b/public-dns.py  # read-only audit
sudo python3 infrastructure/l3b/verify-dns-policy.py
```

Recursive caches may retain an old NXDOMAIN or wildcard answer until TTL expiry. Query the authoritative Cloudflare nameserver or a fresh resolver when changing records.

## Historical note

The former DNS LXC at `10.1.1.2` and the public apex/wildcard model are superseded. Internal wildcard resolution remains on AdGuard, but Cloudflare no longer has a wildcard and every current hostname has an exact record.
