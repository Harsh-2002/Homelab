#!/bin/sh
# A coordinated logical/file/config backup; briefly stops application writers.
set -eu
umask 077
cd /srv/supabase
exec 9>/run/lock/supabase-backup.lock
flock -n 9 || exit 1
destination="backups/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p backups
chmod 700 backups
mkdir -m 700 "$destination"
resume() { sh compose.sh up -d --wait; }
trap resume EXIT HUP INT TERM
sh compose.sh stop api-gw auth rest realtime storage functions supavisor studio
docker exec supabase-db pg_dumpall -U supabase_admin --globals-only > "$destination/globals.sql"
docker exec supabase-db pg_dump -U supabase_admin -d postgres -Fc > "$destination/postgres.dump"
docker exec supabase-db pg_dump -U supabase_admin -d _supabase -Fc > "$destination/platform.dump"
tar -czf "$destination/files-config.tar.gz" .env homelab.env .supabase-version \
    docker-compose.yaml docker-compose.logs.yml compose.homelab.yaml compose.images.yml \
    compose.watchtower.yaml compose.auto-update.yaml compose.sh volumes/storage volumes/functions volumes/snippets \
    volumes/api volumes/db/init volumes/db/*.sql
# PostgreSQL's pgsodium root-key file lives in this named volume, not the data bind.
config_path=$(docker volume inspect supabase_db-config --format '{{.Mountpoint}}')
tar -C "$config_path" -czf "$destination/db-config.tar.gz" .
touch "$destination/COMPLETE"
echo "Completed protected backup: /srv/supabase/$destination"
# Keep the last three complete sets. Failures stay available for inspection.
python3 - <<'PY'
from pathlib import Path
import re
import shutil
root = Path('/srv/supabase/backups')
complete = sorted(p for p in root.iterdir() if p.is_dir() and re.fullmatch(r'\d{8}T\d{6}Z', p.name) and (p / 'COMPLETE').is_file())
for entry in complete[:-3]:
    shutil.rmtree(entry)
PY
