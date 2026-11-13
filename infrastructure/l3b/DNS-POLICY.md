# DNS and private/public routing — updated 13 November 2026

## Current rule — exact records, no public wildcard

This is the authoritative DNS policy. It supersedes the historical public-wildcard model below.

**Cloudflare has no wildcard record.** AdGuard may use an internal apex/wildcard. Cloudflare is DNS-only, never proxied.

### Private service

| Layer | Answer |
|---|---|
| Public DNS (Cloudflare) | Exact DNS-only `A` → **10.1.1.10** (private Caddy) |
| Private DNS (AdGuard) | Wildcard/exact → **10.1.1.10** |
| Caddy | Private source gate; no public handler |
| Outside LAN/VPN | Public DNS returns the private IP; the address is not routable by design |

A device using public DNS **inside the LAN** must still resolve a private service to `10.1.1.10`. This is why every private HTTPS origin needs an exact public record pointing at the private Caddy address. DNS is not access control; Caddy's LAN/VPN source gate is.

Private HTTPS origins currently include:

`l3b.cc.cd`, `auth`, `login`, `portainer`, `dns`, `memory`, `beszel`, `cairn`, `docs`, `downloads`, `frigate`, `git`, `home`, `media`, `motrix`, `n8n`, `orva`, `os`, `registry`, `rustfs`, `s3`, `switch`.

### Public service

| Layer | Answer |
|---|---|
| Public DNS (Cloudflare) | Exact DNS-only `A` → **150.129.31.154** |
| Private DNS (AdGuard) | **10.1.1.10** (split-horizon) |
| Caddy | Approved public handler and native application authentication |

Approved public origins are `notes`, `pin`, `photos`, `drive`, `cairn-s3`, `mdx`, `oc`, and `theking`.

`theking` is the separate friend-owned Nivra instance. It is public by owner request; Nivra's native authentication protects it. The instance is first-visitor claimable until the friend completes onboarding, so public exposure carries that risk.

`orva` is private and keeps the private Caddy gate; its public record points to the private address. Do not add a public handler or public-IP record for a private service without explicit owner approval.

### Direct-host and non-HTTP services

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

### Unknown names

Public DNS returns NXDOMAIN. AdGuard's internal wildcard may resolve an internal name, but no Caddy route means no service.

## Add a private hostname

1. Add the Caddy route with the private source gate.
2. Add an exact Cloudflare **DNS-only A** record for the hostname → `10.1.1.10`, TTL 300.
3. The internal AdGuard wildcard already covers the name; verify it.
4. Test with a public resolver from inside the LAN; it must return `10.1.1.10`.
5. Do not add a public handler or change Caddy's source gate without owner approval.

## Stale records pending owner cleanup

These do not have a current Caddy hostname and should not be treated as deployed services:

- `argocd.l3b.cc.cd`, `dev.l3b.cc.cd`, `store.l3b.cc.cd` — historical public WAN records.
- `omni.l3b.cc.cd`, `omni-api.l3b.cc.cd`, `omni-kube.l3b.cc.cd` — old `10.1.1.3` proxy records.

Do not delete them in a routine DNS change; require explicit owner approval.

## Verification

```sh
dig @1.1.1.1 motrix.l3b.cc.cd A +short          # 10.1.1.10
dig @10.1.1.10 motrix.l3b.cc.cd A +short       # 10.1.1.10
dig @1.1.1.1 unknown-name.l3b.cc.cd A +short   # empty / NXDOMAIN
sudo python3 infrastructure/l3b/public-dns.py  # read-only audit
sudo python3 infrastructure/l3b/verify-dns-policy.py
```

Recursive caches may retain an old NXDOMAIN or wildcard answer until TTL expiry. The authoritative Cloudflare nameservers and a fresh query are the source of truth.

Evidence: [public DNS verification](PUBLIC-DNS-VERIFICATION-2026-11-13.json) and [policy/Caddy verification](DNS-POLICY-VERIFICATION-2026-11-13.json).

## Historical policy, confirmed against the actual backup

Reviewed the DNS/proxy runbooks, indexed memory, and original/final-cutover proxy
Caddyfiles on the external backup disk, read-only. No backup body, credential,
retired service or tailnet configuration was restored wholesale.

- Internal AdGuard apex A plus wildcard CNAME sends proxy-managed names to Caddy.
- Cloudflare DNS-only private apex/wildcard is the default. Deliberately public
  services need exact WAN records **and** matching public Caddy routes. DNS is
  not access control.
- The backup classifies Immich/Jellyfin/Karakeep as historical public apps;
  Portainer/OpenCode as private with native auth; AdGuard/Homepage/router as
  private plus Tinyauth. Argo CD exposed only its signed webhook path. These are
  examples of the former policy, not applications to redeploy now.
- Source checks use the immediate peer, not untrusted forwarded-IP headers.
  WireGuard replaces Tailscale; native application authentication remains.
- The black/white custom403 HTML was inline in Caddy, with no-store caching.

## Effective DNS

The owner chose **native systemd-networkd**, not ifupdown or a Netplan frontend.
The single source for eno1's static IP, gateway and **DNS=10.1.1.10** is
`/etc/systemd/network/10-eno1.network`, tracked as
[`10-eno1.network`](10-eno1.network). Only eno1 matches; Docker bridges/veths and
wg0 remain unmanaged by networkd and owned by Docker/WireGuard.

The complementary `systemd-resolved` service receives per-link DNS from networkd
and generates `/run/systemd/resolve/resolv.conf`; `/etc/resolv.conf` is a symlink
to that generated uplink file, not a hand-maintained file. The tracked
[`resolved.conf`](resolved.conf) disables public fallback, stub DNS listeners,
LLMNR and mDNS. Applications still query AdGuard directly. DNSSEC validation stays
in Unbound. There is one network manager, not two: resolved is its DNS companion.

The previous ifupdown/resolvconf integration was superseded and both packages
purged; Netplan is not installed. The protected live migration adopted the
existing address/routes without ifdown or an interface bounce. A detached
rollback timer was armed, then cancelled after DNS/HTTPS/Docker/WireGuard checks.
The existing system bus was reloaded (not restarted) to load the newly installed
resolved policy, and resolved was restarted; its D-Bus API and generated file
were both verified. No recurring migration task remains, and no reboot is claimed.
The Docker daemon separately and explicitly merges
[`docker-dns.fragment.json`](docker-dns.fragment.json) without replacing its
other options. Docker was restarted with its existing live-restore setting
retained. Browser MCP exec connections were reconnected; the shared browser
was restarted to verify fresh sandbox defaults.

All ten containers use Docker's embedded **127.0.0.11**, preserving service-name
resolution, with internal AdGuard as its recorded upstream. Existing sandboxes
already inherited the same host resolver; new sandboxes use the explicit default.
AdGuard forwards to **unbound:5335**, has no public fallback, and permits only
loopback/current LAN, WireGuard and Docker subnets. The stale Tailscale allowlist
entry was removed. Unbound performs recursive DNSSEC validation.

No public secondary: resolver arrays are not a universal ordered-failover
contract. Public replies can bypass split-DNS/filtering; NXDOMAIN is an answer,
not an outage. The historical runbook documents an SMB failure from this exact
bypass. Real redundancy needs another internal resolver with matching records.
This remains one DNS instance, not HA. Caddy's public resolvers are retained
only inside ACME DNS-01 propagation checking, matching the old design; they are
not host/container application resolvers. No port80 or DNS TCP was published.

## WireGuard and device acceptance

The installed manager's initialization default, saved settings, generated peer
profiles and tracked example now use **DNS = 10.1.1.10**. The native manager
synchronized this without restarting the interface. Existing **MacBook** and
**iPhone** vault Documents were updated in place and read back; comparison
confirmed only the DNS line changed. Keys, endpoints and routes were preserved.

**Re-import the updated Document on each device.** WireGuard cannot push new
DNS into an already imported tunnel. LAN/VPN routes are unchanged; clients need
no direct Docker-subnet route for private HTTPS. Device-side DNS acceptance and
full tunneling are not claimed.

## Cloudflare, source gate and403

The initial read-only Cloudflare audit found the old private apex/wildcard model
and an already-correct exact `oc` record. The latest owner correction above
removed that public wildcard after creating missing exact private mappings.
Existing public WAN exceptions/external monitoring records were not
retargeted, deleted or activated. Stale retired-app/direct-host records need
separately scoped cleanup; they are not evidence of deployed applications.

The four owner-approved apps are public; Orva and all core services remain
private. An explicit Caddy **route** block runs approved public app handlers
first, then custom403 denial for every other host before forward-auth. Testing found
the previous implicit directive ordering could reach an upstream before denial;
this was corrected, not just restyled.

The repeatable test temporarily adds a reserved source address, connects directly
to Caddy's bridge-side TLS listener using real SNI/hostnames, spoofs LAN forwarded
headers, and verifies403/HTML/no-store for the private origins and verifies the approved public origins are reachable. The temporary
address is always removed. A host-local published-port request can have its
source rewritten and is not equivalent. This is synthetic source testing, not
an independent WAN/VPN-device connection or router-firewall audit.

```bash
sudo python3 infrastructure/l3b/verify-dns-policy.py
sudo wg.sh verify
sg docker -c 'python3 infrastructure/l3b/verify-core.py'
```

Evidence: [DNS policy verification](DNS-POLICY-VERIFICATION-2026-11-02.json).
Native OpenCode activation has separate service/browser handover evidence;
DNS policy completion does not imply that activation succeeded.
