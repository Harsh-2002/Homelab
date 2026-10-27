# Claude subscription in OpenCode

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
