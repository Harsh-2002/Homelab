#!/usr/bin/env python3
"""Supervise native mdx and compensate for v1.5.1 directory watcher gaps.

mdx ignores unknown newly created filenames and can debounce an atomic-save
rename behind its temporary-file event. Re-touch known changed documents once
after a quiet polling interval; restart only when the filename set changes.
No document contents are parsed or executed.
"""
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path('/data/apps/mdx/docs')
running = True


def stop(*_):
    global running
    running = False


def inventory():
    result = {}
    for path in ROOT.glob('*.md'):
        if path.is_file() and not path.is_symlink():
            s = path.stat()
            result[path.name] = (s.st_ino, s.st_size, s.st_mtime_ns)
    return result


def launch():
    return subprocess.Popen(['/usr/local/bin/mdx', 'serve', str(ROOT),
                             '--host', '10.1.3.1', '--port', '38471'])


def terminate(child):
    child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
previous = inventory()
child = launch()
try:
    while running:
        time.sleep(1)
        if child.poll() is not None:
            raise SystemExit(child.returncode or 1)
        current = inventory()
        if current.keys() != previous.keys():
            terminate(child)
            child = launch()
        else:
            for name, stat in current.items():
                if previous.get(name) != stat:
                    try:
                        os.utime(ROOT / name, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
        previous = inventory()
finally:
    terminate(child)
