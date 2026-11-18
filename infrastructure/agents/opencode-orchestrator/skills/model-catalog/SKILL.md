---
name: model-catalog
description: Approved models for Atlas and its subagents. Load before choosing a model or spawning a subagent.
---

# Model catalog

These are the approved models. Any approved model may be used by Atlas or by any subagent. The defaults are defaults, not restrictions. The catalog was reconciled with the live server on 2026-11-18: 13 models, thinking levels read from `/api/model`.

**Owner decisions, 2026-11-18:** no OpenCode free models, and the only OpenCode Go models are DeepSeek V4.1 Flash 1017, GLM-5.3 and GLM-5.3-Flash. Kimi, MiniMax, Qwen and every other Go model are not offered.

## OpenCode Go models

| Model | Role |
|---|---|
| `opencode-go/deepseek-v4.1-flash` | **DeepSeek V4.1 Flash 1017** (the 17 Oct 2026 update). Default Atlas model; default for every subagent; all-round. Go limit **$100/month** ($200 on Go Plus), about 43,300 requests per 5 hours, the largest allowance on the plan. Token price $0.15 / $0.60, doubled at peak (Mon-Fri 01:00-04:00 and 06:00-10:00 UTC) |
| `opencode-go/glm-5.3` | **GLM-5.3**, the full flagship, for harder long-horizon work. Go limit **$500/month** ($1000 on Go Plus), about 6,600 requests per 5 hours. **That limit is temporary: higher limits apply only through 22 Nov 2026**, and it is normally far lower. Token price $1.40 / $4.40, so it drains the allowance much faster than a Flash model |
| `opencode-go/glm-5.3-flash` | **GLM-5.3-Flash**: alternative implementation, frontend/TypeScript, documentation. Go limit $60/month ($180 on Go Plus), about 6,320 requests per 5 hours. $0.15 / $0.50 |

Go limits are dollar allowances: at most 20% per 5 hours and 50% per week, one allowance shared by all models. When it runs out every `opencode-go/*` call fails (seen on 2026-11-13 for the first account). Two OpenCode Console profiles are saved, so switch with `opencode auth switch "OpenCode Console" <label>`; otherwise use an OpenAI or Claude Agent model until the allowance resets. Extra Usage in the Console falls back to pay-as-you-go credit when enabled.

## OpenAI Codex models

| Model | Role |
|---|---|
| `openai/gpt-6.2-astra` | **Premium escalation only**; newest and strongest OpenAI reasoner, $8 / $40 per 1M tokens |
| `openai/gpt-6.2-sol` | OpenAI Sol; **newest Sol revision**, strong coding model, $2 / $10 |
| `openai/gpt-6-astra` | Older Astra; **premium escalation only**, $10 / $50. Prefer 6.2 Astra |
| `openai/gpt-6.1-sol` | Previous Sol revision; kept so existing sessions and agents keep working |
| `openai/gpt-6.1-terra` | OpenAI Terra; large context |
| `openai/gpt-6-luna` | OpenAI Luna; fast, lower-cost worker |

These are exposed by the connected OpenAI Codex provider. The provider ID is `openai`; there is no separate `openai-codex/*` reference. The server also lists `-fast`, `-flex` and `-ultrafast` tier variants and `*-cyber` models; they are not in the approved set. The dedicated Codex model `openai/gpt-5.3-codex` is also outside it.

## Claude Agent models

| Model | Alias resolves to | Role |
|---|---|---|
| `claude-agent/claude-opus-5-5` | Opus 5.5 | Highest-capability Claude worker; deep reasoning and review |
| `claude-agent/claude-sonnet-5-5` | Sonnet 5.5 | Balanced Claude worker; strong implementation |
| `claude-agent/claude-haiku-5-5` | Haiku 5.5 | Fast, low-cost Claude worker |
| `claude-agent/claude-fable-5-2` | Fable 5.2 | **Premium escalation only**; ~67× DeepSeek output cost |

These are the **original versioned model IDs**, not family aliases. The provider also exposes `opus`, `sonnet`, `haiku` and `fable`, but the allowlist hides those so the picker preserves the real model names and numbers. Update them when Anthropic ships a new model version.

Use the **Claude Agent** provider only. The separate `anthropic/*` provider is hard-denied by the global `provider.use` policy and removed from the picker. The stored Anthropic credential was removed on 2026-11-16.

## Premium models — escalation only

`openai/gpt-6.2-astra`, `openai/gpt-6-astra` and `claude-agent/claude-fable-5-2` are the most expensive models in the catalog. Approximate list prices per 1M tokens (OpenCode Console pricing, 2026-11-18):

- **GPT-6.2 Astra:** $8 input / $40 output; $16 / $60 above 272k context.
- **GPT-6 Astra:** $10 input / $50 output; $20 / $75 above 272k context.
- **Fable 5.2:** $8 input / $40 output.
- **For comparison:** DeepSeek V4.1 Flash and GLM-5.3-Flash are $0.15 input / $0.5–0.6 output; GLM-5.3 is $1.40 / $4.40.

Do not use Astra or Fable for routine implementation, documentation, tests, research, or normal verification. Use one only when at least one of these is true:

1. The user explicitly asks for Astra or Fable.
2. A cheaper approved model has already failed or produced insufficient quality on the same task.
3. The task is genuinely exceptional — high-stakes, long-horizon, or the expected value clearly justifies 20–100× the cost.

State the justification in the final answer when you use one. In a decision jury, at most one seat may be Astra or Fable, and only for an exceptional decision; never make the whole jury premium.

## Thinking levels

Every model reference must include a `#variant`. Agent defaults already carry one; when you choose a model for a subagent, pass the variant explicitly. A bare model is normalized to that model's default by the allowlist plugin, including a model picked directly in the session picker. Do not rely on the safety net.

| Family | Variants | Default | Routine work | Complex / review / decision | Exceptional |
|---|---|---|---|---|---|
| DeepSeek V4.1 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| GLM 5.3 | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| GLM 5.3 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| OpenAI Astra/Sol (incl. 6.2) | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| OpenAI Terra/Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| Claude Agent | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |

Go models run at `#max` for all work, matching the owner's preference. Use `#high` on OpenAI/Claude for multi-file implementation, debugging, verification, security review, architecture and decision juries. Use `#xhigh` only for genuinely hard or long-horizon work. Use `#max` on OpenAI/Claude only when the user explicitly asks for maximum effort or the task is exceptional. Do not use `#none` for engineering work.

Examples:

```text
opencode-go/deepseek-v4.1-flash#max
opencode-go/glm-5.3#max
opencode-go/glm-5.3-flash#max
openai/gpt-6.2-sol#medium
openai/gpt-6.2-sol#high
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

Any approved model may be used for any role. For quality, the stronger everyday models are OpenAI Sol (use 6.2) and Terra and Claude Agent Opus and Sonnet. Astra and Fable are premium escalation only. DeepSeek V4.1 Flash and GLM-5.3-Flash are the cheap worker defaults; GLM-5.3 is the stronger Go option for harder work while its higher limit lasts. This is advice, not a permission restriction, except that Astra/Fable need the justification above.

## Decision juries

The `oracle` primary agent uses these models as independent jurors. Use an odd jury size and a different model per juror, spanning at least two families:

- 3 voters: `deepseek-v4.1-flash`, `glm-5.3-flash`, `gpt-6.2-sol`
- 5 voters: add `glm-5.3` and `gpt-6.1-terra`
- 7 voters: add `gpt-6-luna` and `claude-agent/claude-sonnet-5-5`
- Claude Agent versioned models can replace OpenAI jurors when that provider is authenticated.

Do not reuse a model in the same jury, and do not reveal earlier votes to later jurors. Astra and Fable are **not** default jury seats; use at most one premium seat, only for an exceptional decision or an explicit user request, and state why.

## Exclusions

OpenCode free models (owner decision, 2026-11-18: they are blocked on both Console accounts by the training-data privacy setting and are not wanted), **Kimi and MiniMax (removed at the owner's request, 2026-11-18)**, Qwen4 Max and every other OpenCode Go model, DeepSeek V4 Pro, GPT-5 and older model families, the older versioned Claude Agent IDs, every OpenCode Console pay-as-you-go model outside the lists above, the `-fast`, `-flex` and `-ultrafast` tier variants, and **all `anthropic/*` models** are excluded. Only the 13 models above are shown.
