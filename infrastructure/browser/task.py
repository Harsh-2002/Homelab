"""Bounded Browser Use delegation using a private, locally configured provider."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

os.umask(0o077)


async def main():
    from browser_use import Agent, Browser
    from openai import AsyncOpenAI
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    task = sys.stdin.read()
    if not task.strip():
        raise SystemExit('Pass the browser task on stdin.')
    config = json.loads(Path('/state/config/model.json').read_text())
    root = Path('/state/tasks')
    root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix='task-', dir=root))
    profile = workspace / 'profile'
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    endpoint = f'http://127.0.0.1:{port}'
    process = subprocess.Popen([
        '/usr/bin/chromium', '--headless=new', '--no-sandbox',
        '--disable-dev-shm-usage', '--no-first-run',
        '--remote-debugging-address=127.0.0.1',
        f'--remote-debugging-port={port}', f'--user-data-dir={profile}',
        'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for attempt in range(50):
            try:
                with urllib.request.urlopen(endpoint + '/json/version', timeout=1):
                    break
            except OSError:
                await asyncio.sleep(0.2)
        else:
            raise RuntimeError('Task browser did not start')
        client = AsyncOpenAI(base_url=config['base_url'], api_key=config['api_key'],
                             default_headers={'x-opencode-session': 'browser-' + workspace.name})
        model = OpenAIChatModel(config['model'], provider=OpenAIProvider(openai_client=client))
        agent = Agent(task, llm=model, browser=Browser(cdp_url=endpoint), workspace=workspace)
        result = await agent.run(max_steps=20, timeout=180)
        output = {'status': str(result.status), 'success': result.is_successful(),
                  'result': result.final_result(), 'workspace': str(workspace)}
        (workspace / 'result.json').write_text(json.dumps(output, indent=2))
        print(json.dumps(output))
        if str(result.status) != 'completed' or result.is_successful() is False:
            raise SystemExit(2)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == '__main__':
    asyncio.run(main())
