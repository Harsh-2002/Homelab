# OpenCode model policy, skills and plugin

This directory holds the shared OpenCode setup: the **model allowlist plugin**, the **model-catalog skill** and a few engineering skills. It no longer installs custom agents.

## History and rollback

From 2026-10 to 2026-11-20 this directory installed a family of custom agents (Atlas, Forge, Scout, Vouch, Shield, Juror, Oracle, plus a `build` override) that delegated work to subagents automatically. On 2026-11-20 the owner removed them: during real project work the automatic delegation misbehaved and damaged a project. OpenCode now runs with its own built-in agents, and a subagent is started only when the user asks for one in chat, on the model the user names.

To roll back:

```sh
git checkout pre-agent-removal-20261120 -- infrastructure/agents/opencode-orchestrator
infrastructure/agents/opencode-orchestrator/install.sh
```

then set `"default_agent": "atlas"` in `~/.config/opencode/opencode.json`. The tag `pre-agent-removal-20261120` is pushed. A copy of the installed config (agents, skills, plugins, `opencode.json`, `AGENTS.md`) was saved to `/BACKUP/opencode-config-before-agent-removal-20261120-162141` (root-only, may contain secrets). The directory name `opencode-orchestrator` is kept so existing links and history still work.

## What is here

| Path | Purpose |
|---|---|
| `plugins/model-allowlist/index.ts` | Limits the model picker to the 13 approved models, normalizes thinking variants, replaces an unapproved model in a `subagent` call with `opencode-go/deepseek-v4.1-flash#max` |
| `skills/model-catalog/` | Approved models, thinking levels, tiers and fallback chains. Load it when choosing a model for a subagent or when a model fails |
| `skills/security-audit/` | Cloudflare `security-audit` skill (MIT, vendored) with an OpenCode adapter that maps its roles to the built-in `explore` and `general` subagents |
| `skills/verification-worktree/` | Run tests in a disposable worktree or microsandbox so the main tree is never changed |
| `check-models.sh` | Fails if an approved model is missing from `opencode models` |
| `install.sh` | Copies skills and the plugin into `~/.config/opencode` and removes any custom agent files |
| `opencode.json.example` | Global config example: plugin, `anthropic` provider denial, Claude Agent versioned model entries |
| `AGENTS.template.md` | Project `AGENTS.md` starter, including the "subagents only when asked" rule |
| `evals/tasks.md` | Checks to run after installing |

## Models

13 approved models, reconciled with the live server on 2026-11-18:

| Group | Models |
|---|---|
| OpenCode Go | `opencode-go/deepseek-v4.1-flash` (DeepSeek V4.1 Flash 1017), `opencode-go/glm-5.3`, `opencode-go/glm-5.3-flash` |
| OpenAI Codex | `openai/gpt-6.2-astra`, `openai/gpt-6.2-sol`, `openai/gpt-6-astra`, `openai/gpt-6.1-sol`, `openai/gpt-6.1-terra`, `openai/gpt-6-luna` |
| Claude Agent | `claude-agent/claude-opus-5-5`, `claude-agent/claude-sonnet-5-5`, `claude-agent/claude-haiku-5-5`, `claude-agent/claude-fable-5-2` |

Excluded: OpenCode free models, MiniMax, Kimi, Qwen and every other Go model, DeepSeek V4 Pro, GPT-5 and older, all `anthropic/*` models. Use Claude Agent only; the separate `anthropic/*` provider is denied by a global `provider.use` policy. The Claude Agent entries use the original versioned IDs (the provider also exposes `opus`, `sonnet`, `haiku` and `fable` aliases, which the plugin hides); see `opencode.json.example`.

Thinking levels, tiers, prices, Go limits and fallback chains are in `skills/model-catalog/SKILL.md`. In short: Go models run at `#max`; OpenAI and Claude use `#medium` for routine work and `#high` for complex work; Astra and Fable are escalation-only because of their cost.

The default model is set in `opencode.json` as `"model": "opencode-go/deepseek-v4.1-flash#max"`. **Keep it set:** without a custom agent supplying a model, a new session otherwise defaulted to `openai/gpt-6.2-astra`, the most expensive model (seen on 2026-11-20). Pick another model in the picker when needed.

## Subagents

Subagents are on demand. Ask in chat, for example "use a subagent with `openai/gpt-6.2-sol#high` to review this". OpenCode starts its built-in `general` or `explore` subagent on that model. The `AGENTS.md` rule is: do not delegate on your own initiative, subagents cannot spawn subagents, no parallel writes to the same files, and the parent session owns the final answer.

## Install

```sh
infrastructure/agents/opencode-orchestrator/install.sh
```

Then `opencode reload`; no service restart is needed for config changes. The script runs `check-models.sh` when `opencode` is available. Remove `default_agent` from `opencode.json` if it is still set.

## Security audit skill

`skills/security-audit/` is the Cloudflare [`security-audit`](https://github.com/cloudflare/security-audit-skill) skill, MIT-licensed, vendored at upstream commit `c1c8a8c`, with its own tests (`validate-findings.cjs`, `validate-coverage-ledger.cjs`). Guidance mode is for focused reviews. Full audit mode needs subagents, so run it only when the user explicitly asks and authorizes the scope. Built-in subagents have normal tool permissions, so the read-only and no-production rules must be written into each brief.

## Guardrails

- The plugin keeps the picker inside the approved list. It is not a security boundary.
- Never send credentials or private homelab configuration to a model you do not trust.
- No secrets in skills, prompts or logs.
