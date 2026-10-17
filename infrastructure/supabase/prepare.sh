#!/bin/sh
set -eu
umask 077

target=${1:?Usage: sh prepare.sh /absolute/new/deployment/directory}
case "$target" in
    /*) ;;
    *) echo 'Use an absolute destination path.' >&2; exit 1 ;;
esac
if [ -e "$target" ]; then
    echo 'Destination already exists; refusing to overwrite deployment or data.' >&2
    exit 1
fi
base=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
commit=bc27d2661edd09a5d0b8d76ce33da6d4071a756e

mkdir -m 700 -- "$target"
git init -q "$target/.upstream"
git -C "$target/.upstream" remote add origin https://github.com/supabase/supabase.git
git -C "$target/.upstream" sparse-checkout init --cone
git -C "$target/.upstream" sparse-checkout set docker
git -C "$target/.upstream" fetch --depth=1 --filter=blob:none origin "$commit"
git -C "$target/.upstream" checkout -q --detach FETCH_HEAD
test "$(git -C "$target/.upstream" rev-parse HEAD)" = "$commit"
cp -a "$target/.upstream/docker/." "$target/"
mv "$target/docker-compose.yml" "$target/docker-compose.yaml"
# Git checkout inherits the protective umask. Non-secret bind-mounted upstream
# assets must still be readable by unprivileged container users.
find "$target/volumes" -type d -exec chmod 755 {} +
find "$target/volumes" -type f -exec chmod 644 {} +
cp "$base/compose.homelab.yaml" "$target/compose.homelab.yaml"
cp "$base/compose.sh" "$target/compose.sh"
cp "$base/compose.images.yml" "$target/compose.images.yml"
cp "$base/compose.watchtower.yaml" "$target/compose.watchtower.yaml"
cp "$base/compose.auto-update.yaml" "$target/compose.auto-update.yaml"
cp "$base/site.env.example" "$target/site.env.example"
cp "$base/enable-mcp.py" "$target/enable-mcp.py"
chmod 700 "$target/compose.sh"
printf 'ref=self-hosted/v0.8.3\ncommit=%s\n' "$commit" > "$target/.supabase-version"
printf 'Prepared %s from verified commit %s. No secrets generated, images pulled or services started.\n' "$target" "$commit"
