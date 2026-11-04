"""Checksum atomically completed rsync files while later files are copied.

The transfer uses temporary names and atomic renames, never --inplace. A final
full walk after COPY-STATUS checks every path and rehashes changed identities.
"""
import hashlib,json,os,re,stat,time
from pathlib import Path
os.umask(0o077)
root=Path('/mnt/homelab-retirement/homelab-backup-2026-10-31')
base=root/'ctr/data';marker=root/'ctr/COPY-STATUS.txt'
assert (root/'BACKUP-DISK.json').is_file()
progress=root/'manifests/ctr-data-files.progress.json'
manifest=root/'manifests/ctr-data-files.jsonl'
records={};started=time.time();last=0;read_bytes=0
temporary=re.compile(r'^\..+\.[A-Za-z0-9]{6}$')
def signature(s):
    return (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_uid,s.st_gid)
def report():
    global last
    if time.time()-last>5:
        progress.write_text(json.dumps({'phase':'overlapping copy/readback','files':len(records),'bytes_read':read_bytes,'elapsed_seconds':round(time.time()-started)}));last=time.time()
def walk(final):
    global read_bytes
    found=set()
    for directory,dirs,files in os.walk(base,followlinks=False):
        dirs.sort();files.sort()
        entries=files+[d for d in dirs if (Path(directory)/d).is_symlink()]
        for name in entries:
            if not final and temporary.match(name):continue
            p=Path(directory)/name;key=p.relative_to(root).as_posix()
            try:
                before=p.lstat();sig=signature(before)
                if not(stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)):continue
                found.add(key)
                if key in records and records[key][0]==sig:continue
                row={'path':key,'mode':stat.S_IMODE(before.st_mode),'uid':before.st_uid,'gid':before.st_gid}
                if stat.S_ISLNK(before.st_mode):row['link']=os.readlink(p)
                else:
                    digest=hashlib.sha256()
                    with p.open('rb') as f:
                        while chunk:=f.read(4*1024**2):
                            digest.update(chunk);read_bytes+=len(chunk);report()
                    row.update(bytes=before.st_size,sha256=digest.hexdigest())
                if signature(p.lstat())!=sig:
                    if final:raise RuntimeError('A file changed after the transfer completion marker')
                    continue
                records[key]=(sig,row)
                report()
            except FileNotFoundError:
                if final:raise
    return found
while True:
    final=marker.exists()
    found=walk(final)
    if final:break
    time.sleep(5)
records={k:v for k,v in records.items() if k in found}
with manifest.with_suffix('.partial.jsonl').open('w') as f:
    for key in sorted(records):f.write(json.dumps(records[key][1])+'\n')
    f.flush();os.fsync(f.fileno())
os.replace(manifest.with_suffix('.partial.jsonl'),manifest)
progress.write_text(json.dumps({'complete':True,'files':len(records),'bytes_read':read_bytes,'logical_bytes':sum(v[1].get('bytes',0) for v in records.values()),'elapsed_seconds':round(time.time()-started),'verification':'All final paths checked after rsync completion; changed file identities rehashed'}))
print('CTR data readback checksums complete:',len(records),'entries',flush=True)
