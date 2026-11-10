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

## OpenAI models

| Model | Role |
|---|---|
| `openai/gpt-6-astra` | OpenAI Astra |
| `openai/gpt-6.1-sol` | OpenAI Sol |
| `openai/gpt-6.1-terra` | OpenAI Terra |
| `openai/gpt-6-luna` | OpenAI Luna |

These are the models exposed by the connected OpenAI Codex provider. The OpenAI provider ID is `openai`; there is no separate `openai-codex/*` model reference in this catalog.

## Claude Agent models

| Model | Role |
|---|---|
| `claude-agent/claude-opus-5` | Claude Agent Opus |
| `claude-agent/claude-sonnet-5` | Claude Agent Sonnet |
| `claude-agent/claude-haiku-4-5-20251001` | Claude Agent Haiku |

Use the **Claude Agent** provider only. The separate `anthropic/*` provider is not enabled or allowed; it is a different provider and is removed from the picker.

## Defaults

- Atlas default: `opencode-go/deepseek-v4.1-flash`.
- Subagent default: `opencode-go/deepseek-v4.1-flash`.
- If you select a different approved model in the model picker, Atlas uses it for that session.
- If Atlas passes a model to a subagent, that model is used.
- If no model is passed to a subagent, its configured default applies.
- If an unapproved model is passed, the allowlist plugin falls back to DeepSeek V4.1 Flash.

## Guidance

Any approved model may be used for any role. For quality, the stronger reasoning models are OpenAI Sol/Astra/Terra and Claude Agent Opus/Sonnet. The Chinese flash models are the cheaper worker defaults. This is advice, not a permission restriction.

## Exclusions

DeepSeek V4 Pro, Kimi, GPT-5 and older model families, and **all `anthropic/*` models** are excluded. Only the ten models above are shown.
