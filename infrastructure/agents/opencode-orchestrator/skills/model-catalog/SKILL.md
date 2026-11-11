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
| `openai/gpt-6-astra` | **Premium escalation only**; strongest OpenAI reasoner, ~50–100× DeepSeek output cost |
| `openai/gpt-6.1-sol` | OpenAI Sol; newest Sol revision and a strong coding model |
| `openai/gpt-6.1-terra` | OpenAI Terra; newest Terra revision, large context |
| `openai/gpt-6-luna` | OpenAI Luna; fast, lower-cost worker |

These are exposed by the connected OpenAI Codex provider. The provider ID is `openai`; there is no separate `openai-codex/*` model reference in this catalog. The latest dedicated Codex model (`openai/gpt-5.3-codex`) remains outside the approved set so the picker stays focused on the models the owner named.

## Claude Agent models

| Model | Alias resolves to | Role |
|---|---|---|
| `claude-agent/claude-opus-5-5` | Opus 5.5 | Highest-capability Claude worker; deep reasoning and review |
| `claude-agent/claude-sonnet-5-5` | Sonnet 5.5 | Balanced Claude worker; strong implementation |
| `claude-agent/claude-haiku-5-5` | Haiku 5.5 | Fast, low-cost Claude worker |
| `claude-agent/claude-fable-5-2` | Fable 5.2 | **Premium escalation only**; ~67× DeepSeek output cost |

These are the **original versioned model IDs**, not family aliases. The provider also exposes `opus`, `sonnet`, `haiku` and `fable`, but the allowlist hides those so the picker preserves the real model names and numbers. Claude Code `2.1.322` supports all four versioned IDs. Update them when Anthropic ships a new model version.

Use the **Claude Agent** provider only. The separate `anthropic/*` provider is hard-denied by the global `provider.use` policy and removed from the picker; it is a different provider. The stored Anthropic credential is not usable.

## Premium models — escalation only

`openai/gpt-6-astra` and `claude-agent/claude-fable-5-2` are the two most expensive models in the catalog. Approximate list prices per 1M tokens from models.dev:

- **Astra:** $10 input / $50 output; $20 / $75 above 272k context.
- **Fable 5.2:** $8 input / $40 output.
- **For comparison:** DeepSeek, GLM and MiniMax are about $0.15 input / $0.5–0.6 output.

Do not use Astra or Fable for routine implementation, documentation, tests, research, or normal verification. Use one only when at least one of these is true:

1. The user explicitly asks for Astra or Fable.
2. A cheaper approved model has already failed or produced insufficient quality on the same task.
3. The task is genuinely exceptional — high-stakes, long-horizon, or the expected value clearly justifies 20–100× the cost.

State the justification in the final answer when you use either model. In a decision jury, at most one seat may be Astra or Fable, and only for an exceptional decision; never make the whole jury premium.

## Thinking levels

Every model reference must include a `#variant`. Agent defaults already carry one; when you choose a model for a subagent, pass the variant explicitly. A bare model is normalized to that model's default by the allowlist plugin, including a model picked directly in the session picker. Do not rely on the safety net.

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
claude-agent/claude-opus-5-5#high
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

Any approved model may be used for any role. For quality, the stronger everyday models are OpenAI Sol/Terra and Claude Agent Opus/Sonnet. Astra and Fable are premium escalation only. The Chinese flash models are the cheaper worker defaults. This is advice, not a permission restriction, except that Astra/Fable require the justification above.

## Decision juries

The `oracle` primary agent uses these models as independent jurors. Use an odd jury size and a different model per juror, spanning at least two families:

- 3 voters: `deepseek-v4.1-flash`, `glm-5.3-flash`, `gpt-6.1-sol`
- 5 voters: add `minimax-m3.1-flash` and `gpt-6.1-terra`
- 7 voters: add `gpt-6-luna` and `claude-agent/claude-sonnet-5-5`
- Claude Agent versioned models can replace OpenAI jurors when that provider is authenticated.

Do not reuse a model in the same jury, and do not reveal earlier votes to later jurors. Astra and Fable are **not** default jury seats; use at most one premium seat, only for an exceptional decision or an explicit user request, and state why.

## Exclusions

DeepSeek V4 Pro, Kimi, GPT-5 and older model families, the older versioned Claude Agent IDs, and **all `anthropic/*` models** are excluded. Only the eleven models above are shown.
