"""Check analytics internally without publishing its port or printing keys."""
import json
import pathlib
import shlex
import subprocess
import urllib.request
import urllib.error
import urllib.parse

env = {}
for line in pathlib.Path('/srv/supabase/.env').read_text().splitlines():
    if line and not line.startswith('#') and '=' in line:
        key, value = line.split('=', 1)
        env[key] = shlex.split(value)[0] if value else ''
ip = subprocess.check_output(['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', 'supabase-analytics'], text=True).strip()
query = urllib.parse.urlencode({'sql': 'select count(*) as total from `gotrue.logs.prod`'})
req = urllib.request.Request('http://' + ip + ':4000/api/query?' + query, headers={'x-api-key': env['LOGFLARE_PRIVATE_ACCESS_TOKEN']})
try:
    with urllib.request.urlopen(req, timeout=15) as response:
        result = json.load(response)
except urllib.error.HTTPError as error:
    result = json.loads(error.read())
assert result.get('result', [{}])[0].get('total', 0) > 0, 'Auth log ingestion/query did not return events'
print('PASS: Logflare query returned', result['result'][0]['total'], 'Auth events ingested through Vector')
