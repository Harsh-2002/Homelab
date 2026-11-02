#!/usr/bin/env python3
import os, sys, urllib.parse, urllib.request
cfg = {}
for line in open('/etc/smartd-alert.env'):
    if '=' in line:
        k, v = line.rstrip('\n').split('=', 1)
        cfg[k] = v
body = sys.stdin.read().strip() or 'smartd reported a warning'
device = os.environ.get('SMARTD_DEVICE', 'unknown')
fail = os.environ.get('SMARTD_FAILTYPE', 'SMART')
text = f"SMART warning: {device} ({fail})\n\n{body}"
data = urllib.parse.urlencode({
    'chat_id': cfg['TELEGRAM_CHAT_ID'],
    'text': text,
    'disable_web_page_preview': 'true',
}).encode()
req = urllib.request.Request(
    f"https://api.telegram.org/bot{cfg['TELEGRAM_BOT_TOKEN']}/sendMessage",
    data=data, method='POST')
with urllib.request.urlopen(req, timeout=15) as r:
    r.read()
