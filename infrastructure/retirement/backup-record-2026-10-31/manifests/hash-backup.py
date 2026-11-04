import hashlib,json,os,stat,sys,time
from pathlib import Path
os.umask(0o077)
root=Path(sys.argv[1]);name=sys.argv[2];components=sys.argv[3:]
assert (root/'BACKUP-DISK.json').is_file()
manifest=root/'manifests'/(name+'.jsonl')
progress=root/'manifests'/(name+'.progress.json')
count=total=0;started=time.time();last=0
with manifest.with_suffix('.partial.jsonl').open('w') as output:
    for component in components:
        base=root/component
        assert base.is_dir(),component
        for directory,dirs,files in os.walk(base,followlinks=False):
            dirs.sort();files.sort()
            for entry in files+[d for d in dirs if (Path(directory)/d).is_symlink()]:
                path=Path(directory)/entry;info=path.lstat()
                row={'path':path.relative_to(root).as_posix(),'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'gid':info.st_gid}
                if stat.S_ISLNK(info.st_mode):row['link']=os.readlink(path)
                elif stat.S_ISREG(info.st_mode):
                    digest=hashlib.sha256()
                    with path.open('rb') as f:
                        while chunk:=f.read(4*1024**2):digest.update(chunk)
                    row.update(bytes=info.st_size,sha256=digest.hexdigest());total+=info.st_size
                else:continue
                output.write(json.dumps(row,ensure_ascii=False)+'\n');count+=1
                if time.time()-last>5:
                    progress.write_text(json.dumps({'files':count,'bytes_read':total,'elapsed_seconds':round(time.time()-started)}));last=time.time()
    output.flush();os.fsync(output.fileno())
os.replace(manifest.with_suffix('.partial.jsonl'),manifest)
progress.write_text(json.dumps({'complete':True,'files':count,'bytes_read':total,'elapsed_seconds':round(time.time()-started)}))
print(json.dumps({'manifest':manifest.name,'files':count,'bytes_read':total,'elapsed_seconds':round(time.time()-started)}),flush=True)
