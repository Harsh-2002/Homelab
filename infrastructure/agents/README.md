# Shared coding-agent tools on dev

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
