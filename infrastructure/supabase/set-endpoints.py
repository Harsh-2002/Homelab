#!/usr/bin/env python3
"""On Supabase VM: keep persisted env and canonical vault input consistent."""
from pathlib import Path
import os
import re
import shutil

root = Path('/srv/supabase')
updates = {'SUPABASE_PUBLIC_URL': 'https://sb.l3b.cc.cd', 'API_EXTERNAL_URL': 'https://sb.l3b.cc.cd/auth/v1'}
for name in ('.env', 'homelab.env'):
    path = root / name
    text = path.read_text()
    new = text
    for key, value in updates.items():
        new, count = re.subn(r'^' + key + r'=.*$', key + '=' + value, new, flags=re.M)
        if count != 1:
            raise SystemExit('Expected one URL field per file; refusing unknown layout')
    if new != text:
        backup = root / (name + '.pre-sb-endpoints')
        if not backup.exists():
            shutil.copy2(path, backup)
            os.chmod(backup, 0o600)
        path.write_text(new)
        os.chmod(path, 0o600)
print('Canonical API URLs synchronized without changing credentials')
