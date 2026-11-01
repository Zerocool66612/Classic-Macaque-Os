#!/usr/bin/python3
"""User-session UDisks actions restricted to removable non-system disks."""
import json,subprocess,sys,os,shutil,stat,tempfile,ctypes,errno
from pathlib import Path
COLUMNS='NAME,PATH,TYPE,TRAN,RM,HOTPLUG,MODEL,LABEL,SIZE,FSTYPE,MOUNTPOINTS,RO,UUID,MAJ:MIN'
def protected(mount):return mount in ('/','/boot','/boot/efi','/home','[SWAP]') or mount.startswith(('/run/live','/lib/live','/usr','/var'))
def removable(data):
    disks=[]
    for disk in data.get('blockdevices',[]):
        if disk.get('type')!='disk' or not (disk.get('tran')=='usb' or disk.get('rm')):continue
        def walk(n):
            yield n
            for child in n.get('children',[]):yield from walk(child)
        nodes=list(walk(disk))
        if any(protected(m) for n in nodes for m in (n.get('mountpoints') or []) if m):continue
        volumes=[]
        for n in nodes:
            if n.get('type') not in ('part','disk') or not n.get('fstype') or n['fstype'] in ('swap','crypto_LUKS','LVM2_member','linux_raid_member'):continue
            if n.get('children'):continue
            volumes.append({'device':n['path'],'identity':n['maj:min'],'uuid':n.get('uuid') or '', 'name':n.get('label') or n['name'],'size':n.get('size',0),'mounts':[m for m in n.get('mountpoints',[]) if m],'readonly':bool(n.get('ro'))})
        if volumes:disks.append({'device':disk['path'],'identity':disk['maj:min'],'model':(disk.get('model') or disk['name']).strip(),'volumes':volumes})
    return disks

def commit_copy(staged,destination):
    # Linux renameat2 commits atomically without replacing another file, also
    # on FAT/exFAT where hard-link based exclusive commits aren't available.
    libc=ctypes.CDLL(None,use_errno=True)
    rename=libc.renameat2;rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint];rename.restype=ctypes.c_int
    if rename(-100,os.fsencode(staged),-100,os.fsencode(destination),1)!=0:
        code=ctypes.get_errno();raise OSError(code,os.strerror(code),str(destination))

def inventory():
    result=subprocess.run(['lsblk','--json','--bytes','--paths','--output',COLUMNS],capture_output=True,text=True,check=True,timeout=15)
    return removable(json.loads(result.stdout))

def selected(payload,disks):
    for disk in disks:
        for volume in disk['volumes']:
            if volume['device']==payload.get('device') and volume['identity']==payload.get('identity') and volume['uuid']==payload.get('uuid',''):return disk,volume
    raise ValueError('This removable volume changed or is a protected system/live disk. Refresh and select it again.')

def action(payload,scan=inventory,runner=subprocess.run):
    operation=payload.get('action','list')
    if operation=='list':return {'disks':scan()}
    disk,volume=selected(payload,scan())
    def call(args):runner(args,check=True,capture_output=True,text=True,timeout=90)
    if operation=='mount':call(['udisksctl','mount','--block-device',volume['device']])
    elif operation=='unmount':call(['udisksctl','unmount','--block-device',volume['device']])
    elif operation=='eject':
        # Revalidate before each unmount and before powering off. Never force a
        # busy filesystem or affect siblings that aren't on the selected disk.
        for v in disk['volumes']:
            if v['mounts']:
                current,v2=selected({'device':v['device'],'identity':v['identity'],'uuid':v['uuid']},scan())
                if current['identity']!=disk['identity']:raise ValueError('Disk identity changed.')
                call(['udisksctl','unmount','--block-device',v2['device']])
        current,_=selected(payload,scan())
        if any(v['mounts'] for v in current['volumes']):raise ValueError('A volume is still mounted. Close its files and try again.')
        call(['udisksctl','power-off','--block-device',disk['device']])
    elif operation in ('import','export'):
        if not volume['mounts']:raise ValueError('Mount this volume first.')
        mount=Path(volume['mounts'][0]).resolve();local=Path(payload['local_root']).resolve()
        chosen=Path(payload['source']);source=chosen.resolve();name=chosen.name
        if chosen.is_symlink() or not source.is_file():raise ValueError('Choose a regular file.')
        if operation=='import':
            if not source.is_relative_to(mount):raise ValueError('Choose a file from this USB volume.')
            destination=local/'Documents'/name
        else:
            if volume['readonly']:raise ValueError('This USB volume is read only.')
            if not source.is_relative_to(local):raise ValueError('Choose a file from Macaque HD.')
            destination=mount/name
        # Resolve parent to prevent an external Documents symlink redirect.
        if operation=='import' and not destination.parent.resolve().is_relative_to(local):raise ValueError('The import folder is outside Macaque HD.')
        original=destination;i=2
        while destination.exists():destination=original.with_name(original.stem+f' {i}'+original.suffix);i+=1
        descriptor,staged=tempfile.mkstemp(prefix='.macaque-copy-',suffix='.part',dir=destination.parent)
        try:
            with os.fdopen(descriptor,'wb') as target:
                with source.open('rb') as stream:shutil.copyfileobj(stream,target,1024*1024)
                target.flush();os.fsync(target.fileno())
            while True:
                try:commit_copy(staged,destination);break
                except OSError as ex:
                    if ex.errno!=errno.EEXIST:raise
                    destination=original.with_name(original.stem+f' {i}'+original.suffix);i+=1
        finally:Path(staged).unlink(missing_ok=True)
        return {'message':'Copied to '+str(destination),'disks':scan()}
    else:raise ValueError('Unknown removable-drive action.')
    return {'message':'Drive operation completed.','disks':scan()}
if __name__=='__main__':
    try:print(json.dumps(action(json.loads(sys.stdin.read(32768)))))
    except Exception as ex:
        text=ex.stderr.strip() if isinstance(ex,subprocess.CalledProcessError) and ex.stderr else str(ex)
        print(text+' No forced unmount or formatting was attempted.',file=sys.stderr);sys.exit(1)
