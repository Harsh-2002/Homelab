# Claude Code on dev

Configured on 2026-10-05 for the existing dev account, Claude Code2.1.289. User-scope MCP configuration lives in `~/.claude.json`; plugin settings live in `~/.claude/settings.json`.

Enabled development connections: Playwright (`@playwright/mcp@latest`, Chrome/headless), Chrome DevTools (`chrome-devtools-mcp@latest`, headless), Context7 (`@upstash/context7-mcp@latest`), shadcn (`shadcn@latest mcp`), and HTTP Orva (`https://orva.l3b.cc.cd/mcp`). All local launchers use `npx -y`. Orva reuses the existing Codex bearer credential without exposing it or creating another vault item. Preserve all existing settings when changing MCPs. Do not print the whole user configuration because it contains that header.

OpenViking uses the official `openviking-memory@openviking` Claude plugin0.6.9, installed at user scope from the official GitHub marketplace URL. It supplies its own MCP proxy and nine lifecycle hooks. It reuses `~/.openviking/ovcli.conf` (0600) with the existing account-scoped key and `https://memory.l3b.cc.cd`; do not add a second raw OpenViking MCP entry or use the root key. Marketplace auto-update is currently off; update deliberately and restart Claude. Automatic conversation/tool capture is privacy-sensitive: keep credentials out of prompts and outputs.

## Login correction

The copied Linux `~/.claude/.credentials.json` was readable and `claude auth status` reported an existing logged-in subscription. Its access and refresh token fields were present. Interactive launch nevertheless entered first-run onboarding, which requested login: `~/.claude.json` lacked `hasCompletedOnboarding`. Set the local completed-onboarding metadata while preserving existing config and tokens. Tightened `~/.claude` to0700, `.credentials.json` and `.claude.json` to0600. No credential file content was printed, token replaced, or account changed.

A minimal actual model request returned AUTH_OK. A fresh interactive launch reached the ordinary repository trust prompt rather than login. Repository trust was left for the owner; do not treat that prompt as an authentication failure. Copied tokens are not a permanent login guarantee: future expiry/revocation may require native reauthentication. Never delete credentials merely to suppress onboarding.

## Verification

## User settings and shell shortcut

Merged the owner's settings into `~/.claude/settings.json`, preserving the OpenViking marketplace and enabled plugin. Theme auto, effort xhigh (supported by installed CLI), always-thinking enabled, gitignore respected, latest update channel, 30-day cleanup, turn duration and terminal progress bar enabled, spinner tips disabled, English language, and empty commit/PR attribution. `defaultMode` is correctly nested as `permissions.defaultMode: acceptEdits`; `skipDangerousModePermissionPrompt` is true.

Persistent Bash alias in `~/.bashrc`: `alias cc='claude --dangerously-skip-permissions'`. A fresh interactive Bash resolves it correctly. Use `source ~/.bashrc` in an existing terminal. `cc` bypasses Claude permission checks and can execute destructive commands without approval; this is explicitly requested for the trusted dev environment, not a security boundary. Normal `claude` retains acceptEdits. Tokens are unchanged.

## Connection checks

`claude mcp list` reported all six integrations connected, plus the existing Claude Docs connection. OpenViking's bundled memory doctor reported no problems,16 upstream MCP tools, healthy storage/embedding components, successful session injection/recall, and two captured test messages with no failures. This does not claim that every browser workflow or Orva mutation was tested. No browser navigation, deployment or application data mutation was part of the connection checks.

```sh
claude auth status
claude mcp list
claude plugin list
node ~/.claude/plugins/cache/openviking/openviking-memory/0.6.9/scripts/ov-memory-doctor.mjs --no-color
```

Sources: [Claude MCP](https://code.claude.com/docs/en/mcp), [OpenViking Claude integration](https://docs.openviking.ai/en/agent-integrations/02-claude-code).
