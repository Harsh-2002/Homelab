#!/usr/bin/env python3
"""Merge selected OpenCode skills/MCPs without restoring other agent configs."""
import argparse
import json
import os
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('saved_home', type=Path)
    args = parser.parse_args()
    source = args.saved_home
    home = Path('/home/dev')
    target = home / '.config/opencode'
    config = target / 'opencode.json'
    if config.exists():
        raise SystemExit('OpenCode config exists; refusing to overwrite concurrent work')

    def copy_missing(src, dst):
        if dst.exists() or dst.is_symlink():
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            link = os.readlink(src)
            if link.startswith('/home/dev/Homelab/'):
                dst.symlink_to(link)
                return
            resolved = Path(os.path.normpath(str(src.parent / link))) if not link.startswith('/') else source / link.removeprefix('/home/dev/')
            if not resolved.is_relative_to(source):
                raise ValueError('Skill symlink escapes saved home')
            copy_missing(resolved, dst)
        elif src.is_dir():
            dst.mkdir()
            for child in src.iterdir():
                copy_missing(child, dst / child.name)
        else:
            shutil.copy2(src, dst)
        if not dst.is_symlink():
            os.chown(dst, 1000, 1000)

    for src in (source / '.agents/skills').iterdir():
        copy_missing(src, home / '.agents/skills' / src.name)
    for src in (source / '.claude/skills').iterdir():
        # Import only reusable skills, never Claude configuration/authentication.
        copy_missing(src, home / '.agents/skills' / src.name)
    for sub in ['agents', 'commands', 'skills']:
        root = source / '.config/opencode' / sub
        if root.is_dir():
            for src in root.iterdir():
                copy_missing(src, target / sub / src.name)
    saved = json.loads((source / '.config/opencode/opencode.json').read_text())
    servers = saved.get('mcp', {}).get('servers', {})
    for name, entry in servers.items():
        entry['disabled'] = name not in ['context7', 'shadcn', 'rea']
    servers['playwright'] = {
        'type': 'local', 'command': ['docker', 'exec', '-i', 'playwright', 'node',
            '/app/cli.js', '--cdp-endpoint', 'http://127.0.0.1:9222',
            '--shared-browser-context', '--caps', 'devtools,pdf,vision'],
        'disabled': False, 'timeout': {'startup': 60000, 'catalog': 30000}}
    restored = {
        '$schema': 'https://opencode.ai/config.json',
        'mcp': {'servers': servers},
        'skills': [str(home / '.agents/skills')],
    }
    # OpenViking stays unregistered until its backend is restored. Current native
    # Herdr plugins, CLI preferences, service settings and auth stores are untouched.
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(restored, stream, indent=2)
        stream.write('\n')
    os.chown(config, 1000, 1000)
    for parent in [home / '.agents', home / '.agents/skills']:
        os.chown(parent, 1000, 1000)
    print('Reusable skills restored; OpenCode MCP config merged without credential output.')
    print('Enabled: playwright, context7, shadcn, rea. Others retained disabled.')


if __name__ == '__main__':
    main()
