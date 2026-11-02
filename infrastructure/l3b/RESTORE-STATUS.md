# Core restoration checkpoint — 2 November 2026

## Final follow-up completion

DNS policy and native OpenCode handover are complete and verified. The native
unit is active/enabled, previous vault password restored, session history
preserved, HTTPS browser pairing/cookie/API tests pass, and all five Homepage
cards pass desktop/mobile checks. Initial handover failure is resolved. The
one-shot exited; no recurring schedule remains. See
[completion evidence](NATIVE-HANDOVER-2026-11-02.json) and [DNS policy](DNS-POLICY.md).
Owner devices still need fresh OpenCode pairing and VPN profile re-import;
independent device/WAN, human passkey/OAuth, reboot and backup drills remain
distinct acceptance limits, not unfinished server configuration.

Authoritative detail: [core runbook](README.md),
[read-only acceptance record](CORE-VERIFICATION-2026-11-02.json), and the separate
[WireGuard/setup handoff](HANDOFF-2026-11-02.md).

## Current verified state

Owner network correction applied: `l3b` now uses the dedicated Docker /24 and
gateway from the [current network plan](README.md#network-plan--owner-correction-2-november-2026).
Ten existing containers and their aliases are retained; LAN/WireGuard routes
are unchanged. DNS/proxy ACLs, native-host aliases and stopped Hermes trust were
updated. Core and memory checks pass. Native remote activation and the wider
DNS/public-private policy is now applied and verified in [DNS-POLICY.md](DNS-POLICY.md).
Native remote activation remains tracked by its separate handover evidence.

- One restored Portainer BE2.45.3, internal-only behind Caddy. Original users and
  30 legacy stack definitions are preserved; actual browser admin login passed.
  The erroneous failed self-stack entry was removed through the native API.
- Portainer-managed `dns`169: current stable AdGuard0.107.79 plus public
  `klutchell/unbound`1.26.2. Only host **53/UDP**; UI stays internal. Private DNS,
  valid/invalid DNSSEC, cache answers and Unbound health passed.
- `proxy`171: original custom Caddy binary/plugins/certificates in the
  official image; only **443/TCP+UDP**. No HTTP80 or management publications.
- `identity`170: Pocket ID and Tinyauth with original data/encryption key.
  HTTPS discovery/JWKS and DNS UI forward-auth/spoof rejection passed. Human
  passkey and complete OAuth sign-in still require owner acceptance.
- Homepage stack `dashboard`172 is healthy at the private apex, behind the saved Tinyauth
  policy. Current cards and DNS metrics passed desktop/mobile browser tests.
  No new host ports or Docker socket. Tailscale is retired and absent on l3b;
  WireGuard remains the current VPN.
- OpenCode is **host-native only**. Session history/Herdr retained;
  39 skills and eight configured MCPs (six connected; Olx/Supabase disabled).
  Browser automation is Playwright CLI with its official skill; the former
  `tools` browser stack and Playwright/Chrome DevTools MCPs are removed.
- Nivra, Orva, Karakeep, Immich and OpenCloud are restored as Portainer stacks
  with original application data. Nivra/Karakeep/Immich/OpenCloud are
  owner-approved public origins with native app authentication; Orva remains
  behind the private Caddy source gate. Core services remain private.
- Docker publications are exactly **53/UDP,443/TCP,443/UDP**. Native SSH,
  OpenCode's approved native handover is tracked separately; WireGuard is unchanged.
- The temporary duplicate OpenCode server, custom Unbound build and unwanted
  host proxy were removed. No substitute proxy/helper service was added.

## Scope boundary

Hermes configuration is staged; stack166 is **stopped**, pending core acceptance.
No messaging gateway, cron job, old session DB or unrelated application stack
is running from this restoration. Codex/Claude config was not restored.
The owner subsequently authorized OpenViking: stack `memory`174 is restored and
healthy, with local embeddings, saved VLM access, semantic retrieval and native
OpenCode's official plugin/MCP/three bundled skills verified. Automatic capture
was explicitly chosen with redaction filters; see [memory](MEMORY.md).

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
Notion runbook received an append-only nine-block verified update. OpenViking's
current-state entry and index were refreshed and semantically retrieved. This
is not a blanket sync of every old repository/Notion snapshot.

## Native remote handover

The first attempt rolled back. Its user-manager credentials lacked the existing
Docker group, breaking both browser MCP launches. Those MCPs are now repaired
and actual calls pass; socket permissions and published ports are unchanged.
The native unit and detached retry select the authorized group with `sg`, and
the retry now preflights Docker/CDP before stopping the active server. See
`BROWSER-VERIFICATION-2026-11-02.json`; the old failure record is retained.

The owner also requested native OpenCode HTTPS web/app access and chose the
previous vault credentials, accepting logout of old logins while retaining all
session history. The [one-shot handover](REMOTE-ACCESS.md) runs outside the
active server. It creates `NATIVE-HANDOVER-2026-11-02.json` only after actual
native/browser and five-card dashboard tests pass, then publishes the evidence
and refreshes Notion/OpenViking. Until its `state` is verified, this step remains
pending; no duplicate OpenCode or custom host proxy is a permitted fallback.
