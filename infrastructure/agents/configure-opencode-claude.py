#!/usr/bin/env python3
"""Merge non-secret Claude SDK defaults, preserving protected agent configuration."""
import datetime
import json
import os
from pathlib import Path
import shutil


def main():
    source = Path(__file__).resolve().parent
    config = Path.home() / '.config/opencode/opencode.json'
    current = json.loads(config.read_text())
    packages = [p if isinstance(p, str) else p.get('package', '')
                for p in current.get('plugins', [])]
    if '@openchamber/opencode-claude@1.6.0' not in packages:
        raise SystemExit('Install the reviewed plugin first: opencode plugin add @openchamber/opencode-claude@1.6.0')
    fragment = json.loads((source / 'opencode-claude.fragment.json').read_text())
    preserved = {key: current.get(key) for key in ('mcp', 'plugins', 'skills')}
    current['model'] = fragment['model']
    current['default_agent'] = fragment['default_agent']
    for name, settings in fragment['agents'].items():
        current.setdefault('agents', {}).setdefault(name, {}).update(settings)
    assert all(current.get(key) == value for key, value in preserved.items())
    rendered = json.dumps(current, indent=2) + '\n'
    if config.read_text() != rendered:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup = config.parent / 'backups' / ('claude-sdk-' + stamp)
        backup.mkdir(parents=True, mode=0o700)
        shutil.copy2(config, backup / config.name)
        os.chmod(backup / config.name, 0o600)
        temporary = config.with_name(config.name + '.claude-sdk.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(rendered)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, config)
        finally:
            temporary.unlink(missing_ok=True)
    else:
        os.chmod(config, 0o600)
    target = Path.home() / '.config/systemd/user/opencode.service.d/claude-sdk.conf'
    target.parent.mkdir(parents=True, exist_ok=True)
    desired = (source / 'opencode-claude.conf').read_bytes()
    if not target.exists() or target.read_bytes() != desired:
        if target.exists():
            raise SystemExit('Existing Claude SDK environment differs; review it before replacement')
        target.write_bytes(desired)
        target.chmod(0o644)
    print('Claude SDK defaults match the reviewed fragment; MCPs, skills and plugins preserved.')
    print('Apply a changed service environment with daemon-reload and restart opencode.service.')


if __name__ == '__main__':
    main()
