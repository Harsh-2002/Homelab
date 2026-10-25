---
name: herdr-control
description: Manage Herdr panes, workspaces, terminal commands and coding agents when the user explicitly asks to use Herdr. Not for generic background jobs or unrelated delegation.
---

# Herdr control

Use the installed `herdr` CLI, not tmux commands or a new MCP server. The owner
runs Codex CLI and Claude Code inside Herdr when needed; support those existing
sessions without changing their launch commands, authentication or approvals.

## Context and current instructions

Before any session/pane/agent control, check:

```bash
test "${HERDR_ENV:-}" = 1
```

If false, explain that this agent is outside a Herdr-managed pane and stop the
control task. Do not set HERDR_ENV yourself, connect to an arbitrary focused
session, or start a server to bypass this boundary. A Hermes messaging session
does not inherit the owner's interactive Herdr pane context.

For an authorized control task inside Herdr, run `herdr --skill` and read its
complete output before acting. It is the installed version's authoritative
procedure for IDs, layout, prompts, waits, remote-machine routing and safety.
Use `herdr --help` and the relevant bare command group to resolve current syntax.
Never run bare `herdr` for discovery; it launches/attaches the TUI. Do not probe
mutating nested commands with missing arguments.

## Important local boundaries

- Target the current pane or explicit IDs discovered from JSON. Keep the user's
  focus with `--no-focus`, preserve cwd, and do not invent IDs or agent names.
- Use agent operations for recognized coding agents and pane operations for
  shells/processes. A timeout is not proof input was not delivered; inspect
  state/output before retrying. Do not answer approval dialogs without authority.
- Do not close another task's panes, send prompts to unrelated agents, or
  change topology beyond the user's request.
- Do not stop, restart, update or kill a Herdr server as a diagnostic shortcut.
  `herdr stop` is invalid; `herdr server stop` is destructive to its pane
  processes and requires an explicit shutdown request.
- Native lifecycle hooks/plugins are installed for Codex, Claude Code, Hermes
  and OpenCode. They report agent identity/state; they do not authorize work or
  replace this control skill. `herdr integration status` checks installation.

When explicitly asked to install/repair Herdr integrations, setup commands and
config checks do not require pane control. Preserve existing client settings;
back up configs, use the native integration installer, and do not control live
sessions merely to validate installation.
