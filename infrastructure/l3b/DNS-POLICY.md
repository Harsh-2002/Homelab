# DNS and private/public routing — 2 November 2026

## Owner correction — public exact records only

This supersedes the historical public wildcard model described below.
**AdGuard may use an internal apex/wildcard; Cloudflare must not have a wildcard.**
Every deployed private HTTPS origin has an explicit DNS-only A record pointing
to the private Caddy address. Only an explicitly approved public service gets an
exact public-IP record and corresponding public Caddy route/path policy.

Applied: exact `auth`, `login`, `portainer`, `dns`, and `memory` mappings added;
apex and `oc` were already exact/correct. After verifying all seven mappings,
the Cloudflare apex wildcard CNAME was removed. All other existing records,
including `wg`, external monitoring, historical public apps and direct-host
exceptions, were preserved unchanged. Retired-app WAN records are flagged for
separate owner-approved cleanup, not treated as current deployment approval.

Both authoritative nameservers must return matching private answers for the
seven current origins and NXDOMAIN for an unknown public name; AdGuard must
still resolve an unknown internal name through its private wildcard. See
[`PUBLIC-DNS-VERIFICATION-2026-11-02.json`](PUBLIC-DNS-VERIFICATION-2026-11-02.json).
Recursive caches may retain old wildcard answers until TTL expiry.

This is about **DNS records**, not TLS certificates: Caddy's wildcard certificate
and hostname matcher remain valid, and its source/auth gates still apply.
For future private deployments add an explicit Cloudflare private A record as
well as the Caddy route; never infer a public exception from a new hostname.
`public-dns.py` is a manual, narrowly guarded maintenance operation, not a watch
or generic synchronization job. No service/firewall/publication rules changed.

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

All currently restored apps remain private. An explicit Caddy **route** block
now runs custom403 denial before host routing or forward-auth. Testing found
the previous implicit directive ordering could reach an upstream before denial;
this was corrected, not just restyled.

The repeatable test temporarily adds a reserved source address, connects directly
to Caddy's bridge-side TLS listener using real SNI/hostnames, spoofs LAN forwarded
headers, and verifies403/HTML/no-store for all six current origins. The temporary
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
