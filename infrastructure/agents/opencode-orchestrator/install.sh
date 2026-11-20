#!/bin/sh
set -eu

src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${1:-"$HOME/.config/opencode"}

mkdir -p "$target/skills" "$target/plugins"

for agent in atlas build forge juror oracle scout shield vouch lead decision-maker voter explorer implementer verifier security; do
  rm -f "$target/agents/$agent.md"
done
rmdir "$target/agents" 2>/dev/null || true

for skill in "$src"/skills/*; do
  [ -d "$skill" ] || continue
  name=$(basename "$skill")
  rm -rf "$target/skills/$name"
  cp -R "$skill" "$target/skills/$name"
  chmod 755 "$target/skills/$name"
  find "$target/skills/$name" -type d -exec chmod 755 {} +
  find "$target/skills/$name" -type f ! -name '*.cjs' -exec chmod 644 {} +
  find "$target/skills/$name" -type f -name '*.cjs' -exec chmod 755 {} +
done

rm -rf "$target/plugins/model-allowlist"
cp -R "$src/plugins/model-allowlist" "$target/plugins/model-allowlist"
chmod 644 "$target/plugins/model-allowlist/index.ts"

if command -v opencode >/dev/null 2>&1; then
  "$src/check-models.sh" || {
    echo "Model check failed; fix the catalog before relying on the picker." >&2
    exit 1
  }
fi

echo "Installed skills and the model-allowlist plugin into: $target"
echo "Custom agents are not installed. OpenCode's built-in agents are used."
