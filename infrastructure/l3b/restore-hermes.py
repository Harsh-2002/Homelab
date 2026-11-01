#!/usr/bin/env python3
"""Restore Hermes configuration/persona/skills, not history, cron or process state."""
import argparse
import os
from pathlib import Path
import shutil

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('saved_home', type=Path)
    args = parser.parse_args()
    source = args.saved_home / '.hermes'
    dest = Path('/data/apps/hermes/home')
    if dest.exists():
        raise SystemExit('Hermes destination exists; refusing overwrite')
    dest.mkdir(parents=True, mode=0o700)

    def copy(src, dst):
        if src.is_symlink():
            value = str(src.readlink())
            name = src.name
            if '/.agents/skills/' in value or value.startswith('../../.agents/skills/'):
                dst.symlink_to('/opt/data/shared-skills/' + name)
            elif value.startswith('/home/dev/Homelab/'):
                dst.symlink_to(value.replace('/home/dev/Homelab/', '/workspace/Homelab/'))
            else:
                raise ValueError('Unreviewed Hermes skill symlink: ' + name)
        elif src.is_dir():
            dst.mkdir()
            for child in src.iterdir():
                if child.name.startswith('.') or child.name.endswith(('.lock', '.log')):
                    continue
                copy(child, dst / child.name)
        else:
            shutil.copy2(src, dst)

    for name in ['.env', 'auth.json', 'SOUL.md', 'memories', 'skills', 'plugins', 'openviking']:
        path = source / name
        if path.exists():
            copy(path, dest / name)
    shutil.copytree('/home/dev/.agents/skills', dest / 'shared-skills', symlinks=True)
    # Shared repository skills use the container's actual repository mount.
    for path in (dest / 'shared-skills').iterdir():
        if path.is_symlink() and str(path.readlink()).startswith('/home/dev/Homelab/'):
            value = str(path.readlink()).replace('/home/dev/Homelab/', '/workspace/Homelab/')
            path.unlink()
            path.symlink_to(value)
    config = yaml.safe_load((source / 'config.yaml').read_text())
    for name, entry in config.get('mcp_servers', {}).items():
        entry['enabled'] = name in ['context7', 'shadcn', 'rea']
    config.setdefault('mcp_servers', {})['playwright'] = {
        'url': 'http://playwright:8931/mcp', 'enabled': True}
    plugins = config.setdefault('plugins', {})
    disabled = set(plugins.get('disabled', [])) | set(plugins.get('enabled', []))
    plugins['enabled'] = []
    plugins['disabled'] = sorted(disabled)
    config.setdefault('memory', {}).pop('provider', None)
    config.setdefault('terminal', {})['cwd'] = '/workspace/Homelab'
    config.setdefault('cron', {})['catch_up_missed'] = False
    config.setdefault('gateway', {})['allow_all_users'] = False
    config.setdefault('dashboard', {})['trusted_proxies'] = ['172.17.0.0/16']

    def paths(value):
        if isinstance(value, dict):
            return {key: paths(item) for key, item in value.items()}
        if isinstance(value, list):
            return [paths(item) for item in value]
        if isinstance(value, str):
            return value.replace('/home/dev/.hermes', '/opt/data').replace(
                '/home/dev/.agents/skills', '/opt/data/shared-skills').replace(
                '/home/dev/Homelab', '/workspace/Homelab')
        return value

    config = paths(config)
    (dest / 'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    for path in [dest, *dest.rglob('*')]:
        if not path.is_symlink():
            os.chown(path, 1000, 1000)
    for name in ['config.yaml', '.env', 'auth.json']:
        if (dest / name).is_file():
            (dest / name).chmod(0o600)
    os.chown(dest.parent, 1000, 1000)
    print('Hermes config, credentials, persona and skills restored privately.')
    print('No history/cron copied; messaging gateway and unavailable plugins remain disabled.')


if __name__ == '__main__':
    main()
