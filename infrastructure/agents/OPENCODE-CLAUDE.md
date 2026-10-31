# Claude subscription in OpenCode

## Current state — native migration completed, 31 October 2026

The owner subsequently authorized upgrading immediately. Installed the explicit
current v2 release2.2.5 through the official curl upgrade path and restarted the
user service to activate it. Do not use GitHub's unqualified latest-release
endpoint for v2: it returned the separate v1.19.5 line during this upgrade.
The newest v2 release was verified from the release list and official changelog.

Saved protected configuration, previous binary and a consistent SQLite session
snapshot (quick_check=ok) before upgrade. The old service exited130 during the
requested stop; the new service is active as PID136077, starting08:27:23UTC.
Running-server executable and CLI both report2.2.5. No unexpected restart has
occurred since activation. Existing HTTPS endpoint responds200. All63 pre-upgrade stored session IDs and
all pre-upgrade message IDs remain present; the new verification session makes64.

Connected built-in `claude-agent` with `opencode auth login claude-agent --method
claude-login`. Existing Claude CLI2.1.302 reports claude.ai/firstParty/Max; no new
browser sign-in or API key. Actual native model discovery supplies IDs and effort
variants; no global/Build/Plan Claude default was reintroduced. Other agents'
model selections and all shared tools/memory configuration remain intact.

A real turn using claude-agent/claude-haiku-4-5-20251001 completed exactly one
shell call (`printf NATIVE_CLAUDE_TOOL_OK`) and replied NATIVE_CLAUDE_OK. A second
turn in the same OpenCode session recalled the exact tool output without tools.
Session: ses_e6eed1c2cfferwvvyOMJjwRBAs. Both requests reported subscription cost0.
Native provider/model variants and all10 MCPs, including OpenViking and REA,
were then verified in the already-live Homelab location. Four-agent static checks
pass. No saturation, concurrency or automatic memory-capture guarantee is implied.

The old plugin is absent from configuration and live provider discovery; its
343MiB private cache/dependencies were removed after checking process command
lines and mappings for references. Shared Claude CLI/login and unrelated caches
remain. The native provider uses no third-party loopback bridge. Current diagrams
show the native SDK route. Historical setup/retirement evidence below is retained.

Read-only validation for an already-used location (never initialize extra
locations just for a health poll under memory pressure):

```bash
python3 infrastructure/agents/check-integrations.py
python3 infrastructure/agents/verify-opencode-claude.py --directory /home/dev/Homelab
```

The native verifier sends no prompt, does not call `opencode models`, and explicitly
sets x-opencode-directory so it does not accidentally initialize the server's
home location with another set of MCP processes. `--session` can check the known
smoke test's persisted tool/resume evidence. Existing Claude CLI login and native
OpenViking account identity were preserved; no expanded credentials were printed.

## Earlier checkpoint — legacy startup retired, 31 October 2026

Owner confirmed current agents do not use the external Claude provider models.
Removed only @openchamber/opencode-claude1.6.0 from protected global startup
configuration, exact setup-installed global/Build/Plan Claude model overrides,
and the matching claude-sdk.conf systemd environment drop-in. Defaults before
installation had no model/agent override; restored that absence without choosing
another paid provider. Preserved other plugins, MCPs, skills, provider settings,
existing sessions and Claude CLI credentials. A protected rollback copy was made.

**Not a completed native migration:** installed OpenCode/server remains2.1.4.
The official built-in provider requires2.2.3+. Its ID is `claude-agent`, not the
old plugin's `claude-code`. No upgrade, manual restart, daemon-reload or location
reload was issued. Package/SDK cache files and any already-loaded legacy copy
remain for the current process; deleting them while it is active is deferred.
Do not describe runtime/package removal or native inference as completed.

## Verified upstream research

- [Official2.2.3 release](https://github.com/anomalyco/opencode/releases/tag/v2.2.3)
  adds Claude Agent using the installed Claude Code CLI and its existing login.
- [Versioned implementation/design](https://github.com/anomalyco/opencode/blob/v2.2.3/specs/v2/claude-agent-provider.md)
  confirms local Claude Agent SDK execution, OpenCode tools/permissions, agent
  instructions, MCPs and skills. The native provider does not use Claude Code's
  separate MCP/skill/auto-memory settings. Preserve the existing native OpenViking
  integration in OpenCode rather than relying on Claude auto-memory.
- [Upstream bridge README](https://github.com/openchamber/opencode-claude)
  now states the plugin is unnecessary on2.2.3+ and the repository is archived.
- The generic providers page still contains older Anthropic API/OAuth guidance;
  use the newer release and versioned native-provider specification for this
  SDK-based path. An Anthropic API-key provider is a different billing route.
- [Installed-version config reload tests](https://github.com/anomalyco/opencode/blob/v2.1.4/packages/core/test/config/reload.test.ts)
  distinguish automatic config-domain refresh from external-plugin reload.
  Config writes are watched, so saving a file is not an inert staging mechanism.
  No explicit location reload was performed. The service PID/restart count stayed
  unchanged during the actual retirement edits; HTTPS remained200.

Existing Claude CLI login can be reused on the same Linux user. After upgrading,
select Claude Agent in `/connect` to record/check that login method. Only sign in
again with the CLI if its session is expired. Never read/copy .credentials.json,
extract OAuth tokens or add an API key for subscription usage.

## Safe completion at an idle maintenance window

1. Confirm agents and their tool calls are idle. Preserve protected config,
   session database and rollback state. Recheck upstream release/plugin compatibility.
2. Upgrade to a supported release with built-in Claude Agent (2.2.3 minimum;
   latest observed release during research2.2.5). Activating new server code
   requires a new server process; do not promise an uninterrupted in-flight turn.
3. Use existing CLI login, then choose Claude Agent in `/connect`. Discover the
   actual returned `claude-agent/<model-id>` and supported effort variants.
   Do not mechanically reuse the old plugin's IDs or assume identical model limits.
4. Verify an isolated real model/tool turn and resumption, OpenCode permissions,
   native OpenViking/MCP connections and browser access. Preserve unrelated active
   model selections. Session history persistence does not prove seamless reuse
   of the old bridge's separate SDK session cache.
5. After confirming no process references the old package, remove only its unused
   cache/SDK dependencies, leaving shared Claude CLI credentials and other packages.
   Update live verification, shared integration checks and architecture to the
   actual native route. Do not run the old installer below; its tracked helper
   now refuses to reinstall the retired bridge.

## Incident observed during read-only verification

A live model-catalog/integration probe initialized extra location/MCP processes.
At08:10:31 UTC on31 October the dev guest's kernel recorded a global OOM kill of
OpenCode PID1005. Its existing Restart=on-failure policy restarted it automatically
at08:10:36 as PID100147; HTTPS recovered200. No explicit restart command was issued.
The service cgroup peak included child workloads (5.5GiB RAM/1.8GiB swap); this
is not the main server's RSS or proof that the probe alone caused exhaustion.
Concurrent sandbox/load/browser processes were present. The verifier also saw
REA unavailable before the restart. Do not claim every live MCP check passed.

Stopped live catalog/location/MCP probes after the event. The retired-plugin
verifier now exits without initializing a live location when the startup entry
is absent. Shared four-agent static integration checks pass. No child workload
was killed, VM memory changed, or in-flight session replay attempted. This dev
OOM is distinct from the earlier physical-host incident and does not explain
px20's abrupt loss or px30's power-key events.

## Historical installation and verification — 27 October 2026

The following is a historical record, not the current deployment instructions.

Configured on dev, 2026-10-27, using
[@openchamber/opencode-claude](https://github.com/openchamber/opencode-claude)
1.6.0 (reviewed source 507cb87bfe9f17ee1d560e4da42e4fd27b2ac5c4).
Installed dependency: official Claude Agent SDK 0.3.311; Claude CLI 2.1.302;
OpenCode/service 2.1.4. The plugin declares an SDK semver range, so a fresh
package resolution can select another compatible SDK version. Recheck after
updates instead of claiming a fully frozen transitive dependency graph.

## Request and authentication path

OpenCode → loopback-only plugin proxy → official Claude Agent SDK → existing
Claude Code CLI → Anthropic subscription. This is not a custom Anthropic HTTP
proxy that extracts OAuth tokens. The CLI owns authentication and session
credentials; no Claude API key or token was added to OpenCode, Git, shell
startup, or the systemd environment.

The existing /home/dev/.claude login reports claude.ai, firstParty and Max.
A live plugin request and tool call succeeded using it; no new sign-in was
needed. The owner initially planned to authenticate afterward, then asked to
reuse the current CLI login. This supersedes the initial pending-auth plan.
For later reauthentication, use the same Linux user and configuration directory:

```bash
CLAUDE_CONFIG_DIR=/home/dev/.claude claude auth login --claudeai
systemctl --user restart opencode.service
```

Do not read or print .credentials.json. Use narrowly filtered `claude auth
status --json` metadata if needed; it is not a substitute for an inference test.
Other agents' providers and OpenViking account identity remain unchanged.

## Coding defaults and environment

Global primary: `claude-code/claude-opus-5-5[1m]`. Build and Plan explicitly select
`#xhigh`; OpenCode's root model alone does not retain an effort variant. The
provider catalog confirms a 1,000,000-token context and xhigh support. This
context limit does not mean every request uses a full million tokens. Existing
sessions retain their selections; start a new session or explicitly pick the
Claude Code model to change one. Sonnet/Haiku and existing providers remain
selectable. The default is the regular model, not the separate :fast entry.

Native Plan permissions, OpenCode tools, MCPs and skill discovery are preserved.
The plugin supplies those tools to Claude through its SDK bridge, while Claude's
own built-in tools are disabled. Claude Code reads project instructions; the
plugin also forwards applicable OpenCode instructions and skills. The plugin's
session reuse, rate-limit fast-fail, title handling, compaction and dynamic-system
section defaults remain intact. No blanket permission bypass was added.

The tracked [service drop-in](opencode-claude.conf) sets only:

- CLAUDE_CONFIG_DIR=/home/dev/.claude, shared with the existing login.
- CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH=8192, preserving longer tool descriptions.
- OPENCODE_CLAUDE_DEBUG=0, leaving verbose logging off.

No fixed proxy port or working-directory override is needed. The proxy allocates
a free loopback port, and the plugin forwards each request's actual project
folder. Do not set OPENCODE_CLAUDE_CWD to the home directory for all projects.
Do not set rate-limit fast-fail to 0. API-key/token overrides are removed from
the plugin's Claude child environment; none were present on the active server.
The public-facing OpenCode listener/proxy/login and LAN/Tailscale restrictions
were preserved. The new Claude proxy has no Caddy route or LAN listener.

## Reproduce

The protected ~/.config/opencode/opencode.json keeps existing MCP credentials.
Never copy its expanded contents into this repository. Install the package, then
merge the tracked non-secret defaults and service drop-in:

```bash
opencode plugin add @openchamber/opencode-claude@1.6.0
python3 infrastructure/agents/configure-opencode-claude.py
systemctl --user daemon-reload
systemctl --user restart opencode.service
opencode models
python3 infrastructure/agents/verify-opencode-claude.py
python3 infrastructure/agents/check-integrations.py
```

The helper creates private config backups only when the defaults change. It
preserves MCPs, existing plugins, skill roots and unrelated agent fields. It
refuses to replace a differing environment drop-in without review. The original
pre-install config and service/password state are in the private directory
~/.config/opencode/backups/claude-sdk-20261027T132837Z/. Editable diagrams were
also preserved there before regeneration. Backups contain secrets: never commit
or upload them.

## Verified behavior

- Native provider/model discovery, with Build and Plan resolving the intended
  Opus model and xhigh variant.
- Proxy health/model endpoints200; proxy host is127.0.0.1; browser-origin requests403.
- Existing Max auth: actual OpenCode turn returned CLAUDE_SDK_OK. Its recorded
  tool state completed, with actual output CLAUDE_SDK_TOOL_OK.
- A second turn resumed that OpenCode session and recalled the prior tool result.
- All10 existing MCPs, including OpenViking, reported connected. Shared MCP/skill
  checks passed. Existing HTTPS UI returned200.
- Architecture inventory, native Excalidraw flow and SVG/Mermaid/PNG/PDF exports
  refreshed. No private-address exports staged for public Git.

Read-only checks:

```bash
python3 infrastructure/agents/verify-opencode-claude.py
python3 infrastructure/agents/check-integrations.py
```

A real model/tool probe, which consumes subscription usage, can be repeated when
needed (do not run it on every health poll):

```bash
opencode run --model 'claude-code/claude-opus-5-5[1m]#xhigh' \
  'Use the shell tool once to run printf CLAUDE_SDK_TOOL_OK, then reply with exactly CLAUDE_SDK_OK. Do not read files or run any other commands.'
```

The test session was ses_e826caec6ffetrMdVXQi5ha3jl. Its recorded actual tool
output can be checked using verify-opencode-claude.py --session with that ID.
No destructive editing, remote deployment, fast mode, rate-limit failover or
long-context saturation test was attempted. Subscription availability and
limits remain those of the signed-in Claude account.

## Updates and rollback

Review the upstream release before `opencode plugin update`, then repeat the
native catalog, proxy, tool and resume checks. Preserve OpenViking and all
other plugin entries. A package pin records what was validated; there is no
new automatic updater.

To roll back, compare current changes with the private pre-install backup,
remove only this plugin and its Build/Plan/global model preferences, and remove
only the Claude SDK drop-in. Restore the previous choices rather than replacing
all config if other edits occurred. Reload systemd and restart OpenCode. Do not
remove the shared Claude CLI login or existing OpenCode service/password state.
