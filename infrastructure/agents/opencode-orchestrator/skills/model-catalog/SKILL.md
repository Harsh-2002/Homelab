---
name: model-catalog
description: Approved models for OpenCode sessions and subagents, with thinking levels, tiers and fallbacks. Load before picking a model for a subagent or when a model fails.
---

# Model catalog

These are the approved models, 13 in total, reconciled with the live server on 2026-11-18 (thinking levels read from `/api/model`). The `model-allowlist` plugin hides every other model from the picker.

Owner decisions: no OpenCode free models; the only OpenCode Go models are DeepSeek V4.1 Flash 1017, GLM-5.3 and GLM-5.3-Flash; Kimi, MiniMax, Qwen and every other Go model are not offered. No custom agents are installed. The user decides when a subagent is used and which model it runs.

## Models

| Model | Notes |
|---|---|
| `opencode-go/deepseek-v4.1-flash` | **DeepSeek V4.1 Flash 1017** (17 Oct 2026 update). Go limit $100/month ($200 Go Plus), about 43,300 requests per 5 h. $0.15 / $0.60 per 1M tokens, doubled at peak (Mon-Fri 01-04 and 06-10 UTC). Takes images. Best Go model for coding and agent work in the benchmarks checked |
| `opencode-go/glm-5.3` | **GLM-5.3** flagship, text only. Go limit $500/month ($1000 Go Plus) **only through 22 Nov 2026**, normally far lower. $1.40 / $4.40, so it drains the allowance fast |
| `opencode-go/glm-5.3-flash` | **GLM-5.3-Flash**, $0.15 / $0.50, limit $60/month ($180 Go Plus). Takes images and video |
| `openai/gpt-6.2-sol` | Newest Sol; strong coding model, $2 / $10 |
| `openai/gpt-6.2-astra` | **Premium escalation only**, $8 / $40 |
| `openai/gpt-6-astra` | Older Astra, **premium escalation only**, $10 / $50 |
| `openai/gpt-6.1-sol` | Previous Sol, kept so older sessions keep working |
| `openai/gpt-6.1-terra` | Terra; large context |
| `openai/gpt-6-luna` | Luna; fast, low cost |
| `claude-agent/claude-opus-5-5` | Opus 5.5; deepest Claude reasoning |
| `claude-agent/claude-sonnet-5-5` | Sonnet 5.5; balanced |
| `claude-agent/claude-haiku-5-5` | Haiku 5.5; fast, low cost |
| `claude-agent/claude-fable-5-2` | Fable 5.2, **premium escalation only**, $8 / $40 |

Use the **Claude Agent** provider only. The `anthropic/*` provider is hard-denied and its credential was removed on 2026-11-16. Go limits are dollar allowances shared by all models: at most 20% per 5 hours and 50% per week; when exhausted every `opencode-go/*` call fails.

## Thinking levels

Reference a model as `provider/model#variant`. A bare approved model is normalized to its default variant by the plugin, and an invalid variant also falls back to that model's default.

| Family | Variants | Default |
|---|---|---|
| DeepSeek V4.1 Flash, GLM-5.3, GLM-5.3-Flash | `low`, `high`, `max` | `max` |
| OpenAI Sol and Astra | `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| OpenAI Terra and Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| Claude Agent | `low`, `medium`, `high`, `xhigh`, `max` | `medium` |

Go models run at `#max`. For OpenAI and Claude use `#medium` for routine work, `#high` for multi-file work, debugging and review, `#xhigh` only for genuinely hard work, and `#max` only on request. Do not use `#none`.

## Choosing a model, when asked to

Only choose when the user has not named a model. If they name one, use it.

| Tier | Models | Use for |
|---|---|---|
| 0, low cost | DeepSeek V4.1 Flash 1017, GLM-5.3-Flash, GPT-6 Luna, Haiku 5.5 | Research, reading, docs, simple edits, tests, routine changes |
| 1, strong | GPT-6.2 Sol, Sonnet 5.5, GPT-6.1 Terra | Multi-file features, hard debugging, security review, migrations, verification |
| 2, top | Opus 5.5 | The hardest or highest-stakes work |
| 3, premium | Astra, Fable | Only when the user asks, or a cheaper model already failed the same task |

Start at the cheapest adequate tier, and if quality is the problem go up one tier rather than sideways. Prefer a verifier from a different model family than the implementer. Use GLM-5.3-Flash for video input.

Never use Astra or Fable for routine work, and say so in the answer when one is used.

## When a model fails

For an unavailable model, usage or quota limit, rate limit (429), authentication failure or provider 5xx: retry once if it looks transient, then tell the user which model failed and use the first available replacement below, keeping the same role. A weak result is not a failure; escalate a tier instead. Never fall back to a premium model, a model outside the 13, or a free model. Do not switch OpenCode or OpenAI accounts without the user's say-so.

| Failed | Replacement chain |
|---|---|
| DeepSeek V4.1 Flash | GLM-5.3-Flash, GPT-6 Luna, Haiku 5.5, GPT-6.2 Sol |
| GLM-5.3-Flash | DeepSeek V4.1 Flash, GPT-6 Luna, Haiku 5.5 |
| GLM-5.3 | DeepSeek V4.1 Flash, GLM-5.3-Flash, GPT-6.2 Sol |
| GPT-6.2 Sol | Sonnet 5.5, GPT-6.1 Terra, Opus 5.5 (hard work), DeepSeek V4.1 Flash |
| Sonnet 5.5 | GPT-6.2 Sol, GPT-6.1 Terra, DeepSeek V4.1 Flash |
| GPT-6.1 Terra | GPT-6.2 Sol, Sonnet 5.5, DeepSeek V4.1 Flash |
| Opus 5.5 | GPT-6.2 Sol (`#high` or `#xhigh`), Sonnet 5.5 `#high`, GPT-6.1 Terra `#high` |
| GPT-6 Luna | Haiku 5.5, DeepSeek V4.1 Flash, GLM-5.3-Flash |
| Haiku 5.5 | GPT-6 Luna, DeepSeek V4.1 Flash, GLM-5.3-Flash |
| Astra or Fable | GPT-6.2 Sol `#xhigh` or Opus 5.5 `#xhigh` |

If every `opencode-go/*` call fails the Go allowance is exhausted: two OpenCode Console profiles are saved, but switching them is the owner's call.

A subagent call with an unapproved model is replaced by the plugin with `opencode-go/deepseek-v4.1-flash#max`. A subagent call with no model uses the session's model.
