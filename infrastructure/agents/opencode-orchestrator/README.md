# OpenCode engineering agent family

Status: **installed globally; Atlas is the default for new sessions.** This is a general software-engineering agent set for OpenCode V2, not a homelab-only setup. The homelab is one domain it handles; the same primary agent covers Rust, Go, Node/TypeScript/JavaScript, Python, SQL, infrastructure, testing, QA and security work.

## Design

- **One primary agent** (`atlas`) is the default primary agent. It is a generalist senior/staff-level engineer, not a router with no tools.
- **Role-based subagents** provide context isolation, independent verification and permission separation. They are not language-specific.
- **Skills are the first-class procedures.** Agents load the installed skill that matches the language, framework, test type or domain. No Rust/Go/Node agents.
- **Atlas chooses the worker model per subagent call** from the approved catalog. The subagent definition also has a default model.
- **Subagents cannot spawn more subagents.** Atlas is the only orchestrator.
- **No same-file parallel writes.** Parallelism is for independent read-only research, verification and separate modules.

## Files

```text
opencode-orchestrator/
├── README.md
├── AGENTS.template.md
├── install.sh
├── check-models.sh
├── agents/
│   ├── atlas.md
│   ├── build.md          # compatibility override for existing Build sessions
│   ├── explorer.md
│   ├── implementer.md
│   ├── verifier.md
│   └── security.md
├── skills/
│   ├── model-catalog/
│   │   └── SKILL.md
│   └── verification-worktree/
│       └── SKILL.md
├── plugins/
│   └── model-allowlist/
│       └── index.ts
└── evals/
    └── tasks.md
```

## Models

The approved catalog has three groups. **Any approved model may be used by Atlas or by any subagent; the defaults are just defaults.**

| Group | Models |
|---|---|
| Chinese | `opencode-go/deepseek-v4.1-flash`, `opencode-go/glm-5.3-flash`, `opencode-go/minimax-m3.1-flash` |
| OpenAI Codex | `openai/gpt-6-astra`, `openai/gpt-6.1-sol`, `openai/gpt-6.1-terra`, `openai/gpt-6-luna` |
| Claude Agent | `claude-agent/claude-opus-5`, `claude-agent/claude-sonnet-5`, `claude-agent/claude-haiku-4-5-20251001` |

Atlas defaults to DeepSeek V4.1 Flash. Subagents default to DeepSeek V4.1 Flash. If you select another approved model in the picker, Atlas uses it for that session. If Atlas passes a model to a subagent, it uses that model. If no model is passed, the subagent's default applies.

Use **Claude Agent** only. The separate `anthropic/*` provider is not enabled and is removed from the picker. DeepSeek V4 Pro, Kimi, GPT-5 and older families are excluded.

The `model-allowlist` plugin removes every model outside this list and falls back to DeepSeek V4.1 Flash only when an **invalid** model is passed. An unspecified model is left to the subagent default. `check-models.sh` verifies all approved IDs.

## Routing

Atlas does small, sequential, context-heavy work itself. It delegates when:

- the codebase area is unknown and would bloat its context,
- research paths are independent,
- verification should be independent from implementation,
- a task has a clean interface and little shared context,
- permissions should be separated.

It does not delegate simple one-file changes, same-file parallel edits, or tasks that need continuous shared context.

Normal work uses at most **2–4 subagents**. Each gets a scoped brief: goal, context, files, constraints, acceptance criteria, output format, and what not to touch.

## Install

Global (all projects):

```sh
./install.sh
```

Project-local (overrides for one repository):

```sh
./install.sh .opencode
```

Global installs need the local plugin registered in `~/.config/opencode/opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "atlas",
  "plugins": [
    "/home/dev/.config/opencode/plugins/model-allowlist"
  ]
}
```

Project-local plugins under `.opencode/plugins/` load automatically.

`default_agent` applies to **new sessions**. Existing sessions keep their stored agent and model. The `build.md` override gives existing Build sessions Atlas's prompt, model and permissions; the UI may still label them Build. Use `opencode reload` for configuration changes; a binary upgrade still needs a service restart.

## Verification safety

`verifier` loads `verification-worktree` and runs tests in a disposable worktree or microsandbox. It must not modify the main checkout. If it cannot create an isolated environment, it stops and asks.

`security` is scope-gated and read-only. It denies `.env` files, private keys, `~/.ssh`, OpenCode auth stores and `secrets/` paths. It must not scan production or extract credentials.

## Activation

New sessions start with Atlas on DeepSeek V4.1 Flash. The model selector is limited to the ten approved models by the plugin. The current session may still be an older Build session; use the agent selector once or open a new session to get Atlas.

## Guardrails

- The `model-allowlist` plugin enforces the approved-model list for the model picker and subagent calls.
- `security` requires explicit scope and authorization. No production scanning, DoS, destructive exploitation, credential extraction or data exfiltration.
- `verifier` must not edit code or weaken tests; it works in a disposable worktree.
- Atlas must ask before destructive, production, external or credential-sensitive actions.
- No secrets in agent files, prompts, logs or skill content.
