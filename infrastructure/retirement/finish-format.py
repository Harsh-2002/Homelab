#!/usr/bin/env python3
"""Observe already-authorized erase jobs; verify, document and unmount on completion.

This program never starts an erase operation. Private device identities live in
an owner-only plan outside Git. No credentials are read into reports.
"""
import argparse,json,os,re,shlex,shutil,subprocess,tempfile,time
from pathlib import Path

def run(args,**kw):
    return subprocess.run(args,check=True,text=True,**kw)
def capture(args,**kw):
    return run(args,capture_output=True,**kw).stdout.strip()
def ssh(host,code):
    assert host in ('px10','px20')
    return run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2',host,'python3','-'],input=code,capture_output=True,timeout=90).stdout

def probe(host):
    return json.loads(ssh(host,r'''
import json,socket,subprocess
from pathlib import Path
host=socket.gethostname().split('.')[0];result={}
for kind,prefix in [('sata','SATA'),('usb','USB256')]:
 p=Path('/root/retirement-20261031/format-results')/(prefix+'_'+host.upper()+'.json')
 d=json.loads(p.read_text()) if p.exists() else {'phase':'missing'}
 unit='retirement-erase-usb256.service' if kind=='usb' else 'retirement-erase-sata.service'
 state=subprocess.run(['systemctl','show',unit,'-p','ActiveState','--value'],capture_output=True,text=True).stdout.strip()
 d['unit_state']=state;result[kind]=d
print(json.dumps(result))
'''))

def report(plan,results):
    public={'status':'in_progress','updated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'disks':{},'preserved':['NVMe host/root disks','dev VM root disk','4TB verified data backup'],'all_targets_unmounted':False}
    for host in ('px10','px20'):
        for kind in ('sata','usb'):
            d=results[host][kind];expected=plan['serials'][host][kind]
            if d.get('serial')!=expected:raise RuntimeError('Device identity differs from approved plan')
            public['disks'][host+'_'+kind]={k:d[k] for k in ('phase','bytes','label','filesystem','erase_method','filesystem_check','left_unmounted') if k in d}
    complete=all(d.get('phase')=='complete' for h in results.values() for d in h.values())
    failed=any(d.get('phase')!='complete' and d.get('unit_state') not in ('active','activating') for h in results.values() for d in h.values())
    if complete:public['status']='complete'
    elif failed:public['status']='failed'
    return public

def verify_targets(plan):
    for host in ('px10','px20'):
        expected=plan['serials'][host]
        code=r'''
import json,subprocess
from pathlib import Path
expected=EXPECTED
host=HOST
for kind,prefix in [('sata','SATA'),('usb','USB256')]:
 p=Path('/root/retirement-20261031/format-results')/(prefix+'_'+host.upper()+'.json');d=json.loads(p.read_text());assert d['phase']=='complete' and d['serial']==expected[kind]
 dev=d['device'];assert subprocess.check_output(['lsblk','-dn','-o','SERIAL',dev],text=True).strip()==expected[kind]
 part=dev+'-part1';assert subprocess.run(['findmnt','-rn','--source',part],stdout=subprocess.DEVNULL).returncode==1
 assert subprocess.check_output(['blkid','-s','TYPE','-o','value',part],text=True).strip()=='ext4'
 assert subprocess.check_output(['blkid','-s','LABEL','-o','value',part],text=True).strip()==d['label']
 subprocess.run(['e2fsck','-n',part],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
assert 'data' not in subprocess.check_output(['zpool','list','-H','-o','name'],text=True).splitlines()
subprocess.run(['zpool','status','-x','rpool'],check=True,stdout=subprocess.DEVNULL)
if host=='px10':assert subprocess.check_output(['qm','status','100'],text=True).strip()=='status: running'
print('Four-disk postconditions and retained roots checked')
'''.replace('EXPECTED',repr(expected)).replace('HOST',repr(host))
        ssh(host,code)

def backup_mount(plan):
    uuid=plan['backup_uuid'];backup_serial=plan['backup_serial'];assert re.fullmatch(r'[a-f0-9-]{36}',uuid)
    ssh('px20',r'''
import subprocess,json
from pathlib import Path
uuid=UUID
mount='/mnt/homelab-retirement';dev='/dev/disk/by-uuid/'+uuid
assert BACKUP_SERIAL in subprocess.check_output(['lsblk','-ns','-o','SERIAL',dev],text=True).split()
probe=subprocess.run(['findmnt','-nr','-o','UUID','--target',mount],text=True,capture_output=True)
if probe.returncode==0 and probe.stdout.strip()==uuid:pass
else:
 assert subprocess.run(['mountpoint','-q',mount]).returncode!=0
 subprocess.run(['mount','-o','noatime,nodev,nosuid',dev,mount],check=True)
assert subprocess.check_output(['findmnt','-nr','-o','UUID','--target',mount],text=True).strip()==uuid
assert (Path(mount)/'homelab-backup-2026-10-31/BACKUP-DISK.json').is_file()
'''.replace('UUID',repr(uuid),1).replace('BACKUP_SERIAL',repr(backup_serial)))

def backup_close(plan):
    uuid=plan['backup_uuid']
    ssh('px20',r'''
import subprocess
uuid=UUID
mount='/mnt/homelab-retirement'
assert subprocess.check_output(['findmnt','-nr','-o','UUID','--target',mount],text=True).strip()==uuid
subprocess.run(['sync','-f',mount],check=True)
subprocess.run(['umount',mount],check=True)
subprocess.run(['e2fsck','-n','/dev/disk/by-uuid/'+uuid],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
assert subprocess.run(['mountpoint','-q',mount]).returncode!=0
'''.replace('UUID',repr(uuid),1))

def save_backup_report(plan,public,results):
    backup_mount(plan)
    payload={'public':public,'private_drive_results':results}
    code="from pathlib import Path\nimport json,os\nos.umask(0o077)\np=Path('/mnt/homelab-retirement/homelab-backup-2026-10-31/retirement-format');p.mkdir(exist_ok=True)\n(p/'FORMAT-COMPLETION.private.json').write_text("+repr(json.dumps(payload,indent=2)+'\n')+")\n"
    ssh('px20',code)
    note="Reviewed disk retirement completion; import this resource after restoring OpenViking.\n\n"+json.dumps(public,indent=2)+"\n"
    ssh('px20',"from pathlib import Path\nPath('/mnt/homelab-retirement/homelab-backup-2026-10-31/retirement-format/OPENVIKING-UPDATE-PENDING.md').write_text("+repr(note)+")\n")

def publish(plan,public):
    repo=Path(plan['repo']);published=None;workspace=None
    for attempt in range(3):
        run(['git','fetch','origin','main'],cwd=repo,stdout=subprocess.DEVNULL)
        workspace=Path(tempfile.mkdtemp(prefix='homelab-format-publish-'))
        work=workspace/'repo'
        try:
            run(['git','worktree','add','--detach',str(work),'origin/main'],cwd=repo,stdout=subprocess.DEVNULL)
            path=work/'infrastructure/retirement/DISK-FORMAT-STATUS.json';path.write_text(json.dumps(public,indent=2)+'\n')
            readme=work/'infrastructure/retirement/README.md';text=readme.read_text();message='All four approved data disks finished erasure, received fresh ext4 filesystems, passed checks and were left unmounted. The 4TB backup filesystem checked clean and is unmounted; NVMe roots and dev remain intact.' if public['status']=='complete' else 'The unattended erase reported a failure. Inspect the private format completion record before reuse.'
            text=re.sub(r'<!-- format-status -->.*?<!-- /format-status -->','<!-- format-status -->\n'+message+'\n<!-- /format-status -->',text,flags=re.S);readme.write_text(text)
            overview=work/'docs/architecture/README.md';body=overview.read_text();body=body.replace('The two external256GB disks are undergoing owner-approved full overwrites.','The two external256GB disks finished full overwrites, formatting and checks; all four data disks are unmounted.' if public['status']=='complete' else 'A USB erase failed; inspect the completion status.');overview.write_text(body)
            invpath=work/'docs/architecture/inventory.json';inv=json.loads(invpath.read_text());inv['retirementFormat']['externalUsbStatus']=public['status'];inv['retirementFormat']['status']='All four data disks formatted and unmounted' if public['status']=='complete' else 'USB erase failure; inspect private completion record'
            if public['status']=='complete':
                for disk in inv['physicalStorage']:
                    if disk['size']=='256 GB':disk['roles']=['Full logical overwrite verified; empty ext4; unmounted']
            invpath.write_text(json.dumps(inv,indent=2)+'\n')
            for name in ('internal-addresses.local.json','topology-addresses.local.json'):
                shutil.copy2(repo/'docs/architecture'/name,work/'docs/architecture'/name)
            run(['/bin/bash','infrastructure/retirement/rebuild-architecture.sh'],cwd=work)
            run(['git','add','docs/architecture','infrastructure/retirement/DISK-FORMAT-STATUS.json','infrastructure/retirement/README.md'],cwd=work)
            staged=capture(['git','diff','--cached','--name-only'],cwd=work).splitlines()
            assert not any('/internal/' in p or p.endswith('.local.json') for p in staged)
            run(['git','diff','--cached','--check'],cwd=work)
            run(['git','commit','-m','Record verified disk erasure completion'],cwd=work,stdout=subprocess.DEVNULL)
            commit=capture(['git','rev-parse','HEAD'],cwd=work)
            pushed=subprocess.run(['git','push','origin','HEAD:main'],cwd=work,text=True,capture_output=True)
            if pushed.returncode!=0:
                if attempt==2:raise RuntimeError('Completion publication did not fast-forward')
                continue
            assert capture(['git','ls-remote','origin','refs/heads/main'],cwd=work).split()[0]==commit
            published=commit
            if not capture(['git','status','--porcelain'],cwd=repo):
                merged=subprocess.run(['git','merge','--ff-only',commit],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                if merged.returncode==0 and capture(['git','rev-parse','HEAD'],cwd=repo)==commit:
                    shutil.copytree(work/'docs/architecture/internal',repo/'docs/architecture/internal',dirs_exist_ok=True)
            # Save the final source and private diagrams without a dangling worktree .git file.
            backup_mount(plan)
            target='px20:/mnt/homelab-retirement/homelab-backup-2026-10-31/retirement-format/completed-docs/Homelab/'
            ssh('px20',"from pathlib import Path\nPath('/mnt/homelab-retirement/homelab-backup-2026-10-31/retirement-format/completed-docs/Homelab').mkdir(parents=True,exist_ok=True)\n")
            run(['rsync','-aHAX','--exclude=.git',str(work)+'/',target],stdout=subprocess.DEVNULL)
            run(['scp','-q',str(work/'infrastructure/retirement/README.md'),'px20:/mnt/homelab-retirement/homelab-backup-2026-10-31/retirement-format/README.md'])
            bundle=workspace/'repository.bundle';run(['git','bundle','create',str(bundle),'--all','HEAD'],cwd=work,stdout=subprocess.DEVNULL)
            run(['scp','-q',str(bundle),'px20:/mnt/homelab-retirement/homelab-backup-2026-10-31/retirement-format/completed-docs/repository.bundle'])
            return published
        finally:
            if work.exists():subprocess.run(['git','worktree','remove','--force',str(work)],cwd=repo,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            shutil.rmtree(workspace,ignore_errors=True)
    raise RuntimeError('Could not publish completion')

def hash_format_metadata():
    ssh('px20',"import subprocess\nb='/mnt/homelab-retirement/homelab-backup-2026-10-31'\nsubprocess.run(['python3',b+'/manifests/hash-backup.py',b,'format-result-files','retirement-format'],check=True,stdout=subprocess.DEVNULL)\n")

def verify_cutover(plan):
    """Require the final NVMe/file backup before declaring disks ready to remove."""
    backup_mount(plan)
    return json.loads(ssh('px20',r'''
import hashlib,json
from pathlib import Path
b=Path('/mnt/homelab-retirement/homelab-backup-2026-10-31')
m=b/'manifests';summary=json.loads((m/'final-cutover-files.progress.json').read_text())
assert summary['complete'] is True
expected=(m/'FINAL-CUTOVER-MANIFEST.sha256').read_text().split()[0]
h=hashlib.sha256()
with (m/'final-cutover-files.jsonl').open('rb') as inp:
 while block:=inp.read(4*1024**2):h.update(block)
assert h.hexdigest()==expected
mapping=json.loads((b/'final-cutover/dev/consistent-sqlite/restore-map.json').read_text())
assert len(mapping)>=14 and all(r['integrity']=='ok' for r in mapping)
assert (b/'final-cutover/RESTORE-PATHS.json').is_file()
print(json.dumps(summary))
'''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    p=Path(args.plan);assert p.stat().st_uid==os.getuid() and p.stat().st_mode&0o077==0
    plan=json.loads(p.read_text());state=Path(plan['local_status']);state.parent.mkdir(parents=True,exist_ok=True)
    while True:
        try:results={host:probe(host) for host in ('px10','px20')};public=report(plan,results)
        except (subprocess.SubprocessError,ValueError,OSError):
            if args.check:raise
            print('Waiting for host connectivity',flush=True);time.sleep(30);continue
        state.write_text(json.dumps(public,indent=2)+'\n')
        if args.check:print(json.dumps(public,indent=2));return
        if public['status']!='in_progress':break
        print('USB full overwrites still active; NVMe roots and backup remain preserved',flush=True);time.sleep(30)
    try:
        if public['status']=='complete':verify_targets(plan);public['all_targets_unmounted']=True
        public['final_cutover_verification']=verify_cutover(plan)
        save_backup_report(plan,public,results);hash_format_metadata();backup_close(plan)
        public['backup_unmounted']=True;public['backup_filesystem_check']='clean'
        commit=publish(plan,public);public['published_commit']=commit
        save_backup_report(plan,public,results);hash_format_metadata();backup_close(plan)
        public['backup_unmounted']=True;public['backup_filesystem_check']='clean'
        state.write_text(json.dumps(public,indent=2)+'\n');print('COMPLETED: '+json.dumps(public),flush=True)
    except Exception:
        public['status']='finalization_failed';state.write_text(json.dumps(public,indent=2)+'\n')
        try:backup_close(plan)
        except Exception:pass
        raise
if __name__=='__main__':main()
