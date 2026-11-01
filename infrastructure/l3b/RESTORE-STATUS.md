# Core restoration checkpoint — 2 November 2026

Authoritative detail: [core runbook](README.md),
[read-only acceptance record](CORE-VERIFICATION-2026-11-02.json), and the separate
[WireGuard/setup handoff](HANDOFF-2026-11-02.md).

## Current verified state

- One restored Portainer BE2.45.3, internal-only behind Caddy. Original users and
  30 legacy stack definitions are preserved; actual browser admin login passed.
  The erroneous failed self-stack entry was removed through the native API.
- Portainer-managed `core-dns`163: current stable AdGuard0.107.79 plus public
  `klutchell/unbound`1.26.2. Only host **53/UDP**; UI stays internal. Private DNS,
  valid/invalid DNSSEC, cache answers and Unbound health passed.
- `core-proxy`165: original custom Caddy binary/plugins/certificates in the
  official image; only **443/TCP+UDP**. No HTTP80 or management publications.
- `core-identity`164: Pocket ID and Tinyauth with original data/encryption key.
  HTTPS discovery/JWKS and DNS UI forward-auth/spoof rejection passed. Human
  passkey and complete OAuth sign-in still require owner acceptance.
- Homepage stack168 is healthy at the private apex, behind the saved Tinyauth
  policy. Current cards and DNS metrics passed desktop/mobile browser tests.
  No new host ports or Docker socket. Tailscale is retired and absent on l3b;
  WireGuard remains the current VPN.
- OpenCode is **host-native only**. Current auth/sessions/Herdr retained;
  33 skills and five MCPs available. Playwright/Chrome DevTools share one Docker
  browser through the `agent-tools`162 stack; no MCP/CDP host ports.
- Docker publications are exactly **53/UDP,443/TCP,443/UDP**. Native SSH,
  loopback OpenCode and the separately approved WireGuard service are unchanged.
- The temporary duplicate OpenCode server, custom Unbound build and unwanted
  host proxy were removed. No substitute proxy/helper service was added.

## Scope boundary

Hermes configuration is staged; stack166 is **stopped**, pending core acceptance.
No messaging gateway, cron job, old session DB or unrelated application stack
is running from this restoration. Codex/Claude config was not restored.
OpenViking is unavailable; its synchronization is still pending.

The active HomeLab service account and `cf` OAuth were verified without printing
credentials. Both keys from the owner's SSH ID were already authorized for dev;
no duplicates or root-key changes were made. The SSH ID itself is recorded only
in private instructions/runbook context, not public key contents.

## Preservation and limits

The external backup remains mounted temporarily, unchanged. Docker-managed
state remains on NVMe and application bind data on UUID-mounted SATA `/data`.
The parallel WireGuard commits througha200ba5 and their working keys/profiles,
router configuration and firewall backend were preserved. Its iPhone acceptance
is not pending; MacBook/cold-boot tests remain separate.

UDP-only client DNS deliberately has no TCP fallback. No current-node backup,
independent HTTP3 transport test, reboot, Docker-daemon restart or paid model
acceptance is claimed. See the runbook for the restored historical Portainer
backup warning and remaining identity/client gates.

Public/internal native diagrams passed the architecture checks and official CLI
rendering; current PNG/PDF overviews were refreshed and visually inspected.
Core, agent-scope and Homepage browser acceptance checks passed. The existing
Notion runbook received an append-only nine-block verified update. OpenViking
remains unavailable; do not infer its synchronization from Git/Notion updates.
