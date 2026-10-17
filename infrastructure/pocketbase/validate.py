#!/usr/bin/env python3
"""Real authenticated CRUD, backup and recreation persistence acceptance test."""
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import urllib.error
import uuid

base = "https://pocketbase.l3b.cc.cd"
op = str(Path(__file__).resolve().parents[2] / "scripts/op-sa")
items = json.loads(subprocess.run([op, "item", "list", "--vault", "HomeLab", "--format", "json"], capture_output=True, text=True, check=True).stdout)
matches = [item for item in items if item["title"] == "PocketBase - VM108"]
assert len(matches) == 1, "Canonical PocketBase vault item must be unambiguous"
item = json.loads(subprocess.run([op, "item", "get", matches[0]["id"], "--vault", "HomeLab", "--format", "json"], capture_output=True, text=True, check=True).stdout)
fields = {f["id"]: f.get("value", "") for f in item["fields"]}
token = ""
def request(method, path, data=None, expected=200):
    req = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(), method=method,
        headers={"Content-Type": "application/json", **({"Authorization": token} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            assert response.status == expected, response.status
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        if error.code != expected:
            raise RuntimeError(f"{method} {path} returned {error.code}; response withheld") from None

request("GET", "/api/health")
request("GET", "/api/collections", expected=401)
token = request("POST", "/api/collections/_superusers/auth-with-password", {"identity": fields["username"], "password": fields["password"]})["token"]
settings = request("GET", "/api/settings")
assert settings["rateLimits"]["enabled"]
assert settings["backups"]["cron"] == "0 22 * * *"
collection = request("POST", "/api/collections", {"name": "acceptance_" + uuid.uuid4().hex[:10], "type": "base", "fields": [{"name": "message", "type": "text", "required": True}]})
cid = collection["id"]
backup_name = "acceptance-" + uuid.uuid4().hex + ".zip"
try:
    record = request("POST", f"/api/collections/{cid}/records", {"message": "persistent homelab acceptance"})
    old_token, token = token, ""
    request("GET", f"/api/collections/{cid}/records", expected=403)
    token = old_token
    request("POST", "/api/backups", {"name": backup_name}, expected=204)
    subprocess.run(["ssh", "supabase", "sudo docker compose -f /srv/pocketbase/docker-compose.yaml up -d --force-recreate --wait"], check=True, capture_output=True)
    assert request("GET", f"/api/collections/{cid}/records/{record['id']}")["message"] == "persistent homelab acceptance"
    assert any(b["key"] == backup_name for b in request("GET", "/api/backups"))
    print("PASS: health, superuser auth, unauthenticated denial, rate limits, backup, CRUD and persistence after container recreation")
finally:
    request("DELETE", f"/api/collections/{cid}", expected=204)
    request("DELETE", f"/api/backups/{backup_name}", expected=204)
