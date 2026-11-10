#!/bin/sh
set -eu

src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${1:-"$HOME/.config/opencode"}

mkdir -p "$target/agents" "$target/skills" "$target/plugins"

# Remove the old agent name from earlier installs.
rm -f "$target/agents/lead.md"

install -m 644 "$src"/agents/*.md "$target/agents/"

for skill in "$src"/skills/*; do
  [ -d "$skill" ] || continue
  name=$(basename "$skill")
  rm -rf "$target/skills/$name"
  cp -R "$skill" "$target/skills/$name"
  chmod 644 "$target/skills/$name/SKILL.md"
done

rm -rf "$target/plugins/model-allowlist"
cp -R "$src/plugins/model-allowlist" "$target/plugins/model-allowlist"
chmod 644 "$target/plugins/model-allowlist/index.ts"

if command -v opencode >/dev/null 2>&1; then
  "$src/check-models.sh" || {
    echo "Model check failed; fix the catalog before using the agents." >&2
    exit 1
  }
fi

echo "Installed agents, skills and model-allowlist plugin into: $target"
echo "Ensure \"default_agent\": \"atlas\" is set in the corresponding opencode.json, then reload."
