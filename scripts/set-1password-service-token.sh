#!/bin/bash
set -euo pipefail

token_dir="${XDG_CONFIG_HOME:-$HOME/.config}/op"
token_file="$token_dir/service-account-token"

install -d -m 0700 "$token_dir"
read -r -s -p 'Paste the 1Password service-account token: ' token
printf '\n'
test -n "$token"
install -m 0600 /dev/null "$token_file"
printf '%s' "$token" >"$token_file"
unset token

printf 'Token stored at %s with mode 0600.\n' "$token_file"
