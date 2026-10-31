#!/usr/bin/env python3
"""Read back an immutable final-cutover tree, reusing verified hardlink hashes."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
import time

os.umask(0o077)
base = Path(sys.argv[1]).resolve()
tree = base / 'final-cutover'
manifests = base / 'manifests'
assert tree.is_dir() and (base / 'BACKUP-DISK.json').is_file()
origins = ['dev/rootfs', 'orva/rootfs', 'hosts/px10/rootfs', 'hosts/px20/rootfs']
origins += ['containers/' + name + '/rootfs' for name in
            ['101-proxy', '102-dns', '103-identity', '104-observability', '109-store']]
old = {}
for name in ['dev-files', 'px10-service-files', 'px20-service-files']:
    with (manifests / (name + '.jsonl')).open() as source:
        for line in source:
            row = json.loads(line)
            if any(row['path'].startswith(prefix + '/') for prefix in origins):
                old[row['path']] = row

count = reused = read_bytes = logical = checked = 0
started = time.monotonic()
last = started
partial = manifests / 'final-cutover-files.partial.jsonl'
progress = manifests / 'final-cutover-files.progress.json'

def status(complete=False):
    return dict(complete=complete, files=count, reused_hardlink_checksums=reused,
                new_bytes_read=read_bytes, logical_bytes=logical,
                sqlite_checked=checked, elapsed_seconds=round(time.monotonic()-started))

with partial.open('w') as out:
    for directory, dirs, files in os.walk(tree, followlinks=False):
        dirs.sort()
        files.sort()
        for name in files + [n for n in dirs if (Path(directory)/n).is_symlink()]:
            path = Path(directory)/name
            st = path.lstat()
            rel = path.relative_to(tree).as_posix()
            row = dict(path=path.relative_to(base).as_posix(),
                       mode=stat.S_IMODE(st.st_mode), uid=st.st_uid, gid=st.st_gid)
            if stat.S_ISLNK(st.st_mode):
                row['link'] = os.readlink(path)
            elif stat.S_ISREG(st.st_mode):
                match = old.get(rel)
                same = False
                if match and match.get('bytes') == st.st_size:
                    prior = (base/rel).lstat()
                    same = (prior.st_dev, prior.st_ino) == (st.st_dev, st.st_ino)
                if same:
                    digest = match['sha256']
                    reused += 1
                else:
                    h = hashlib.sha256()
                    with path.open('rb') as inp:
                        while block := inp.read(4*1024**2):
                            h.update(block)
                            read_bytes += len(block)
                    digest = h.hexdigest()
                row.update(bytes=st.st_size, sha256=digest)
                logical += st.st_size
                # Live raw dev/host databases have separate consistent copies.
                if not rel.startswith(('dev/rootfs/', 'hosts/')) and st.st_size >= 16:
                    with path.open('rb') as inp:
                        is_sqlite = inp.read(16) == b'SQLite format 3\x00'
                    if is_sqlite:
                        with sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1', uri=True) as db:
                            assert db.execute('PRAGMA quick_check').fetchall() == [('ok',)], rel
                        checked += 1
            else:
                continue
            out.write(json.dumps(row)+'\n')
            count += 1
            if time.monotonic()-last > 5:
                progress.write_text(json.dumps(status()))
                last = time.monotonic()
    out.flush()
    os.fsync(out.fileno())
target = manifests/'final-cutover-files.jsonl'
os.replace(partial, target)
seal = hashlib.sha256(target.read_bytes()).hexdigest()
(manifests/'FINAL-CUTOVER-MANIFEST.sha256').write_text(seal+'  '+target.name+'\n')
progress.write_text(json.dumps(status(True), indent=2)+'\n')
print(json.dumps(status(True)), flush=True)
