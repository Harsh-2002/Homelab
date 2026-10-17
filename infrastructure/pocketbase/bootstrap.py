#!/usr/bin/env python3
"""Create one canonical vault item and deliver bootstrap env over SSH stdin."""
import json
from pathlib import Path
import secrets
import subprocess

op = str(Path(__file__).resolve().parents[2] / "scripts/op-sa")
def vault(*args, data=None):
    result = subprocess.run([op, *args, "--format", "json"], input=data, text=True, capture_output=True)
    if result.returncode:
        raise SystemExit("1Password operation failed; no secret output displayed")
    return json.loads(result.stdout)

TITLE = "PocketBase - VM108"
items = [x for x in vault("item", "list", "--vault", "HomeLab") if x["title"] == TITLE]
if len(items) > 1:
    raise SystemExit("Duplicate PocketBase vault items; refusing to choose")
if items:
    item = vault("item", "get", items[0]["id"], "--vault", "HomeLab")
    fields = {f.get("id"): f.get("value", "") for f in item["fields"]}
    email, password = fields["username"], fields["password"]
else:
    email, password = "iam.anuragvishwakarma@gmail.com", secrets.token_urlsafe(36)
    vault("item", "create", "--vault", "HomeLab", "-", data=json.dumps({
        "title": TITLE, "category": "LOGIN",
        "urls": [{"href": "https://pocketbase.l3b.cc.cd/_/", "primary": True}],
        "fields": [
            {"id": "username", "type": "STRING", "purpose": "USERNAME", "value": email},
            {"id": "password", "type": "CONCEALED", "purpose": "PASSWORD", "value": password},
        ],
    }))
env = f"PB_ADMIN_EMAIL={email}\nPB_ADMIN_PASSWORD={password}\n"
subprocess.run(["ssh", "supabase", "sudo sh -c 'umask 077; test ! -e /srv/pocketbase/.env; install -m 600 /dev/stdin /srv/pocketbase/.env'"], input=env, text=True, check=True)
print("PocketBase bootstrap env installed; credentials saved in HomeLab / PocketBase - VM108")
