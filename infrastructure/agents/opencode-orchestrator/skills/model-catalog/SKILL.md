---
name: model-catalog
description: Approved models for Atlas and its subagents. Load before choosing a model or spawning a subagent.
---

# Model catalog

These are the approved models. Any approved model may be used by Atlas or by any subagent. The defaults are defaults, not restrictions.

## Chinese models

| Model | Role |
|---|---|
| `opencode-go/deepseek-v4.1-flash` | Default Atlas model; default for every subagent; all-round |
| `opencode-go/glm-5.3-flash` | Alternative implementation, frontend/TypeScript, documentation |
| `opencode-go/minimax-m3.1-flash` | Alternative UI/frontend, independent checks, high-volume work |

## OpenAI Codex models

| Model | Role |
|---|---|
| `openai/gpt-6-astra` | OpenAI Astra; strongest general reasoner in the current OpenAI set |
| `openai/gpt-6.1-sol` | OpenAI Sol; newest Sol revision and a strong coding model |
| `openai/gpt-6.1-terra` | OpenAI Terra; newest Terra revision, large context |
| `openai/gpt-6-luna` | OpenAI Luna; fast, lower-cost worker |

These are exposed by the connected OpenAI Codex provider. The provider ID is `openai`; there is no separate `openai-codex/*` model reference in this catalog. The latest dedicated Codex model (`openai/gpt-5.3-codex`) remains outside the approved set so the picker stays focused on the models the owner named.

## Claude Agent models

| Model | Alias resolves to | Role |
|---|---|---|
| `claude-agent/opus` | Opus 5.5 (`claude-opus-5-5`) | Highest-capability Claude worker; deep reasoning and review |
| `claude-agent/sonnet` | Sonnet 5.5 (`claude-sonnet-5-5`) | Balanced Claude worker; strong implementation |
| `claude-agent/haiku` | Haiku 5.5 (`claude-haiku-5-5`) | Fast, low-cost Claude worker |
| `claude-agent/fable` | Fable 5.2 (`claude-fable-5-2`) | Fable family; current latest |

These are deliberate aliases, not versioned IDs. Claude Code resolves them to the latest model in each family (verified against Claude Code `2.1.322`), so the catalog keeps working when Anthropic ships a point release. Do not replace them with the older versioned IDs that OpenCode also lists (`claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001`, `claude-fable-5`).

Use the **Claude Agent** provider only. The separate `anthropic/*` provider is not enabled or allowed; it is a different provider and is removed from the picker.

## Thinking levels

Every model reference must include a `#variant`. Agent defaults already carry one; when you choose a model for a subagent, pass the variant explicitly. A bare model is normalized to that model's default by the allowlist plugin, but do not rely on it.

| Family | Variants | Default | Routine work | Complex / review / decision | Exceptional |
|---|---|---|---|---|---|
| DeepSeek V4.1 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| GLM 5.3 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| MiniMax 3.1 Flash | `low`, `medium`, `high`, `xhigh`, `max` | `max` | `max` | `max` | `max` |
| OpenAI Astra/Sol | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| OpenAI Terra/Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| Claude Agent | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |

Use `#high` for multi-file implementation, debugging, verification, security review, architecture and decision juries. Use `#xhigh` only for genuinely hard or long-horizon work. Use `#max` on OpenAI/Claude only when the user explicitly asks for maximum effort or the task is exceptional. Do not use `#none` for engineering work; it is only for deliberately disabling reasoning on Terra/Luna.

Examples:

```text
opencode-go/deepseek-v4.1-flash#max
opencode-go/glm-5.3-flash#max
openai/gpt-6.1-sol#medium
openai/gpt-6.1-sol#high
claude-agent/opus#high
```

## Defaults

- Atlas default: `opencode-go/deepseek-v4.1-flash`.
- Subagent default: `opencode-go/deepseek-v4.1-flash`.
- If you select a different approved model in the model picker, Atlas uses it for that session.
- If Atlas passes a model to a subagent, that model is used.
- If no model is passed to a subagent, its configured default applies.
- If a bare approved model is passed, the allowlist plugin adds that model's default variant.
- If an invalid variant is passed, the allowlist plugin uses that model's default variant.
- If an unapproved model is passed, the allowlist plugin falls back to `opencode-go/deepseek-v4.1-flash#max`.

## Guidance

Any approved model may be used for any role. For quality, the stronger reasoning models are OpenAI Sol/Astra/Terra and Claude Agent Opus/Sonnet. The Chinese flash models are the cheaper worker defaults. This is advice, not a permission restriction.

## Decision juries

The `decision-maker` primary agent uses these models as independent voters. Use an odd jury size and a different model per voter, spanning at least two families:

- 3 voters: `deepseek-v4.1-flash`, `glm-5.3-flash`, `gpt-6.1-sol`
- 5 voters: add `minimax-m3.1-flash` and `gpt-6-astra`
- 7 voters: add `gpt-6.1-terra` and `gpt-6-luna`
- Claude Agent aliases can replace OpenAI voters when that provider is authenticated.

Do not reuse a model in the same jury, and do not reveal earlier votes to later voters.

## Exclusions

DeepSeek V4 Pro, Kimi, GPT-5 and older model families, the older versioned Claude Agent IDs, and **all `anthropic/*` models** are excluded. Only the eleven models above are shown.
