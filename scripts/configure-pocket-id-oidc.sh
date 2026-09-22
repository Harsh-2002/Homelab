#!/bin/sh
set -eu

base_url="${POCKET_ID_URL:-https://auth.l3b.cc.cd}"
key_file="${POCKET_ID_API_KEY_FILE:-$HOME/.config/pocket-id/api-key}"
output_dir="${POCKET_ID_CLIENT_DIR:-$HOME/.config/pocket-id/clients}"

install -d -m 0700 "$output_dir"
api_key="${POCKET_ID_API_KEY:-}"
if test -z "$api_key"; then
  test -s "$key_file"
  api_key="$(cat "$key_file")"
fi

api() {
  method="$1"
  path="$2"
  data="${3:-}"
  if test -n "$data"; then
    curl -fsS -X "$method" -H "X-API-KEY: $api_key" -H 'Content-Type: application/json' -d "$data" "$base_url/api$path"
  else
    curl -fsS -X "$method" -H "X-API-KEY: $api_key" "$base_url/api$path"
  fi
}

user_id="$(api GET '/users' | jq -r '.data[] | select(.isAdmin == true and .disabled == false) | .id' | head -n1)"
test -n "$user_id"

groups="$(api GET '/user-groups')"
group_id="$(printf '%s' "$groups" | jq -r '.data[] | select(.name == "infrastructure-admins") | .id' | head -n1)"
if test -z "$group_id"; then
  group_id="$(api POST '/user-groups' '{"friendlyName":"infrastructure-admins","name":"infrastructure-admins"}' | jq -r '.id')"
fi
api PUT "/user-groups/$group_id" '{"friendlyName":"infrastructure-admins","name":"infrastructure-admins","customClaims":[]}' >/dev/null
api PUT "/user-groups/$group_id/users" "$(jq -cn --arg id "$user_id" '{userIds:[$id]}')" >/dev/null

create_client() {
  id="$1"
  name="$2"
  launch_url="$3"
  callbacks="$4"
  logout_callbacks="${5:-}"
  if test -z "$logout_callbacks"; then
    logout_callbacks="$(jq -cn --arg launch "$launch_url" '[$launch]')"
  fi
  existing="$(api GET '/oidc/clients' | jq -r --arg id "$id" '.data[] | select(.id == $id) | .id' | head -n1)"
  created=false
  if test -z "$existing"; then
    payload="$(jq -cn --arg id "$id" --arg name "$name" --arg launch "$launch_url" --argjson callbacks "$callbacks" --argjson logout_callbacks "$logout_callbacks" '{id:$id,name:$name,description:"Homelab single sign-on",callbackURLs:$callbacks,logoutCallbackURLs:$logout_callbacks,isPublic:false,pkceEnabled:false,requiresReauthentication:false,requiresPushedAuthorizationRequests:false,skipConsent:true,credentials:{},launchURL:$launch,isGroupRestricted:true,accessTokenDurationMinutes:15,refreshTokenDurationMinutes:10080}')"
    api POST '/oidc/clients' "$payload" >/dev/null
    created=true
  fi
  api PUT "/oidc/clients/$id/allowed-user-groups" "$(jq -cn --arg gid "$group_id" '{userGroupIds:[$gid]}')" >/dev/null
  secret_file="$output_dir/$id.json"
  if test "$created" = true && ! test -s "$secret_file"; then
    api POST "/oidc/clients/$id/secrets" '{}' >"$secret_file"
    chmod 0600 "$secret_file"
  fi
}

create_client headlamp 'Headlamp' 'https://headlamp.l3b.cc.cd' '["https://headlamp.l3b.cc.cd/oidc-callback"]'
create_client argocd 'Argo CD' 'https://argocd.l3b.cc.cd' '["https://argocd.l3b.cc.cd/auth/callback"]'
create_client proxmox 'Proxmox' 'https://px.l3b.cc.cd' '["https://px.l3b.cc.cd","https://px10.l3b.cc.cd","https://px20.l3b.cc.cd","https://px30.l3b.cc.cd"]'
create_client portainer 'Portainer' 'https://portainer.l3b.cc.cd/' '["https://portainer.l3b.cc.cd/"]'
create_client s3 'RustFS' 'https://rustfs.l3b.cc.cd' '["https://rustfs.l3b.cc.cd/rustfs/admin/v3/oidc/callback/default"]'
create_client tinyauth 'Tinyauth' 'https://login.l3b.cc.cd' '["https://login.l3b.cc.cd/api/oauth/callback/pocketid"]'
create_client beszel 'Beszel' 'https://beszel.l3b.cc.cd' '["https://beszel.l3b.cc.cd/api/oauth2-redirect"]'
create_client immich 'Immich' 'https://photos.l3b.cc.cd' '["https://photos.l3b.cc.cd/auth/login","https://photos.l3b.cc.cd/user-settings","app.immich:///oauth-callback"]' '["https://photos.l3b.cc.cd/api/oauth/backchannel-logout"]'

declared_client_ids='["headlamp","argocd","proxmox","portainer","s3","tinyauth","beszel","immich"]'
existing_client_ids="$(api GET "/user-groups/$group_id" | jq -c '[.allowedOidcClients[].id]')"
client_ids="$(jq -cn --argjson existing "$existing_client_ids" --argjson declared "$declared_client_ids" '$existing + $declared | unique')"
api PUT "/user-groups/$group_id/allowed-oidc-clients" "$(jq -cn --argjson ids "$client_ids" '{oidcClientIds:$ids}')" >/dev/null

printf 'Pocket ID group and OIDC clients configured.\n'
