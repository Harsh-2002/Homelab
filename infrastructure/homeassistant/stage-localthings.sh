#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || "$1" != /* || -e "$1" ]]; then
  echo "Usage: $0 /absolute/new/staging-directory" >&2
  exit 2
fi

TASK_STAGE="$1"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p -- "$TASK_STAGE"
curl -fsSL --max-time 60 \
  https://github.com/mbillow/localthings/archive/refs/tags/v0.34.0.tar.gz \
  -o "$TASK_STAGE/upstream.tar.gz"
echo "1968cdc055388e99142ad8c4fd894d38a227a0bb77920393f33d663526197e33  $TASK_STAGE/upstream.tar.gz" | sha256sum --check

python3 - "$TASK_STAGE" <<'PY'
from pathlib import Path, PurePosixPath
import sys
import tarfile

stage = Path(sys.argv[1])
with tarfile.open(stage / "upstream.tar.gz", "r:gz") as archive:
    members = [m for m in archive.getmembers() if m.name.startswith("localthings-0.34.0/custom_components/localthings/")]
    if not members:
        raise SystemExit("Expected integration directory absent")
    for member in members:
        path = PurePosixPath(member.name)
        if member.issym() or member.islnk() or path.is_absolute() or ".." in path.parts:
            raise SystemExit("Unsafe archive member")
    archive.extractall(stage, members=members, filter="data")
PY

TASK_COMPONENT="$TASK_STAGE/localthings-0.34.0/custom_components/localthings"
for TASK_PATCH in registry.patch translations.patch select-names.patch; do
  patch --fuzz=0 -p1 -d "$TASK_COMPONENT" < "$SCRIPT_DIR/localthings/$TASK_PATCH"
done
cp "$SCRIPT_DIR/localthings/homelab_samsung_ac.py" "$TASK_COMPONENT/registry/capabilities/"
python3 -m json.tool "$TASK_COMPONENT/translations/en.json" >/dev/null
python3 -m compileall -q "$TASK_COMPONENT"
python3 "$SCRIPT_DIR/localthings/test_controls.py" "$TASK_COMPONENT"
echo "Staged: $TASK_COMPONENT"
echo "No live Home Assistant or device changes made."
