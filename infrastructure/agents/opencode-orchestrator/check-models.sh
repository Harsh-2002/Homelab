#!/bin/sh
set -eu

# Models the agents depend on. A missing one fails the check.
required="
opencode-go/deepseek-v4.1-flash
opencode-go/glm-5.3-flash
opencode-go/minimax-m3.1-flash
opencode-go/qwen4-max
openai/gpt-6.2-astra
openai/gpt-6.2-sol
openai/gpt-6-astra
openai/gpt-6.1-sol
openai/gpt-6.1-terra
openai/gpt-6-luna
claude-agent/claude-opus-5-5
claude-agent/claude-sonnet-5-5
claude-agent/claude-haiku-5-5
claude-agent/claude-fable-5-2
"

# OpenCode free models are limited-time and rotate, so a missing one only warns.
# Update plugins/model-allowlist/index.ts and skills/model-catalog/SKILL.md when
# OpenCode adds or retires one (see the free-models and deprecated-models lists in
# https://opencode.ai/docs/zen).
optional="
opencode/glm-5.3-flash-free
opencode/deepseek-v4.1-flash-free
opencode/hy4-flash-free
opencode/beam-free
opencode/longcat-2.5-free
opencode/mimo-v2.6-flash-free
opencode/big-pickle
opencode/iceman-free
opencode/inkling-2-small-free
opencode/flint-40b-free
opencode/nemotron-3.5-lightning-free
opencode/nemotron-3.5-super-vl-free
"

available=$(opencode models 2>/dev/null || true)
missing=0
for model in $required; do
  if printf '%s\n' "$available" | grep -Fxq "$model"; then
    echo "available: $model"
  else
    echo "MISSING: $model" >&2
    missing=1
  fi
done

for model in $optional; do
  if printf '%s\n' "$available" | grep -Fxq "$model"; then
    echo "available (free): $model"
  else
    echo "warning: free model not available: $model" >&2
  fi
done

if [ "$missing" -eq 1 ]; then
  echo "One or more approved models are unavailable." >&2
  exit 1
fi

echo "All required models are available."
