# Shared coding-agent tools on dev

Excalidraw CLI added 2026-10-25: official user-global CLI plus shared local
skill for all four agents. Local scene rendering is account-free; no cloud
uploads or MCP added. See [EXCALIDRAW.md](EXCALIDRAW.md). The Homelab's current
diagram direction is an internal connected tree/flow board with IP labels.

Living architecture standard, 2026-10-25: all four global instruction files
point to the root Homelab AGENTS.md. Material infrastructure changes update
the [architecture inventory and diagrams](../../docs/architecture/README.md),
rebuild/validate, refresh Notion/OpenViking and commit/push scoped work. Private
address annotations and internal diagram exports remain outside public Git.

Herdr management support added2026-10-25 for all four agents: native lifecycle
hooks/plugins installed/current, plus shared local `herdr-control` skill. Existing
settings/MCPs/memory and launch commands preserved. See [HERDR.md](HERDR.md) for
paths, installation, checks, context boundary and rollback. New CLI/TUI sessions
load these components; setup did not start/control any live Herdr session.

## Four-agent standard, 2026-10-22

The owner now requires shared tools, MCP integrations and skills to remain aligned
across **Codex, Claude Code, Hermes and OpenCode**. This supersedes the old
three-agent scope and the earlier observation that OpenCode was absent. Global
instructions in all four harnesses record this rule. Preserve harness-specific
formats, native memory providers/plugins, authentication and approval choices.
Check configuration parity before marking future changes complete:

```sh
python3 infrastructure/agents/check-integrations.py
```

This read-only check compares presence, enabled state, command structure, remote
URLs and protected headers without displaying values. Newly added standalone
servers must propagate to all four. Hermes Context7's protected environment
reference remains intentional. This is a completion gate, not an unattended
configuration-writing daemon or proof of live connectivity/automatic capture.

OpenCode **v2.1.2** is installed at `~/.opencode/bin/opencode`, with `opencode2`
also present. Interactive Bash PATH was set by the owner-installed package;
`~/.local/bin/opencode` forwards to that binary for noninteractive agent use.
No second binary was installed. Global mode-0600 configuration lives in
`~/.config/opencode/opencode.json`, using v2 **mcp.servers**, `disabled: false`,
catalog/execution timeouts and **plugins**. Do not overwrite with old v1 examples.

Nine common MCPs are configured in all four: Playwright, Chrome DevTools,
Context7, shadcn, Orva, Supabase, Nivra, REA6.7.0 and OLX. Existing authenticated
URLs/headers were reused. Hermes gained the browser MCPs; Codex/Claude gained OLX.
Codex Chrome DevTools was enabled for the new all-four requirement. Removed OLX's
fixed container name and Hermes-only label to permit concurrent agent sessions;
read-only root, tmpfs, shared-memory and log limits remain. OpenCode OLX explicitly
uses `protocol: "2026-07-28"`, fixing its default legacy-handshake failure.

OpenCode's official `@openviking/opencode-plugin@2026.10.21-1` registers its MCP
and automatic recall/capture hooks, using existing `~/.openviking/ovcli.conf`
and the same account-scoped identity. No new/root key or duplicate MCP entry.
The package includes its memory/skills/experience skills. Extra global skill
roots are `~/.agents/skills`, `~/.claude/skills` and Hermes's productivity skills
(Quick Share/Karakeep). No broad approval/model-policy changes were made.

Explicit home, Homelab and Orva location API checks reported all **10 MCPs
connected**, including OpenViking. Plugin logs confirmed registration and healthy
authenticated memory service. Hermes native tests discovered Playwright25,
ChromeDevTools32 and OLX4 tools. Configuration parity passed. Full automatic
agent-turn recall/capture was not separately exercised. Some native CLI list
calls returned empty before location initialization; use a narrow explicit check:

```sh
opencode api GET /api/mcp --param 'location={"directory":"/home/dev/Homelab"}'
```

Never dump `debug config`, `/api/config` or raw command arguments: expanded
configuration can expose credentials. Large `opencode api` responses can be
truncated; narrow the operation or filter direct authenticated HTTP locally.
Do not mistake truncated JSON for an underlying service failure.

## OpenCode remote UI/API

Upgrade follow-up, 2026-10-25: owner updated the installed binary to **v2.1.4**.
The existing user service was still running its pre-upgrade process. Restarted
with `systemctl --user restart opencode.service`; the actual running executable
reported v2.1.4, HTTPS UI returned200 and unauthenticated API returned401.
Unit remains enabled. Future CLI upgrades may require this separate service
restart; refresh the browser afterward. No authentication, MCP or proxy changes.

- URL: **https://oc.l3b.cc.cd**, private LAN/Tailscale through Caddy.
- Backend: **0.0.0.0:49374** on dev10.1.1.5.
- Explicit DNS-only Cloudflare A record: oc→10.1.1.3, matching local resolution.
- Native username: **opencode**, hard-coded in upstream v2.1.2. An email username
  is not supported. No source patch or extra authentication layer was introduced.
- **HomeLab → OpenCode** Login item holds the generated48-character password,
  URL and owner email metadata (iam.anuragvishwakarma@gmail.com, homelab contact
  l3bctl@gmail.com). Vault and active service credential were compared successfully.
- Native protected configuration/password: `~/.config/opencode/service.json`,0600.

Unauthenticated web UI shell returns200; protected API returns401. Authenticated
API access through HTTPS succeeded. Native API clients use HTTP Basic username
opencode plus the concealed vault password, not an invented Bearer token.
Pairing signs the browser/app into a30-day session; the link is single-use and
expires in5minutes. Password rotation invalidates prior sessions. Generate a
fresh link locally and never save it in Git, memory, Notion or Homepage:

Browser-mode pairing (Accept:text/html) was tested through HTTPS and issued a
session cookie; the subsequent API read succeeded without a Basic header.
Non-browser requests receive JSON credentials instead, so a plain urllib/curl
request is not a browser-cookie test. The upstream HTTP backend omits Secure on
its cookie behind TLS termination; Caddy adds Secure only to OpenCode session
cookies while preserving native HttpOnly/SameSite attributes. Verify this after
proxy or OpenCode upgrades. Homepage deployment is Synced/Healthy at f24dfd3;
all33 native Homepage HTTP checks passed and the live OpenCode card was verified.

```sh
opencode pair --url https://oc.l3b.cc.cd
```

The same server serves browser sessions. Caddy forwards WebSockets/streams and
uses its existing private network policy; no public tunnel/port-forward was
enabled. Homepage has an Applications card and native HTTP monitor, not an
unsupported metrics widget. Network restriction plus native authentication are
both retained; authenticated users inherit the powerful dev account's access.

The enabled systemd user service runs native `opencode serve --service`, reuses
the protected settings, integrates with CLI discovery and restarts on failure.
User lingering is enabled for boot startup without an SSH session. It does not
print passwords or put them in process arguments. Reproduce from the tracked unit:

```sh
install -m 644 infrastructure/agents/opencode.service ~/.config/systemd/user/opencode.service
systemctl --user daemon-reload
systemctl --user enable --now opencode.service
```

Use `systemctl --user restart opencode` for managed restarts. Native settings
commands can stop its daemon; start/restart the systemd unit afterward. Do not
run a second server on the port. Boot/failure-injection tests were not performed.
Original Caddy config retained at `/etc/caddy/Caddyfile.before-opencode`; staged
validation and graceful reload passed, with unrelated routes preserved.

Sources: [v2 web guide](https://github.com/anomalyco/opencode/blob/v2.1.2/services/www/src/docs/content/cli/web.mdx),
[v2 migration](https://github.com/anomalyco/opencode/blob/v2.1.2/services/www/src/docs/content/migrate-v1.mdx),
[OpenViking integration](https://docs.openviking.ai/en/agent-integrations/10-opencode).

## REA, installed 2026-10-22

REA (`rea-agents` from `morluto/rea`) is installed for the existing `dev` user.
The owner reviewed and approved the global Codex, Claude Code and Hermes plan
before configuration changes. Global means all projects for this user on this
machine, not every operating-system user or remote machine.

- Version: `6.7.0`.
- CLI: `/home/dev/.local/bin/rea` and `rea-agents`.
- Package: `/home/dev/.local/lib/node_modules/rea-agents`.
- MCP: local stdio, `npx -y rea-agents@6.7.0 mcp` in all three clients.
- No API key, public endpoint, Docker deployment or reverse proxy is required.
- No optional native analysis engines were installed.

| Agent | User configuration | Bundled workflow skill |
| --- | --- | --- |
| Codex | `~/.codex/config.toml`, `mcp_servers.rea` | `~/.agents/skills/reverse-engineer-anything` |
| Claude Code | `~/.claude.json`, `mcpServers.rea` | `~/.claude/skills/reverse-engineer-anything` |
| Hermes | `~/.hermes/config.yaml`, `mcp_servers.rea` | `~/.hermes/skills/reverse-engineer-anything` |

Codex has `startup_timeout_sec = 30` and `tool_timeout_sec = 450`.
Hermes has `enabled: true`, and its main YAML remains comment-free. REA supports
Hermes profiles; the verified paths above are the active default profile.
Existing MCP entries, authentication and unrelated settings were preserved.

### Reproduce

Node 26.9.0, npm 12.0.2 and `/usr/bin/ps` were available during installation.
Use a reviewed explicit version to reproduce; `@latest` may change later.

```sh
npm install --global --prefix /home/dev/.local rea-agents@6.7.0
npx --yes rea-agents@6.7.0 setup \
  --client codex --client claude_code --client hermes --dry-run --json
```

Review the plan and obtain approval before applying on another installation:

```sh
npx --yes rea-agents@6.7.0 setup \
  --client codex --client claude_code --client hermes --yes --json
```

The actual approved setup used `npx --yes rea-agents@latest setup` with those
three explicit client flags and resolved to 6.7.0. Its version-pinned MCP
registrations avoid silently switching tool contracts at the next session.
Do not use `--all-detected`: an old OpenCode configuration directory exists,
but OpenCode was not requested for installation and no working binary was found.

### Verification

```sh
rea --version
rea doctor --client codex --client claude_code --client hermes --skill --json
codex mcp get rea
claude mcp get rea
hermes mcp test rea
```

Verified on 2026-10-22:

- Setup reported `ready`; scoped doctor reported `healthy: true`.
- All three registrations and the bundled workflow skill were aligned. Skill
  version 42 advertises 207 tools.
- Each configured launcher passed actual MCP initialization, discovery of 207
  tools, and `binary_session` with expected package version 6.7.0.
- Claude's native status reported connected. Hermes's native probe connected
  and discovered 207 tools.
- `analyze_javascript_application` successfully inspected the local Quick Share
  `handler.js` through MCP, with a 256 MiB analyzer heap and 20-second per-source
  timeout. Static inspection did not execute or modify the function.
- Parsed before/after configurations were identical after removing only the
  added REA entry. All three live configs and their backups are mode 0600.
- `hermes gateway restart` completed gracefully, with replacement PID 115700
  starting at 09:27:11 UTC. Gateway and dashboard were active afterward, and
  Telegram polling reconnected. This is not an end-to-end iMessage test.

Restart existing Codex and Claude sessions to discover newly configured tools.
Standalone connection tests do not inject tools into an already-running chat.
The REA server is started on demand by each client, not as a permanent service.

`environment_healthy: false` is expected for the unconfigured optional native
providers (Ghidra, IDA, JADX and Kuna); it does not invalidate the scoped MCP
installation. Static JavaScript inspection works without them. npm also blocked
Frida's native install script under its existing install-script policy. Dynamic
Frida instrumentation was not enabled or tested. Do not claim every advertised
tool can work without its additional prerequisites, or loosen npm policy just
to remove a warning.

### Update and rollback

Review the new package and setup plan before updates. Update the global package
and rerun setup for the same three clients to keep launchers and skills aligned;
then reconnect clients and repeat diagnostics. Never add a floating `@latest`
MCP launcher solely to avoid this controlled refresh.

The installer retained protected first snapshots at:

- `~/.codex/config.toml.rea.backup`
- `~/.claude.json.rea.backup`
- `~/.hermes/config.yaml.rea.backup`

These contain existing credentials and must never enter Git, memory or logs.
For removal, review `rea uninstall --help` and use REA's ownership-aware
uninstaller, which removes REA-owned registrations and skills. Then remove the
global package with `npm uninstall --global --prefix /home/dev/.local rea-agents`.
Do not blindly restore an old full-config backup over newer agent changes.
Do not purge analysis data without an explicit request.

Sources: [official project](https://github.com/morluto/rea),
[installation](https://github.com/morluto/rea/blob/main/docs/installation.md),
[client configuration](https://github.com/morluto/rea/blob/main/docs/client-configuration.md).

## OpenCode check, 2026-10-22

No `opencode` command was available on PATH. No executable was found in the
usual user, Bun, npm-global, system or `/opt` locations, or in the bounded home
directory search. Global npm packages did not include OpenCode.
`~/.config/opencode/AGENTS.md` exists from an earlier setup, but that file alone
does not establish an installed or usable CLI. OpenCode was not installed or
modified as part of the approved three-agent REA setup.
