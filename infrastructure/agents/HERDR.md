# Herdr support across four coding agents

Configured 2026-10-25 using installed Herdr 0.9.1. Owner runs Codex CLI and Claude
Code inside Herdr when needed; all four agents should understand Herdr control.
No new MCP, service, credentials, model policy or approval changes.

## Native lifecycle integrations

Installed using Herdr's own supported commands:

```bash
herdr integration install codex
herdr integration install claude
herdr integration install hermes
herdr integration install opencode
herdr integration status
```

| Agent | Native component | Verified version |
|---|---|---|
| Codex | `~/.codex/herdr-agent-state.sh`, existing hooks.json entries, hooks feature |v8(current before install too) |
| Claude Code | `~/.claude/hooks/herdr-agent-state.sh`, merged settings.json hooks |v10 |
| Hermes | `~/.hermes/plugins/herdr-agent-state/`, enabled plugin ID |v5 |
| OpenCode | `~/.config/opencode/plugins/herdr-agent-state.js`, TUI session plugin and tui.jsonc |v12 |

These report session identity/lifecycle to Herdr. They do not grant permission
to control other agents. Open new CLI/TUI sessions to load newly installed
hooks/plugins. No existing sessions, gateway or server were restarted solely
to load these integrations.

## Shared control skill

Canonical source: `infrastructure/agents/skills/herdr-control/SKILL.md`.
Symlinked globally as `herdr-control` under `~/.agents/skills`, `~/.codex/skills`,
`~/.claude/skills` and `~/.hermes/skills`. OpenCode already discovers the shared
`~/.agents/skills` root. Its existing main config is unchanged. Hermes's older
bundled `autonomous-ai-agents/herdr` skill is preserved, not deleted/overwritten.

The new skill is intentionally local/environment-bound: it requires Herdr's
installed CLI and the process's real pane context. Do not upload it as a portable
OpenViking skill. Shared memory holds this runbook and the durable preference.

Before control, the agent must verify `HERDR_ENV=1`. Outside Herdr, stop the
control task; never fake environment variables, take over the focused session,
or auto-start a server. Inside Herdr, read the complete `herdr --skill` output,
then relevant CLI help. That installed version is authoritative. Do not browse
the full website/manual merely because Herdr is present.

Use explicit returned IDs/current pane, preserve cwd and user focus, and use
agent operations for recognized agents versus pane operations for shells.
Timeouts do not justify blindly resending input. Approval dialogs require
authority. Do not close others' resources or launch unrelated agents.
`herdr stop` is invalid; `herdr server stop` stops the server/pane processes and
is never a routine diagnostic action. Only use it for an explicit shutdown task.

Current config is `~/.config/herdr/config.toml`; `HERDR_CONFIG_PATH` overrides
the file. Logs are `~/.config/herdr/herdr.log`, `herdr-client.log` and
`herdr-server.log`. These files were not edited for this setup. The pasted
Windows `ssh herdr` reached the proxy host, while `ssh dev` reached the intended
development VM. No Windows SSH alias was changed; don't assume that alias means
the Herdr service or a Herdr session.

## Verification and boundaries

- Protected pre-change client configs retained under local state directory
  `herdr-integrations-qa1x4zwy` (mode 0700; files 0600). Never commit backups.
- All four native integration status entries report current.
- Skill validator passes; all four resolve the same control skill source.
- Semantic config comparisons show Codex settings preserved except native hooks
  enablement, Hermes preserved except new enabled plugin, OpenCode main config
  byte-identical, and preexisting Claude/Codex hooks retained.
- Shared MCP/native OpenViking configuration unchanged; parity checker passes.
- Herdr server was not running and this setup chat was outside a managed pane.
  No real pane/agent start, prompt, close or lifecycle socket roundtrip was tested.
  Installation checks are not a claim of end-to-end agent control validation.
- No inference/model calls or prompts to existing tasks used as installation tests.

Re-run `python3 infrastructure/agents/check-integrations.py` after updates. It
now checks Herdr integration status and shared skill parity in addition to MCPs.
After upgrading Herdr, rerun the four native installers and validate again;
leave runtime instructions with `herdr --skill`, not an obsolete copied manual.

## Rollback

Use `herdr integration uninstall <agent>` only for the requested client(s),
then remove only this task's `herdr-control` symlinks if no longer wanted.
Preserve other hooks/plugins and Hermes's original bundled skill. Codex's hook
feature flag may remain enabled after uninstall; don't disable it if other hooks
depend on it. Restore protected config backups only after comparing newer edits.
No Herdr server shutdown is required to remove discovery instructions.

Sources: installed `herdr --help`, `herdr --skill`, integration status and
[Herdr0.9.1 CLI reference](https://github.com/herdrdev/herdr/blob/master/docs/versions/0.9.1/website/src/content/docs/cli-reference.mdx).
