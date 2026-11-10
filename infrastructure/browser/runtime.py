"""Local browser lifecycle; no network listener or Docker socket."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ENDPOINT = 'http://127.0.0.1:9222'


def health():
    for port in (9222, 9223):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=3) as response:
            json.load(response)


def chrome(name, port):
    profile = Path('/state/profiles') / name
    profile.mkdir(parents=True, exist_ok=True)
    # This named container is the sole owner; links from a previous container
    # refer to its retired hostname/PIDs and must not prevent recreation.
    for filename in ('SingletonLock', 'SingletonCookie', 'SingletonSocket'):
        (profile / filename).unlink(missing_ok=True)
    return subprocess.Popen([
        '/usr/bin/chromium', '--headless=new', '--no-sandbox',
        '--disable-dev-shm-usage', '--disable-gpu', '--no-first-run',
        '--no-default-browser-check', '--remote-debugging-address=127.0.0.1',
        '--remote-debugging-port=' + str(port), '--user-data-dir=' + str(profile),
        'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def serve():
    processes = [chrome('opencode', 9222), chrome('hermes', 9223)]
    while all(p.poll() is None for p in processes):
        time.sleep(1)
    for process in processes:
        process.terminate()
    raise SystemExit(1)


if __name__ == '__main__':
    if sys.argv[1] == 'serve':
        serve()
    elif sys.argv[1] == 'health':
        health()
    else:
        raise SystemExit('Expected serve or health')
