#!/usr/bin/env python3
"""Install pinned upstream skills for only the two owner-approved agents.

Pass an existing checkout of the revision in upstream.json. Existing skills are
never overwritten: upgrades require separate review and a private backup.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
lock = json.loads(Path(__file__).with_name('upstream.json').read_text())
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
assert revision == lock['revision'], 'Checkout does not match the pinned skill revision'
targets = [(Path.home()/'.config/opencode/skills', 'browser-use'),
           (Path.home()/'.hermes/skills', 'browser-use-hermes')]
for root, command in targets:
    for name in lock['skills']:
        destination = root/name
        if destination.exists():
            print('Preserved existing skill:', destination)
            continue
        shutil.copytree(source/'skills'/name, destination)
        path = destination/'SKILL.md'
        text = path.read_text()
        boundary = text.find('\n---', 4) + 4
        assert boundary > 4, 'Expected upstream YAML frontmatter'
        adapter = f'''\n\n## l3b managed runtime (takes precedence over generic installation examples)

Routing: explicit user choice wins. Use fetch/APIs for plain reads, Playwright
CLI for deterministic tests and precise UI debugging, Browser Use for interactive
browsing/forms. Use `task` only for self-contained autonomous web work; direct
CLI control does not require another LLM.

Owner-approved Docker deployment. Do not install browser dependencies on the host, start browser MCPs, use cloud browsers, or modify other agents. All host CLI examples use `{command}`; it invokes the pinned container, not host Python. Your browser session/profile is isolated from the other agent. Use `{command} task` with a natural-language task on stdin for autonomous delegation (20 model turns, 180 seconds; existing approved model provider). Never put credentials in task text or print private provider config. Browser data and outputs persist under /data/apps/browser; paths inside the container start /state. Do not start cloud login or auto-install tooling. See /home/dev/Homelab/infrastructure/browser/README.md for operations. Ask before consequential external submission.
'''
        path.write_text(text[:boundary]+adapter+text[boundary:])
        print('Installed scoped skill:', destination)
