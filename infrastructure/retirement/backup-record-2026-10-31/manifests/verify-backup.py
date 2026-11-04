"""Read-only SHA-256 verification of the portable backup's JSONL manifests."""
import hashlib,json,os,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
assert (root/'BACKUP-DISK.json').is_file(),'Expected backup root containing BACKUP-DISK.json'
manifests=sorted((root/'manifests').glob('*-files.jsonl'))
assert manifests,'No completed file manifests found'
checked=0;failed=0
for manifest in manifests:
    for line in manifest.open():
        row=json.loads(line);relative=Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path=root/relative
        try:
            if 'link' in row:assert path.is_symlink() and os.readlink(path)==row['link']
            else:
                assert path.is_file() and not path.is_symlink()
                assert path.stat().st_size==row['bytes']
                digest=hashlib.sha256()
                with path.open('rb') as f:
                    while block:=f.read(4*1024**2):digest.update(block)
                assert digest.hexdigest()==row['sha256']
            checked+=1
        except (AssertionError,OSError):
            failed+=1;print('FAILED:',row['path'])
    print('Read manifest:',manifest.name,flush=True)
print('Verified entries:',checked,'Failed:',failed)
sys.exit(1 if failed else 0)
