#!/usr/bin/env python3
"""Initialize non-default site/SMTP inputs without printing credentials."""
import json
import os
from pathlib import Path
import re
import sys

directory = Path(sys.argv[1])
smtp = json.loads(Path(sys.argv[2]).read_text())
fields = {name: f.get("value", "") for f in smtp["fields"] for name in (f.get("id"), f.get("label")) if name}
if not fields.get("username") or not fields.get("app-password"):
    raise SystemExit("SMTP vault item is missing required fields")
updates = {
    "SMTP_HOST": "smtp.gmail.com", "SMTP_PORT": "587",
    "SMTP_USER": fields["username"], "SMTP_PASS": fields["app-password"],
    "SMTP_ADMIN_EMAIL": fields["username"], "SMTP_SENDER_NAME": "Homelab Supabase",
    "POOLER_TENANT_ID": "homelab-supabase",
    "STUDIO_DEFAULT_ORGANIZATION": "Homelab",
    "STUDIO_DEFAULT_PROJECT": "Supabase",
    "DASHBOARD_USERNAME": "supabase",
    "OPENAI_API_KEY": "",
}
path = directory / ".env"
lines = path.read_text().splitlines()
for index, line in enumerate(lines):
    match = re.match(r"^([A-Z][A-Z_0-9]*)=", line)
    if match and match.group(1) in updates:
        key = match.group(1)
        value = updates.pop(key)
        # Dotenv single quotes prevent interpolation of passwords containing '$'.
        if "\n" in value or "'" in value:
            raise SystemExit("Unsupported multiline/quoted SMTP field; review safely")
        lines[index] = f"{key}='{value}'"
if updates:
    raise SystemExit("Expected upstream environment fields are missing")
path.write_text("\n".join(lines) + "\n")
os.chmod(path, 0o600)
print("Site and SMTP fields configured; no credentials displayed")
