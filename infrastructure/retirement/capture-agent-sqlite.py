#!/usr/bin/env python3
"""Back up local coding-agent SQLite state without stopping live agents."""
import json
import os
from pathlib import Path
import sqlite3
import sys

os.umask(0o077)
home = Path.home()
destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True, mode=0o700)
roots = [home / name for name in [
    '.codex', '.hermes', '.claude', '.config/opencode', '.local/share/opencode'
]]
sources = set()
for root in roots:
    if not root.is_dir():
        continue
    for directory, directories, files in os.walk(root):
        depth = len(Path(directory).relative_to(root).parts)
        directories[:] = [] if depth >= 3 else [
            d for d in directories
            if d not in {'cache', 'plugins', 'node_modules', 'attachments', 'sessions', 'skills'}
        ]
        for name in files:
            source = Path(directory) / name
            if source.suffix in {'.db', '.sqlite', '.sqlite3'}:
                with source.open('rb') as f:
                    if f.read(16) == b'SQLite format 3\x00':
                        sources.add(source)

manifest = []
for source in sorted(sources):
    target = destination / source.relative_to(home).as_posix().replace('/', '__')
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=20) as live:
        with sqlite3.connect(target) as backup:
            live.backup(backup, pages=256, sleep=0.05)
            assert backup.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    manifest.append({
        'source': str(source), 'copy': target.name,
        'integrity': 'ok', 'bytes': target.stat().st_size,
    })
(destination / 'restore-map.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Consistent agent SQLite backups verified: {len(manifest)}')
