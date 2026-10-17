#!/usr/bin/env python3
"""Save a protected dotenv stream in the canonical service vault item."""
import json
from pathlib import Path
import shlex
import subprocess
import sys

op = Path(__file__).resolve().parents[2] / "scripts/op-sa"
contents = sys.stdin.read()
values = {}
for line in contents.splitlines():
    if line and not line.startswith("#") and "=" in line:
        key, value = line.split("=", 1)
        values[key] = shlex.split(value)[0] if value else ""
if not values.get("DASHBOARD_PASSWORD") or not values.get("JWT_SECRET"):
    raise SystemExit("Missing required secrets; refusing vault write")
existing = subprocess.run([str(op), "item", "list", "--vault", "HomeLab", "--format", "json"], check=True, capture_output=True, text=True)
items = [item for item in json.loads(existing.stdout) if item["title"] == "Supabase"]
if len(items) > 1:
    raise SystemExit("Duplicate Supabase vault items require review")
item = {
    "title": "Supabase", "category": "LOGIN",
    "urls": [{"href": "https://supabase.l3b.cc.cd", "primary": True}],
    "fields": [
        {"id": "username", "type": "STRING", "purpose": "USERNAME", "value": "supabase"},
        {"id": "password", "type": "CONCEALED", "purpose": "PASSWORD", "value": values["DASHBOARD_PASSWORD"]},
        {"id": "deployment-env", "label": "deployment-env", "type": "CONCEALED", "value": contents},
        {"id": "publishable-key", "label": "publishable-key", "type": "CONCEALED", "value": values["SUPABASE_PUBLISHABLE_KEY"]},
        {"id": "secret-key", "label": "secret-key", "type": "CONCEALED", "value": values["SUPABASE_SECRET_KEY"]},
    ],
}
command = [str(op), "item", "edit", items[0]["id"]] if items else [str(op), "item", "create", "--vault", "HomeLab"]
result = subprocess.run(command + ["--format", "json", "-"], input=json.dumps(item), text=True, capture_output=True)
if result.returncode:
    raise SystemExit("Vault write failed; inspect safely without printing secret input")
saved = json.loads(result.stdout)
print("Saved canonical HomeLab vault item:", saved["title"], saved["id"])
