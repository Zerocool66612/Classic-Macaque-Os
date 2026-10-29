#!/bin/sh
set -eu
cache=/usr/share/macaque-bootloader
mkdir -p "$cache"
pc_version=$(dpkg-query -W -f='${Version}' grub-pc-bin)
efi_version=$(dpkg-query -W -f='${Version}' grub-efi-amd64-bin)
cd "$cache"
apt-get download "grub-pc=$pc_version" "grub-efi-amd64=$efi_version"
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
cache=Path('/usr/share/macaque-bootloader');manifest={}
for name in ['grub-pc','grub-efi-amd64']:
    files=list(cache.glob(name+'_*.deb'))
    assert len(files)==1,(name,files)
    f=files[0];actual=subprocess.check_output(['dpkg-deb','-f',str(f),'Package'],text=True).strip();assert actual==name
    manifest[name]={'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(cache/'manifest.json').write_text(json.dumps(manifest,indent=2))
PY
# Fail the build if the offline prerequisites are missing.
test -x /usr/sbin/grub-install
test -x /usr/sbin/grub-mkconfig
test -f /usr/lib/grub/i386-pc/modinfo.sh
test -f /usr/lib/grub/x86_64-efi/modinfo.sh
dpkg-query -W -f='${Status}\n' grub-common grub2-common ucf cryptsetup-initramfs
