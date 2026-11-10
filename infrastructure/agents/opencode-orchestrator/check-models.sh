#!/bin/sh
set -eu

allowed="
opencode-go/deepseek-v4.1-flash
opencode-go/glm-5.3-flash
opencode-go/minimax-m3.1-flash
openai/gpt-6-astra
openai/gpt-6.1-sol
openai/gpt-6.1-terra
openai/gpt-6-luna
claude-agent/claude-opus-5
claude-agent/claude-sonnet-5
claude-agent/claude-haiku-4-5-20251001
"

available=$(opencode models 2>/dev/null || true)
missing=0
for model in $allowed; do
  if printf '%s\n' "$available" | grep -Fxq "$model"; then
    echo "available: $model"
  else
    echo "MISSING: $model" >&2
    missing=1
  fi
done

if [ "$missing" -eq 1 ]; then
  echo "One or more approved models are unavailable." >&2
  exit 1
fi

echo "All approved models are available."
