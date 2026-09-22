#!/bin/bash

set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 1; }
case "$(hostname)" in px10|px20|px30) ;; *) echo "Run only on px10, px20, or px30." >&2; exit 1;; esac

read -rsp "Tailscale auth key: " auth_key
printf '\n'
key_file=/run/tailscale-auth-key
trap 'rm -f "$key_file"' EXIT
umask 077
printf '%s' "$auth_key" > "$key_file"
unset auth_key

curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable --now tailscaled
tailscale up \
  --auth-key="file:$key_file" \
  --hostname="$(hostname)" \
  --advertise-routes=10.1.1.0/24 \
  --accept-dns=false \
  --accept-routes=false \
  --snat-subnet-routes=true \
  --netfilter-mode=on \
  --ssh=false \
  --timeout=30s
tailscale set --auto-update=true

echo "Tailscale enrolled. Deploy infrastructure/tailscale files from the repository next."
