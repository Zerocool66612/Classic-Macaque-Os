#!/usr/bin/python3
"""Configure a cached GRUB package inside Calamares' selected target chroot."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

def run(args,input=None):
    subprocess.run(args,input=input,text=True,check=True,timeout=300,env={**os.environ,'DEBIAN_FRONTEND':'noninteractive','LC_ALL':'C'})

def prepare(root,firmware,runner=run):
    root=Path(root)
    if firmware not in ('bios','efi'):raise ValueError('Unknown firmware mode: '+firmware)
    package='grub-efi-amd64' if firmware=='efi' else 'grub-pc'
    cache=root/'usr/share/macaque-bootloader';manifest=json.loads((cache/'manifest.json').read_text());item=manifest[package]
    filename=item['file']
    if Path(filename).name!=filename or not filename.endswith('.deb'):raise ValueError('Invalid cached package name')
    deb=cache/filename
    if hashlib.sha256(deb.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Cached GRUB package checksum mismatch')
    # The disk bootloader itself is installed later by Calamares on its chosen device.
    if firmware=='bios':runner(['/usr/bin/debconf-set-selections'],input='grub-pc grub-pc/install_devices multiselect \ngrub-pc grub-pc/install_devices_empty boolean true\n')
    runner(['/usr/bin/dpkg','--force-confdef','--force-confold','--install',str(deb)])
    (root/'boot/grub').mkdir(parents=True,exist_ok=True)
    grub=root/'etc/default/grub';grub.parent.mkdir(parents=True,exist_ok=True)
    if not grub.exists():grub.write_text('GRUB_DEFAULT=0\nGRUB_TIMEOUT=5\nGRUB_DISTRIBUTOR="Macaque Classic"\nGRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\nGRUB_CMDLINE_LINUX=""\n')
    # No apt download/update is performed here. Debian's installed packages
    # retain the normal GRUB kernel-update hooks after installation.
    print('Configured offline bootloader package:',package)

if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='--calamares-target':raise SystemExit('Run only inside the installer target chroot.')
    prepare('/',sys.argv[2])
