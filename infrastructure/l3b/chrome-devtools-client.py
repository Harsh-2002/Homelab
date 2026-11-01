#!/usr/bin/env python3
"""Attach Hermes DevTools to the existing shared Docker browser, without a socket mount."""
import os
import socket

# Chromium accepts an IP or localhost Host header. Resolve on each launch rather
# than pinning a Docker IP or weakening Chromium's DNS-rebinding protection.
address = socket.gethostbyname('playwright')
os.execvp('npx', ['npx', '-y', 'chrome-devtools-mcp@1.12.0',
                 '--no-usage-statistics', f'--browserUrl=http://{address}:9223'])
