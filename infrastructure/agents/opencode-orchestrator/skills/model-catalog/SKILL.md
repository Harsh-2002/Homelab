---
name: model-catalog
description: Approved models for Atlas and its subagents. Load before choosing a model or spawning a subagent.
---

# Model catalog

Only these three models are approved. Do not use DeepSeek V4 Pro, Kimi, GPT, Qwen, GLM-5.3 non-Flash, or any model not listed here.

| Model | Use |
|---|---|
| `opencode-go/deepseek-v4.1-flash` | Default Atlas model; default worker; all-round |
| `opencode-go/glm-5.3-flash` | Alternative for implementation, frontend/TypeScript, documentation |
| `opencode-go/minimax-m3.1-flash` | Alternative for UI/frontend, independent checks, high-volume work |

Atlas runs on `opencode-go/deepseek-v4.1-flash` by default. The user may switch Atlas to GLM 5.3 Flash or MiniMax 3.1 Flash in the model selector.

Subagents default to `opencode-go/deepseek-v4.1-flash`. Atlas may override a subagent call to GLM 5.3 Flash or MiniMax 3.1 Flash when the task fits. There is no escalation model; if a task fails twice, Atlas retries with a different approved model or handles it itself.

## Task policy

This is a starting policy, not a benchmark result. Tune it from `evals/tasks.md`.

| Task | Default | Alternative |
|---|---|---|
| Codebase exploration | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Small/medium implementation | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Multi-file refactor | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Frontend/TypeScript | DeepSeek V4.1 Flash | MiniMax 3.1 Flash, GLM 5.3 Flash |
| Unit/integration tests | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| QA / acceptance | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Failure analysis | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Security first pass | DeepSeek V4.1 Flash | GLM 5.3 Flash |
| Security deep analysis | Atlas model | GLM 5.3 Flash |
| Documentation | GLM 5.3 Flash | MiniMax 3.1 Flash |
| Large-context summarization | GLM 5.3 Flash | MiniMax 3.1 Flash |

## Rules

1. Only the three models above are allowed. Never use DeepSeek V4 Pro, Kimi K3.1 Pro or an unknown model.
2. Use DeepSeek V4.1 Flash unless the task clearly matches GLM or MiniMax.
3. Pass the chosen model in the `subagent` call. If no model is passed, the subagent uses DeepSeek V4.1 Flash.
4. If a subagent fails twice, retry with a different approved model or handle the task in Atlas.
5. Do not run more than 2–4 subagents for normal work.
6. Do not parallelize writes to the same files.
7. Atlas owns the final answer. The subagent's output is evidence, not a conclusion.
