#!/usr/bin/python3
"""Run Calamares' selected GRUB install with fresh probing and target checks.
No disk discovery/selection or writes to unselected disks are performed here.
"""
import os,sys,subprocess,json,stat
from pathlib import Path

def checked_args(args):
    # Never force a BIOS blocklist install if safe embedding is unavailable.
    result=[a for a in args if a not in ('--force','--recheck')]
    return ['/usr/sbin/grub-install','--recheck',*result]

def verify_config(text,uuid):
    if not uuid or uuid not in text:raise RuntimeError('Generated GRUB menu does not reference the installed root filesystem UUID.')
    if 'menuentry ' not in text:raise RuntimeError('Generated GRUB menu contains no boot entries.')

def output(args):return subprocess.check_output(args,text=True,timeout=60).strip()

def main(args):
    report={'arguments':args,'status':'preparing'}
    dest=Path('/var/log/macaque-bootloader.json')
    try:
        if os.geteuid()!=0:raise RuntimeError('This installer helper requires root inside the installed target.')
        if not Path('/etc/macaque-installed').exists():raise RuntimeError('Missing installed-target marker; refusing to run on the live system.')
        if not list(Path('/boot').glob('vmlinuz-*')):raise RuntimeError('Installed kernel is missing from /boot.')
        if not list(Path('/boot').glob('initrd.img-*')):raise RuntimeError('Installed initramfs is missing from /boot.')
        uuid=output(['/usr/sbin/grub-probe','--target=fs_uuid','/'])
        boot_uuid=output(['/usr/sbin/grub-probe','--target=fs_uuid','/boot/grub'])
        report.update(root_uuid=uuid,boot_uuid=boot_uuid)
        # The image's build-time map must never override install-time probing.
        mapping=Path('/boot/grub/device.map')
        if mapping.exists():mapping.rename(mapping.with_name('device.map.before-macaque-install'))
        command=checked_args(args)
        subprocess.run(command,check=True,timeout=300)
        subprocess.run(['/usr/sbin/update-grub'],check=True,timeout=300)
        verify_config(Path('/boot/grub/grub.cfg').read_text(),uuid)
        platform='i386-pc' if any('i386-pc' in a for a in args) else 'x86_64-efi'
        if not (Path('/boot/grub')/platform/'normal.mod').is_file():raise RuntimeError('Installed GRUB normal.mod is missing for '+platform)
        report['status']='verified-files-and-configuration-not-a-boot-test'
        print('Macaque bootloader prepared for root UUID',uuid)
        print('On a two-disk BIOS laptop, boot the drive selected as bootloader target in the installer. Other disks may still contain an older GRUB.')
    except Exception as ex:
        report.update(status='failed',error=str(ex));raise
    finally:
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main(sys.argv[1:])
