# OpenCode engineering agent family

Status: **installed globally; Atlas is the default for new sessions.** This is a general software-engineering agent set for OpenCode V2, not a homelab-only setup. The homelab is one domain it handles; the same primary agent covers Rust, Go, Node/TypeScript/JavaScript, Python, SQL, infrastructure, testing, QA and security work.

## Design

- **One primary agent** (`atlas`) is the default primary agent. It is a generalist senior/staff-level engineer, not a router with no tools.
- **Role-based subagents** provide context isolation, independent verification and permission separation. They are not language-specific.
- **Skills are the first-class procedures.** Agents load the installed skill that matches the language, framework, test type or domain. No Rust/Go/Node agents.
- **Atlas chooses the worker model per subagent call** from a three-model catalog. The subagent definition also has a default model.
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

Only these three models are approved:

| Model | Use |
|---|---|
| `opencode-go/deepseek-v4.1-flash` | Default Atlas model and default worker; all-round |
| `opencode-go/glm-5.3-flash` | Alternative for implementation, frontend/TS, docs |
| `opencode-go/minimax-m3.1-flash` | Alternative for UI/frontend, independent checks |

Atlas runs on DeepSeek V4.1 Flash by default. The user can switch Atlas to GLM 5.3 Flash or MiniMax 3.1 Flash in the model selector.

Subagents default to DeepSeek V4.1 Flash. Atlas may override a subagent call to GLM 5.3 Flash or MiniMax 3.1 Flash. DeepSeek V4 Pro, Kimi K3.1 Pro, GPT, Qwen and GLM-5.3 non-Flash are deliberately excluded. There is no escalation model; a failed task is retried with another approved model or handled by Atlas.

The `model-allowlist` plugin removes every other model from the picker and rewrites any subagent call outside the three to DeepSeek V4.1 Flash. `check-models.sh` verifies the three IDs are present.

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

New sessions start with Atlas on DeepSeek V4.1 Flash. The model selector is limited to the three approved models by the plugin. The current session may still be an older Build session; use the agent selector once or open a new session to get Atlas.

## Guardrails

- The `model-allowlist` plugin enforces the three-model rule for the model picker and subagent calls.
- `security` requires explicit scope and authorization. No production scanning, DoS, destructive exploitation, credential extraction or data exfiltration.
- `verifier` must not edit code or weaken tests; it works in a disposable worktree.
- Atlas must ask before destructive, production, external or credential-sensitive actions.
- No secrets in agent files, prompts, logs or skill content.
