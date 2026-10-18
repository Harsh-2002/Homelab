#!/usr/bin/env python3
"""Guard the reviewed upstream database init overlays against silent omission."""
from pathlib import Path
import sys
import yaml

root = Path(__file__).resolve().parents[2]
chart = root/'gitops/apps/supabase'
expected = {'97-_supabase.sql', '98-webhooks.sql', '99-jwt.sql', '99-logs.sql',
            '99-pooler.sql', '99-realtime.sql', '99-roles.sql'}
bootstrap = (chart/'templates/bootstrap-job.yaml').read_text()
platform = (chart/'files/db/ensure-platform.sql').read_text()
executed = bootstrap + platform
for name in expected:
    assert (chart/'files/db'/name).is_file(), f'Missing upstream init overlay: {name}'
    assert name in executed, f'Init overlay never executed: {name}'
job = yaml.safe_load((chart/'templates/platform-init.yaml').read_text())
container = job['spec']['template']['spec']['containers'][0]
assert '/seed/ensure-platform.sql' in container['args'][0]
env = {e['name'] for e in container['env']}
assert {'PGPASSWORD','POSTGRES_PASSWORD','JWT_SECRET','JWT_EXP'} <= env
assert 'pg_advisory_lock' in platform and 'platform_migrations' in platform
assert 'to_regprocedure' in platform
if len(sys.argv) == 2:
    # Pass the pinned, reviewed community chart checkout to detect new overlays.
    upstream = Path(sys.argv[1])/'charts/supabase/templates/db/statefulset.yaml'
    import re
    source = upstream.read_text()
    declared = set(re.findall(r'/custom-init-scripts/([\w-]+\.sql)', source))
    assert declared == expected, f'Upstream init inventory changed: {declared ^ expected}'
    for name in ('98-webhooks.sql','99-roles.sql','99-jwt.sql'):
        original = Path(sys.argv[1])/'charts/supabase/files/db/initdb'/name
        assert original.read_bytes() == (chart/'files/db'/name).read_bytes(), f'Review altered upstream SQL: {name}'
print('Reviewed upstream init overlays covered; versioned migration and secret references valid')
