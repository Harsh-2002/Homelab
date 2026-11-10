# OpenCode engineering agent family

Status: **installed globally; Atlas is the default for new sessions.** This is a general software-engineering agent set for OpenCode V2, not a homelab-only setup. The homelab is one domain it handles; the same primary agent covers Rust, Go, Node/TypeScript/JavaScript, Python, SQL, infrastructure, testing, QA and security work.

## Design

- **One primary agent** (`atlas`) is the default primary agent. It is a generalist senior/staff-level engineer, not a router with no tools.
- **Role-based subagents** provide context isolation, independent verification and permission separation. They are not language-specific.
- **A separate decision-maker primary agent** convenes an odd-sized jury of independent `voter` subagents and reports the majority decision. It is selected explicitly; Atlas stays the default.
- **Skills are the first-class procedures.** Agents load the installed skill that matches the language, framework, test type or domain. No Rust/Go/Node agents.
- **Atlas chooses the worker model per subagent call** from the approved catalog. The subagent definition also has a default model.
- **Subagents cannot spawn more subagents.** Only primary agents orchestrate: Atlas for engineering work, the decision maker for juries.
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
│   ├── decision-maker.md # independent jury; majority vote
│   ├── voter.md          # one independent vote
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

The approved catalog has three groups. **Any approved model may be used by Atlas or by any subagent; the defaults are just defaults, except that Astra and Fable are escalation-only because of their cost.**

| Group | Models |
|---|---|
| Chinese | `opencode-go/deepseek-v4.1-flash`, `opencode-go/glm-5.3-flash`, `opencode-go/minimax-m3.1-flash` |
| OpenAI Codex | `openai/gpt-6-astra`, `openai/gpt-6.1-sol`, `openai/gpt-6.1-terra`, `openai/gpt-6-luna` |
| Claude Agent | `claude-agent/opus` (Opus 5.5), `claude-agent/sonnet` (Sonnet 5.5), `claude-agent/haiku` (Haiku 5.5), `claude-agent/fable` (Fable 5.2) |

The Claude Agent entries are aliases. They intentionally track the latest model the connected Claude Code CLI exposes, so the catalog does not go stale when Anthropic ships a point release. Claude Code `2.1.322` resolves them to `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5` and `claude-fable-5-2`.

Atlas defaults to DeepSeek V4.1 Flash. Subagents default to DeepSeek V4.1 Flash. If you select another approved model in the picker, Atlas uses it for that session. If Atlas passes a model to a subagent, it uses that model. If no model is passed, the subagent's default applies.

Use **Claude Agent** only. The separate `anthropic/*` provider is not enabled and is removed from the picker. DeepSeek V4 Pro, Kimi, GPT-5 and older families are excluded.

The `model-allowlist` plugin removes every model outside this list, adds the model's default `#variant` when a caller passes a bare approved model, normalizes an invalid variant to that model's default, and falls back to `opencode-go/deepseek-v4.1-flash#max` only when the **model itself** is invalid. An unspecified model is left to the subagent default. `check-models.sh` verifies all eleven approved base IDs.

### Thinking levels

Every explicit model reference carries a `#variant`. The agent defaults already do; Atlas must pass one on every subagent call. The allowlist plugin normalizes a bare model to its default variant, but that is a safety net, not the intended style.

| Family | Variants | Default | Complex work |
|---|---|---|---|
| DeepSeek / GLM | `low`, `high`, `max` | `max` | `max` |
| MiniMax | `low`, `medium`, `high`, `xhigh`, `max` | `max` | `max` |
| OpenAI Astra/Sol | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `high` |
| OpenAI Terra/Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `high` |
| Claude Agent | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `high` |

Chinese models run at `#max` for all work, matching the owner's preference. OpenAI and Claude Agent use `#medium` for routine work, `#high` for multi-file implementation, debugging, verification, security and decisions, and `#xhigh` or `#max` only for exceptional tasks. Examples: `opencode-go/deepseek-v4.1-flash#max`, `openai/gpt-6.1-sol#high`, `claude-agent/opus#high`.

### Premium models — escalation only

`openai/gpt-6-astra` and `claude-agent/fable` are the two most expensive models in the catalog:

- **Astra:** about $10 input / $50 output per 1M tokens; $20 / $75 above 272k context.
- **Fable 5.2:** about $8 input / $40 output per 1M tokens.
- **Chinese flash models:** about $0.15 input / $0.5–0.6 output — roughly 50–100× cheaper on output.

Do not use Astra or Fable for routine implementation, docs, tests, research or normal verification. Use one only when the user explicitly asks, a cheaper model has already failed on the same task, or the task is genuinely exceptional and the expected value justifies the cost. State the justification in the final answer. In a decision jury, at most one seat may be premium; never make the whole jury premium.

## Decision maker

`decision-maker` is a separate **primary** agent, not Atlas's default. Select it from the agent picker when you want a decision rather than implementation:

```text
/agent decision-maker
Should we move the internal CLI from Go to Rust?
```

It frames the question, gathers facts only if needed, then spawns an odd number of independent `voter` subagents — 3 normally, 5 for high-stakes or irreversible decisions, 7 only for an exceptionally large jury. Each voter gets a different approved model and the same evidence, and never sees another vote. The majority wins. If no option has a majority, it runs a runoff between the top two; a tied runoff uses the highest-capability model's vote and says so.

The final report contains the decision, the tally, confidence, the majority reasoning, the strongest dissent, assumptions, what would change the decision, and each model's vote. The decision maker does not implement the winning option; hand that back to Atlas.

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

New sessions start with Atlas on DeepSeek V4.1 Flash. The model selector is limited to the eleven approved models by the plugin. The current session may still be an older Build session; use the agent selector once or open a new session to get Atlas.

## Guardrails

- The `model-allowlist` plugin enforces the approved-model list for the model picker and subagent calls.
- `security` requires explicit scope and authorization. No production scanning, DoS, destructive exploitation, credential extraction or data exfiltration.
- `verifier` must not edit code or weaken tests; it works in a disposable worktree.
- Atlas must ask before destructive, production, external or credential-sensitive actions.
- No secrets in agent files, prompts, logs or skill content.
