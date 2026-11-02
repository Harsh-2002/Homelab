# DNS and private/public routing — 2 November 2026

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

The static host `/etc/resolv.conf` uses only **10.1.1.10**. Host IPv4 configuration
is static, not DHCP DNS. The Docker daemon now explicitly merges
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

Read-only live Cloudflare audit confirmed apex and exact `oc` already target
**10.1.1.10**, wildcard CNAME targets apex, and all are DNS-only. No DNS mutation
was needed. Existing public WAN exceptions/external monitoring records were not
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
