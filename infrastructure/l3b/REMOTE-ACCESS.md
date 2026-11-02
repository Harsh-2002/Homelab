# Native OpenCode remote access

**Completed and verified, 2 November 2026:** the detached handover succeeded.
The single native unit is active/enabled on the Docker bridge, the chosen
previous vault password is restored, history is preserved, and actual HTTPS
browser pairing/cookie authentication passed. Five Homepage cards are live.
Evidence: [native handover](NATIVE-HANDOVER-2026-11-02.json) and
[OpenCode verification](OPENCODE-VERIFICATION-2026-11-02.json). The earlier failure
record is resolved. The one-shot worker exited; no recurring job remains.

Owner action: use a fresh native pairing link for each browser/app. Re-import
the updated MacBook/iPhone VPN Documents to apply the new DNS on those devices.

The DNS/source-policy review is complete: see [DNS-POLICY.md](DNS-POLICY.md).
Cloudflare's exact `oc` record already matches the internal proxy address;
the native bind change, not another DNS/public exception, fixes the upstream502.

Owner-authorized origin: **https://oc.l3b.cc.cd**. This is the existing native
OpenCode server, not another Docker deployment. Session history, the Herdr
integration, provider authentication and skills remain on the host.

## Handover boundary

This conversation is hosted by the process that must be restarted. The final
takeover therefore runs once in a separate systemd user unit after the active
turn is delivered; it is not a recurring automation or proxy service.

The owner explicitly chose the **previous HomeLab → OpenCode vault password**.
Restoring it intentionally invalidates current browser/app login sessions;
it does not delete conversation history. No password/pairing token is placed
in a unit, argument, runbook, Git, memory document or command output.

The authoritative completion record is
[`NATIVE-HANDOVER-2026-11-02.json`](NATIVE-HANDOVER-2026-11-02.json), which is
created **only after** the actual service, HTTPS/browser, core, memory and
five-card dashboard checks pass. Until that file exists with `state: verified`,
activation is pending, not verified. The scheduled unit is
`opencode-handover.service`/`.timer`; it stops after this single maintenance run.

```bash
systemctl --user status opencode.service
systemctl --user status opencode-handover.service
python3 infrastructure/l3b/verify-opencode.py --browser
```

If the scoped handover fails, its activation script restores the pre-handover
native configuration and starts the same native service. Do not delete the
OpenCode database or auth stores, rotate identities, or start a second server
to work around a failed check. Subprocess output is deliberately withheld
because native pairing/authentication can return credentials.

## Direct private upstream

The `opencode.service` user unit runs `opencode serve --service`, with user
lingering already enabled. It retains the native protected `service.json` and
listens on **Docker bridge 10.1.3.1:4096**, not on the LAN/wildcard address.
The bridge gateway was checked against the actual external `l3b` network.
Native CLI discovery uses that saved address; a loopback-only service cannot
be reached directly by a bridge-network Caddy container.

The first handover rolled back because the already-running systemd user manager
retained groups from before `dev` joined Docker. The browser container stayed
healthy, but Docker exec failed with socket permission denied. Do not fix this
with world-writable socket permissions or by terminating all user services.
The native unit and detached worker now use the standard `sg docker -c` group
selection; the two browser MCP commands do the same, so they can reconnect
without restarting the active server. This selects an existing authorized
membership, adds no proxy/helper service and changes no socket permissions.
The retry checks Docker/CDP access before stopping the server and verifies the
native service's effective Docker group afterward. The original failure record
is retained and marked resolved only after a fully verified handover.

The existing `HERDR_ENV`, `HERDR_SOCKET_PATH` and `HERDR_PANE_ID` values are
preserved privately in the optional `~/.config/opencode/herdr.env` unit input,
because a user service does not automatically inherit the active terminal's
environment. No Herdr config, socket or pane is recreated. These are the
existing pane's attachment metadata, not a new agent or recurring schedule.

Caddy and Homepage map the native host alias `opencode` to that gateway. Caddy
proxies directly to `opencode:4096`, forwarding native streams/WebSockets and
adding Secure to native OpenCode cookies behind TLS. No host proxy, socket
proxy, public tunnel, port-forward or extra container is introduced. Docker
publications remain only 53/UDP and 443/TCP+UDP. Direct LAN TCP4096 must fail.
The private source gate is LAN/WireGuard/Docker, never the retired Tailscale.

OpenCode uses its own native authentication, not Tinyauth. HTTPS UI shell200
does not prove authentication: anonymous `/api/info` must return401, and an
authenticated API request must return200. The browser check obtains a fresh
single-use pairing code privately, opens it as a real browser and verifies
cookie-authenticated API access plus Secure/HttpOnly flags and rendered UI.
The test consumes its own code and does not export it.

## Browser and app connection

Use the established URL and HomeLab vault login. For native browser/app pairing,
generate a **fresh** link on the host:

```bash
opencode pair --url https://oc.l3b.cc.cd
```

Open it in the browser, or scan/paste it into the OpenCode app. Pairing links
are single-use and expire after five minutes; do not save or share them in Git,
Notion, chat, memory or Homepage. Owner devices require their own fresh pairing.
The card contains only the origin URL, never a pairing link or credential.

Sources: [V2 web](https://opencode.ai/v2/docs/cli/web),
[V2 plugins](https://opencode.ai/v2/docs/build/plugins), and the preserved
historical deployment in `infrastructure/agents/README.md`.
