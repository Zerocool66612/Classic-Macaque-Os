#!/usr/bin/python3
"""Inventory or release only direct swap partitions on an explicitly selected disk."""
import argparse,json,os,stat,subprocess
from pathlib import Path

def command(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=120,env={**os.environ,"LC_ALL":"C"})
    if result.returncode:raise ValueError(result.stderr.strip() or 'Command failed: '+args[0])
    return result.stdout

def inventory():
    tree=json.loads(command(['/usr/bin/lsblk','--json','--paths','--bytes','--output','NAME,TYPE,PKNAME,MODEL,SIZE,MOUNTPOINTS,MAJ:MIN,RO']))['blockdevices']
    swaps=json.loads(command(['/usr/sbin/swapon','--show','--json','--bytes','--output','NAME,TYPE,SIZE,USED'])).get('swapdevices',[])
    source=command(['/usr/bin/findmnt','--noheadings','--output','SOURCE','--target','/run/live/medium']).strip().split('[')[0]
    return {'disks':tree,'swaps':swaps,'live_source':source}

def descendants(node):
    yield node
    for child in node.get('children',[]):yield from descendants(child)

def plan(data,disk,expected):
    candidates=[d for d in data['disks'] if d.get('name')==disk and d.get('type')=='disk']
    if len(candidates)!=1:raise ValueError('Select an entire physical disk from the refreshed list.')
    node=candidates[0]
    if node.get('maj:min')!=expected:raise ValueError('Disk identity changed. Refresh the disk list.')
    if node.get('ro'):raise ValueError('The selected disk is read only.')
    children=list(descendants(node));names={os.path.realpath(n['name']) for n in children}
    source=data.get('live_source','')
    if not source.startswith('/dev/'):raise ValueError('Cannot identify the live boot device; refusing swap changes.')
    if os.path.realpath(source) in names:raise ValueError('This is the live USB boot device. Select the installation disk instead.')
    direct={os.path.realpath(c['name']) for c in children if c.get('type')=='part' and c.get('pkname')==disk}
    return [s['name'] for s in data['swaps'] if s.get('type')=='partition' and os.path.realpath(s['name']) in direct]

def release(disk,expected,get_inventory=inventory,run=command):
    if os.geteuid()!=0:raise ValueError('Administrator access is required.')
    if not Path('/etc/macaque-live').is_file() or 'boot=live' not in Path('/proc/cmdline').read_text().split():raise ValueError('Swap release is available only in the Macaque live session.')
    if not stat.S_ISBLK(os.stat(disk).st_mode):raise ValueError('The disk path is not a block device.')
    targets=plan(get_inventory(),disk,expected);done=[]
    try:
        for target in targets:
            # Revalidate immediately before each operation.
            if target not in plan(get_inventory(),disk,expected):raise ValueError('Swap inventory changed; refresh before trying again.')
            run(['/usr/sbin/swapoff','--',target]);done.append(target)
    except (OSError,ValueError,subprocess.TimeoutExpired) as ex:
        raise ValueError('Released: '+(', '.join(done) or 'none')+'. Stopped: '+str(ex)) from ex
    remaining=plan(get_inventory(),disk,expected)
    if remaining:raise ValueError('Swap is still active or was reactivated: '+', '.join(remaining))
    return 'Released '+(', '.join(done) if done else 'no swap; none was active on this disk')+'. No partitions were formatted or removed.'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',action='store_true');p.add_argument('--disk');p.add_argument('--expected-id');args=p.parse_args()
    try:
        if args.release:
            if not args.disk or not args.expected_id:raise ValueError('Select a disk and supply its identity.')
            print(release(args.disk,args.expected_id))
        else:print(json.dumps(inventory()))
    except (OSError,ValueError,subprocess.TimeoutExpired) as ex:raise SystemExit(str(ex))
