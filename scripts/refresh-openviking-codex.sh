#!/bin/sh
set -eu

# Import a fresh dev Codex login without printing or staging credentials.
auth_file=${1:-/home/dev/.codex/auth.json}
target=${OPENVIKING_SSH_TARGET:-ctr}
test -r "$auth_file"
jq -e '.tokens.access_token and .tokens.refresh_token' "$auth_file" >/dev/null
ssh "$target" 'docker exec -i openviking python -c '\''
import json, sys
from openviking.models.vlm.backends.codex_auth import (
    save_codex_tokens, _extract_codex_oauth_client_id,
    CODEX_AUTH_OWNER_EXTERNAL, get_codex_auth_status,
)
payload = json.load(sys.stdin)
tokens = payload["tokens"]
save_codex_tokens(
    tokens["access_token"], tokens["refresh_token"],
    imported_from="/home/dev/.codex/auth.json",
    last_refresh=payload.get("last_refresh"),
    client_id=_extract_codex_oauth_client_id(payload),
    auth_owner=CODEX_AUTH_OWNER_EXTERNAL,
)
status = get_codex_auth_status()
print(json.dumps({k: status.get(k) for k in (
    "provider", "store_exists", "expires_at", "expiring", "auth_owner"
)}))
'\''' < "$auth_file"
