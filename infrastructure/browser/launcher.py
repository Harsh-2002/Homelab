#!/usr/bin/env python3
"""Invoke the shared Docker tooling without exposing browser ports or secrets."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys

agent = 'hermes' if Path(sys.argv[0]).name.endswith('-hermes') else 'opencode'
args = sys.argv[1:]
if args[:1] == ['--agent']:
    if len(args) < 2 or args[1] not in ('opencode', 'hermes'):
        raise SystemExit('Use --agent opencode or --agent hermes')
    agent, args = args[1], args[2:]
port = 9223 if agent == 'hermes' else 9222
state = Path('/data/apps/browser')
with (state / (agent + '.lock')).open('a') as lock:
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('This agent browser is busy; wait for its current command.')
    command = ['docker', 'exec', '-i', '-e', 'BU_NAME=' + agent,
               '-e', f'BU_CDP_URL=http://127.0.0.1:{port}', 'browser']
    if args[:1] == ['task']:
        command += ['python', '/opt/browser/task.py', *args[1:]]
    else:
        command += ['browser-use', *args]
    raise SystemExit(subprocess.call(command))
