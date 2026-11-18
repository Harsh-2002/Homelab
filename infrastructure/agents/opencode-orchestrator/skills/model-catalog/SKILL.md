---
name: model-catalog
description: Approved models for Atlas and its subagents. Load before choosing a model or spawning a subagent.
---

# Model catalog

These are the approved models. Any approved model may be used by Atlas or by any subagent. The defaults are defaults, not restrictions. The catalog was last reconciled with the live server on 2026-11-18: 26 models, thinking levels read from `/api/model`.

## Chinese models (OpenCode Go plan)

| Model | Role |
|---|---|
| `opencode-go/deepseek-v4.1-flash` | Default Atlas model; default for every subagent; all-round |
| `opencode-go/glm-5.3-flash` | Alternative implementation, frontend/TypeScript, documentation |
| `opencode-go/minimax-m3.1-flash` | Alternative UI/frontend, independent checks, high-volume work |
| `opencode-go/qwen4-max` | Newest Qwen; large context (1M); $1.50 / $4.50 per 1M tokens; top level is `xhigh` |

The Go plan has a monthly usage limit. When it is exhausted every `opencode-go/*` call fails (seen on 2026-11-13, resets about 12 days later). Use a zero-retention free model (class A below) or an OpenAI/Claude Agent model until it resets.

## OpenAI Codex models

| Model | Role |
|---|---|
| `openai/gpt-6.2-astra` | **Premium escalation only**; newest and strongest OpenAI reasoner, $8 / $40 per 1M tokens |
| `openai/gpt-6.2-sol` | OpenAI Sol; **newest Sol revision**, strong coding model, $2 / $10 |
| `openai/gpt-6-astra` | Older Astra; **premium escalation only**, $10 / $50. Prefer 6.2 Astra |
| `openai/gpt-6.1-sol` | Previous Sol revision; kept so existing sessions and agents keep working |
| `openai/gpt-6.1-terra` | OpenAI Terra; large context |
| `openai/gpt-6-luna` | OpenAI Luna; fast, lower-cost worker |

These are exposed by the connected OpenAI Codex provider. The provider ID is `openai`; there is no separate `openai-codex/*` reference. The server also lists `-fast`, `-flex` and `-ultrafast` tier variants of these models and `*-cyber` models; they are not in the approved set. The latest dedicated Codex model (`openai/gpt-5.3-codex`) is also outside it.

## Claude Agent models

| Model | Alias resolves to | Role |
|---|---|---|
| `claude-agent/claude-opus-5-5` | Opus 5.5 | Highest-capability Claude worker; deep reasoning and review |
| `claude-agent/claude-sonnet-5-5` | Sonnet 5.5 | Balanced Claude worker; strong implementation |
| `claude-agent/claude-haiku-5-5` | Haiku 5.5 | Fast, low-cost Claude worker |
| `claude-agent/claude-fable-5-2` | Fable 5.2 | **Premium escalation only**; ~67× DeepSeek output cost |

These are the **original versioned model IDs**, not family aliases. The provider also exposes `opus`, `sonnet`, `haiku` and `fable`, but the allowlist hides those so the picker preserves the real model names and numbers. Update them when Anthropic ships a new model version.

Use the **Claude Agent** provider only. The separate `anthropic/*` provider is hard-denied by the global `provider.use` policy and removed from the picker; it is a different provider. The stored Anthropic credential was removed on 2026-11-16.

## OpenCode free models (provider `opencode`)

Twelve free models need no credits. They are **limited-time and rotate**: OpenCode adds and retires them (for example MiniMax M3.1 Flash Free was deprecated on 2026-11-17). `check-models.sh` only warns when one disappears. Re-read https://opencode.ai/docs/zen (Free models, Privacy, Deprecated) when updating.

**Status on 2026-11-18: every free model is blocked on this account.** A real request to `opencode/deepseek-v4.1-flash-free`, `opencode/big-pickle` and `opencode/hy4-flash-free` all failed with "Free models may train on request data. Turn on 'Allow free endpoints that train on request data' ...". The OpenCode Console privacy setting is off, and it gates the free models as a group, including those documented as zero-retention. The owner has not switched it on, so do not select a free model or route work to one until the owner says it is enabled. The other 14 models work (`openai/gpt-6.2-sol` tested).

They are free but **not equal on privacy**. Before sending work to one, pick by class:

| Class | Models | What the provider does with your data | Use for |
|---|---|---|---|
| **A: zero retention, no training** | `opencode/glm-5.3-flash-free`, `opencode/deepseek-v4.1-flash-free`, `opencode/hy4-flash-free` | Not retained, not used for training | Ordinary homelab and repository work, and the fallback when the Go plan is exhausted. Never send secrets to any model |
| **B: no training, but a limit** | `opencode/beam-free` (retained 30 days), `opencode/longcat-2.5-free` (hosted in China, 100 requests per day) | Not used for training | Public or non-sensitive work only |
| **C: retained or used to improve the model** | `opencode/big-pickle`, `opencode/iceman-free`, `opencode/inkling-2-small-free`, `opencode/flint-40b-free`, `opencode/nemotron-3.5-lightning-free`, `opencode/nemotron-3.5-super-vl-free`, `opencode/mimo-v2.6-flash-free` | Logged, retained or used for improvement or training (the NVIDIA and Flint terms say trial use only, no confidential data; MiMo's terms only say feedback is collected) | Public documentation, throwaway code, formatting. **Never** homelab configuration, credentials, personal data or private repository content |

Rules:

1. Free models never receive credentials, tokens, private keys, `.env` content, customer or personal data, or private homelab configuration, whatever the class.
2. Class C models are for public or disposable material only.
3. Free models are not a substitute for Sol, Opus or Sonnet on hard engineering or security work. No quality benchmark was run; do not assume one.
4. State in the final answer when a free model did part of the work.

## Premium models — escalation only

`openai/gpt-6.2-astra`, `openai/gpt-6-astra` and `claude-agent/claude-fable-5-2` are the most expensive models in the catalog. Approximate list prices per 1M tokens (OpenCode Console pricing, 2026-11-18):

- **GPT-6.2 Astra:** $8 input / $40 output; $16 / $60 above 272k context.
- **GPT-6 Astra:** $10 input / $50 output; $20 / $75 above 272k context.
- **Fable 5.2:** $8 input / $40 output.
- **For comparison:** DeepSeek, GLM and MiniMax flash models are about $0.15–0.30 input / $0.5–1.2 output; free models cost nothing.

Do not use Astra or Fable for routine implementation, documentation, tests, research, or normal verification. Use one only when at least one of these is true:

1. The user explicitly asks for Astra or Fable.
2. A cheaper approved model has already failed or produced insufficient quality on the same task.
3. The task is genuinely exceptional — high-stakes, long-horizon, or the expected value clearly justifies 20–100× the cost.

State the justification in the final answer when you use one. In a decision jury, at most one seat may be Astra or Fable, and only for an exceptional decision; never make the whole jury premium.

## Thinking levels

Every model that has thinking levels must be referenced with a `#variant`. Agent defaults already carry one; when you choose a model for a subagent, pass the variant explicitly. A bare model is normalized to that model's default by the allowlist plugin, including a model picked directly in the session picker. Do not rely on the safety net. Models with **no** levels take no `#variant` (the plugin leaves them bare).

| Family | Variants | Default | Routine work | Complex / review / decision | Exceptional |
|---|---|---|---|---|---|
| DeepSeek V4.1 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| GLM 5.3 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| MiniMax 3.1 Flash | `low`, `medium`, `high`, `xhigh`, `max` | `max` | `max` | `max` | `max` |
| Qwen4 Max | `none`, `low`, `high`, `xhigh` | `xhigh` | `xhigh` | `xhigh` | `xhigh` |
| OpenAI Astra/Sol (incl. 6.2) | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| OpenAI Terra/Luna | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| Claude Agent | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `medium` | `high` | `xhigh` or `max` |
| Free: GLM 5.3 Flash, DeepSeek V4.1 Flash | `low`, `high`, `max` | `max` | `max` | `max` | `max` |
| Free: Beam, Flint 40B | `low`, `medium`, `high`, `xhigh`, `max` | `max` | `max` | `max` | `max` |
| Free: Hy4 Flash | `none`, `high` | `high` | `high` | `high` | `high` |
| Free: Inkling 2 Small | `none`, `minimal`, `low`, `medium`, `high`, `max` | `max` | `max` | `max` | `max` |
| Free: Nemotron 3.5 Super VL | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` | `xhigh` | `xhigh` | `xhigh` | `xhigh` |
| Free, no levels: Big Pickle, Iceman, LongCat 2.5, MiMo V2.6 Flash, Nemotron 3.5 Lightning | none | none | none | none | none |

Chinese and free models run at their highest level for all work, matching the owner's preference; they cost nothing extra. Use `#high` on OpenAI/Claude for multi-file implementation, debugging, verification, security review, architecture and decision juries. Use `#xhigh` only for genuinely hard or long-horizon work. Use `#max` on OpenAI/Claude only when the user explicitly asks for maximum effort or the task is exceptional. Do not use `#none` for engineering work.

Examples:

```text
opencode-go/deepseek-v4.1-flash#max
opencode-go/qwen4-max#xhigh
openai/gpt-6.2-sol#medium
openai/gpt-6.2-sol#high
claude-agent/claude-opus-5-5#high
opencode/deepseek-v4.1-flash-free#max
opencode/big-pickle
```

## Defaults

- Atlas default: `opencode-go/deepseek-v4.1-flash`.
- Subagent default: `opencode-go/deepseek-v4.1-flash`.
- If you select a different approved model in the model picker, Atlas uses it for that session.
- If Atlas passes a model to a subagent, that model is used.
- If no model is passed to a subagent, its configured default applies.
- If a bare approved model is passed, the allowlist plugin adds that model's default variant (none for models without levels).
- If an invalid variant is passed, the allowlist plugin uses that model's default variant.
- If an unapproved model is passed, the allowlist plugin falls back to `opencode-go/deepseek-v4.1-flash#max`.

## Guidance

Any approved model may be used for any role. For quality, the stronger everyday models are OpenAI Sol (use 6.2) and Terra and Claude Agent Opus and Sonnet. Astra and Fable are premium escalation only. The Chinese flash models are the cheaper worker defaults, and the class A free models cost nothing. This is advice, not a permission restriction, except that Astra/Fable need the justification above and the free-model rules above apply.

## Decision juries

The `oracle` primary agent uses these models as independent jurors. Use an odd jury size and a different model per juror, spanning at least two families:

- 3 voters: `deepseek-v4.1-flash`, `glm-5.3-flash`, `gpt-6.2-sol`
- 5 voters: add `minimax-m3.1-flash` and `gpt-6.1-terra`
- 7 voters: add `gpt-6-luna` and `claude-agent/claude-sonnet-5-5`
- Claude Agent versioned models can replace OpenAI jurors when that provider is authenticated.
- Free models are not jury seats: their availability and quality are not stable enough for an independent vote.

Do not reuse a model in the same jury, and do not reveal earlier votes to later jurors. Astra and Fable are **not** default jury seats; use at most one premium seat, only for an exceptional decision or an explicit user request, and state why.

## Exclusions

DeepSeek V4 Pro, Kimi, GPT-5 and older model families, the older versioned Claude Agent IDs, every other OpenCode Console paid model (Gemini, Grok, Muse, Mistral and the rest), the `-fast`, `-flex` and `-ultrafast` tier variants, and **all `anthropic/*` models** are excluded. Only the 26 models above are shown.
