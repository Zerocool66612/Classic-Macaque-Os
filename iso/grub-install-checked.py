#!/usr/bin/python3
"""Finalize GRUB against the installed filesystem and the explicitly selected disk."""
import os,sys,subprocess,json,re
from pathlib import Path

def output(args):return subprocess.check_output(args,text=True,timeout=60).strip()

def checked_args(args):
    result=[a for a in args if a not in ('--force','--recheck') and not a.startswith('--boot-directory=')]
    extra=['--modules=part_msdos part_gpt ext2 search search_fs_uuid normal configfile'] if '--target=i386-pc' in result else []
    return ['/usr/sbin/grub-install','--recheck','--boot-directory=/boot',*extra,*result]

def verify_config(text,uuid):
    if not uuid or uuid not in text:raise RuntimeError('Generated GRUB menu does not reference the installed root filesystem UUID.')
    if 'menuentry ' not in text:raise RuntimeError('Generated GRUB menu contains no boot entries.')
    linux_lines=[line for line in text.splitlines() if re.match(r'^\s*linux(?:efi)?\s',line)]
    if not any(re.search(r'\broot=UUID='+re.escape(uuid)+r'(?:\s|$)',line) for line in linux_lines):
        raise RuntimeError('Generated Linux boot entry must use the installed root UUID, not a temporary device name.')

def physical_disks(device):
    data=json.loads(output(['/usr/bin/lsblk','--json','--paths','--inverse','--output','NAME,TYPE',device]))
    found=set()
    def visit(items):
        for item in items:
            if item.get('type') in ('disk','loop'):found.add(os.path.realpath(item['name']))
            visit(item.get('children',[]))
    visit(data.get('blockdevices',[]))
    return found

def bios_install_target(args,boot_device):
    targets=[os.path.realpath(a) for a in args if a.startswith('/dev/')]
    disks=physical_disks(boot_device)
    if len(targets)!=1 or len(disks)!=1 or targets[0] not in disks:
        raise RuntimeError('The BIOS bootloader target must be the whole disk containing /boot. Select that disk as the bootloader target; no other disk was changed.')
    return targets[0]

def remember_bios_target(device):
    # Retain the selected disk for future Debian GRUB updates, not the live build's choice.
    stable=device
    folder=Path('/dev/disk/by-id')
    if folder.is_dir():
        candidates=sorted(p for p in folder.iterdir() if '-part' not in p.name and os.path.realpath(p)==device)
        if candidates:stable=str(candidates[0])
    settings='grub-pc grub-pc/install_devices multiselect '+stable+'\ngrub-pc grub-pc/install_devices_empty boolean false\n'
    subprocess.run(['/usr/bin/debconf-set-selections'],input=settings,text=True,check=True,timeout=30)

def install_grub(args):
    command=checked_args(args)
    result=subprocess.run(command,capture_output=True,text=True,timeout=300)
    if result.returncode:
        details=(result.stdout+'\n'+result.stderr).strip()
        print(details,file=sys.stderr,flush=True)
        raise RuntimeError('GRUB installation failed (exit '+str(result.returncode)+'): '+details[-4000:])

def main(args):
    report={'arguments':args,'status':'preparing'}
    dest=Path('/var/log/macaque-bootloader.json')
    try:
        if os.geteuid()!=0:raise RuntimeError('This installer helper requires root inside the installed target.')
        if not Path('/etc/macaque-installed').exists():raise RuntimeError('Missing installed-target marker; refusing to run on the live system.')
        if not list(Path('/boot').glob('vmlinuz-*')):raise RuntimeError('Installed kernel is missing from /boot.')
        if not list(Path('/boot').glob('initrd.img-*')):raise RuntimeError('Installed initramfs is missing from /boot.')
        mapping=Path('/boot/grub/device.map')
        if mapping.exists():mapping.rename(mapping.with_name('device.map.before-macaque-install'))
        bios='--target=i386-pc' in args
        # Calamares has already selected the destination. Do not make the
        # initial installation depend on grub-probe or a pre-existing menu.
        # Those checks can fail before GRUB has created its own files.
        targets=[os.path.realpath(a) for a in args if a.startswith('/dev/')]
        if bios:
            if len(targets)!=1 or not Path(targets[0]).exists():
                raise RuntimeError('BIOS installation requires one existing whole-disk destination.')
            kind=output(['/usr/bin/lsblk','--noheadings','--nodeps','--output','TYPE',targets[0]])
            if kind.strip() not in ('disk','loop'):
                raise RuntimeError('Refusing to install BIOS GRUB to a partition or non-disk device.')
        target=targets[0] if bios else None
        report.update(install_device=target)
        uuid_conf=Path('/etc/default/grub.d/61-macaque-root-uuid.cfg')
        uuid_conf.parent.mkdir(parents=True,exist_ok=True)
        uuid_conf.write_text('GRUB_DISABLE_LINUX_UUID=false\\nGRUB_DISABLE_LINUX_PARTUUID=true\\n')
        # Install using GRUB's native device discovery first, then generate
        # and verify the menu against the completed installation.
        install_grub(args)
        subprocess.run(['/usr/sbin/update-grub'],check=True,timeout=300)
        uuid=output(['/usr/sbin/grub-probe','--target=fs_uuid','/'])
        boot_uuid=output(['/usr/sbin/grub-probe','--target=fs_uuid','/boot/grub'])
        boot_device=output(['/usr/sbin/grub-probe','--target=device','/boot/grub'])
        report.update(root_uuid=uuid,boot_uuid=boot_uuid,boot_device=boot_device)
        verify_config(Path('/boot/grub/grub.cfg').read_text(),uuid)
        platform='i386-pc' if bios else 'x86_64-efi'
        if not (Path('/boot/grub')/platform/'normal.mod').is_file():raise RuntimeError('Installed GRUB normal.mod is missing for '+platform)
        if bios:remember_bios_target(target)
        subprocess.run(['/bin/sync'],check=True,timeout=60)
        report['status']='verified-files-and-configuration-not-a-boot-test'
        print('Macaque bootloader finalized for root UUID',uuid,'boot UUID',boot_uuid,'device',target or boot_device)
    except Exception as ex:
        report.update(status='failed',error=str(ex));raise
    finally:
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2)+'\n')

def finalize():
    report=json.loads(Path('/var/log/macaque-bootloader.json').read_text())
    args=report.get('arguments')
    if not isinstance(args,list) or not args or not all(isinstance(a,str) for a in args) or '--finalize' in args:
        raise RuntimeError('The installer did not record a valid bootloader installation. Refusing to finish.')
    main(args)

if __name__=='__main__':
    if sys.argv[1:]==['--finalize']:finalize()
    else:main(sys.argv[1:])
