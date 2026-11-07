# OpenTunnel

Public HTTPS URLs for a local development server, without opening a port or
adding a Caddy site. Installed 8 November 2026 for agent-driven development
previews and webhook testing.

## What it is

`anomalyco/opentunnel` (MIT) is a blind TLS tunnel. The CLI keeps the certificate
private key and terminates TLS locally; the relay routes by SNI and never sees
HTTP plaintext. Each route is published at
`https://<route>.<tunnel-id>.opentunnel.xyz`.

A tunnel URL is **unguessable, not private**. There is no authentication, and the
tunnelled app sees every visitor as a loopback peer. It is temporary development
access, never a replacement for a Caddy site.

## Install, upgrade, remove

```bash
npm install -g opentunnel      # npm prefix is ~/.local, no sudo
opentunnel --version           # 0.6.2 verified 2026-11-08
npm uninstall -g opentunnel    # removal; also delete ~/.config/opentunnel
```

The CLI is `~/.local/bin/opentunnel`; keep that directory on `PATH`.

## Configuration

There is no daemon config file to edit. The knobs are:

| Setting | How |
| --- | --- |
| Profile (one tunnel per profile) | `--profile <name>` or `OPENTUNNEL_PROFILE` |
| Extra CA for a TLS-inspecting proxy | `--ca-cert <pem>` or `OPENTUNNEL_CA_CERT` |
| Self-hosted server | `OPENTUNNEL_API=https://…` |
| Autostart | `opentunnel up` enables it, `opentunnel down` removes it |

Default state: **autostart disabled, no routes**. `route add` installs and enables
`opentunnel-<profile>.service`; `down` stops and removes it. The tunnel identity
(private key) lives under `~/.local/state/opentunnel/<profile>/` and is reused, so
later routes skip certificate issuance.

## Skill

The agent skill is canonical at `~/.agents/skills/opentunnel` (OpenCode reads that
root directly), symlinked into `~/.hermes/skills` and `~/.claude/skills`, and
installed in OpenViking as `viking://agent/skills/opentunnel`.

```text
opentunnel/
  SKILL.md                     when to use, autonomy rules, lifecycle, exposure rules
  references/cli.md            commands, flags, output formats, state paths
  references/trust-boundary.md TLS model, loopback peer, cookies/CORS/OAuth
  scripts/opentunnel.py        preview / list / doctor / cleanup / destroy
```

The helper is the supported interface; it adds what the CLI cannot know.

```bash
S=~/.agents/skills/opentunnel/scripts/opentunnel.py

$S preview 18080 --purpose "checkout page" --ttl 60   # create, verify, register
$S list                                               # live routes, target state, TTL
$S doctor                                             # probe URLs, dead targets, cert expiry
$S cleanup --dry-run                                  # what would be removed
$S destroy <route> | --all                            # remove; down when empty
```

`preview` refuses a port with nothing listening, retries up to 45 s while a new
certificate becomes usable, and records purpose, project, TTL and creation time.
Routes created outside the helper still appear in `list`/`doctor` as `STALE`.

## Registry

The CLI is the source of truth (`opentunnel route list`, `opentunnel status`).
The helper keeps annotations only, at
`~/.local/state/opentunnel-skill/registry.json` (0600), keyed `profile|route`. It
is disposable: deleting it loses purpose/TTL history, not routes.

## Policy

- Tunnel **only** a loopback dev server on a high port. Bind `127.0.0.1`.
- Never tunnel Caddy, Portainer, Home Assistant, Immich, n8n, Orva, databases,
  SMB, SSH, OpenCode, 1Password or `10.1.3.1:8099`. A tunnel bypasses Caddy,
  AdGuard and Pocket ID.
- No secrets in URL paths or query strings; test-mode credentials only; assume the
  URL is public.
- Public origins remain exactly `notes`, `pin`, `photos` and `drive` through Caddy.
- Destroy at the end of the task: `destroy` or `cleanup`, then confirm
  `opentunnel status` shows no routes and a stopped service.

## Verified example, 8 November 2026

```text
$ $S preview 18082 --purpose "demo for Anurag" --ttl 15
verified: HTTP 200
https://1c5744d3734899f3.wk6fjfrkhwfr.opentunnel.xyz

$ curl -sS https://1c5744d3734899f3.wk6fjfrkhwfr.opentunnel.xyz/
<h1>Hello from the homelab dev server</h1> …

$ $S doctor
ok     1c5744d3734899f3   HTTP 200 https://1c5744d3734899f3.wk6fjfrkhwfr.opentunnel.xyz

$ $S destroy --all
removed 1 route(s); service stopped and autostart disabled
```

Afterwards `opentunnel status` reported no routes and a stopped service, and
`systemctl --user is-enabled opentunnel-default.service` returned `not-found`.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `refusing: nothing is listening` | App not started, or bound to another interface |
| `NOT reachable` after 45 s | App error, wrong port; test `curl 127.0.0.1:<port>` |
| `no route named …` | `route remove` takes the route name, not the target |
| First run stalls at certificate verification | Normal ACME DNS-01 issuance |
| Service still enabled later | `destroy --all`, then check `systemctl --user is-enabled` |
| Certificate expired | `opentunnel status` shows expiry; renewal is automatic while connected |

## Rollback

```bash
opentunnel route remove <route>     # or: $S destroy --all
opentunnel down                     # stop + disable autostart
opentunnel delete                   # destroy the tunnel identity (hostname lost)
npm uninstall -g opentunnel
rm -rf ~/.config/opentunnel ~/.local/state/opentunnel ~/.local/state/opentunnel-skill
rm -rf ~/.agents/skills/opentunnel ~/.hermes/skills/opentunnel ~/.claude/skills/opentunnel
```

Removing the skill from OpenViking: `ov skills remove opentunnel` (or
`DELETE /api/v1/skills/opentunnel`).
