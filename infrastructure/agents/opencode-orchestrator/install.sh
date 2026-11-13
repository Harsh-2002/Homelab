#!/bin/sh
set -eu

src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${1:-"$HOME/.config/opencode"}

mkdir -p "$target/agents" "$target/skills" "$target/plugins"

# Remove obsolete agent names from earlier installs. Build stays as the
# compatibility profile for sessions created before the Atlas rename.
rm -f "$target/agents/lead.md" \
      "$target/agents/decision-maker.md" \
      "$target/agents/voter.md" \
      "$target/agents/explorer.md" \
      "$target/agents/implementer.md" \
      "$target/agents/verifier.md" \
      "$target/agents/security.md"

install -m 644 "$src"/agents/*.md "$target/agents/"

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
    echo "Model check failed; fix the catalog before using the agents." >&2
    exit 1
  }
fi

echo "Installed agents, skills and model-allowlist plugin into: $target"
echo "Ensure \"default_agent\": \"atlas\" is set in the corresponding opencode.json, then reload."
