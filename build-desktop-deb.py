#!/usr/bin/env python3
"""Build a source-based desktop update package; does not install it or touch disks."""
import argparse,hashlib,re,shutil,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VERSION=re.search(r"VERSION=['\"]([^'\"]+)",(ROOT/'desktop/desktop.py').read_text())[1]
def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='macaque-deb-') as temp:
        root=Path(temp);dest=root/'opt/macaque-classic';shutil.copytree(ROOT/'desktop',dest,ignore=shutil.ignore_patterns('__pycache__','.venv','.git','*.so','*.so.*','*.pyc'))
        for wheel in (ROOT/'vendor').glob('chess-*.whl'):
            with zipfile.ZipFile(wheel) as z:z.extractall(dest)
        session=root/'usr/local/bin/macaque-session';session.parent.mkdir(parents=True);shutil.copy2(ROOT/'iso/macaque-session',session);session.chmod(0o755)
        import runpy
        runpy.run_path(str(ROOT/'iso/stage-wayland.py'))['stage'](root)
        control=root/'DEBIAN';control.mkdir()
        qt=[p for p in (ROOT/'iso/packages.txt').read_text().split() if p.startswith('python3-pyside6.')]
        dependencies=['python3','python3-pyte','python3-dbus','qt6-base-dev','g++','pkg-config','qt6-qpa-plugins','qt6-image-formats-plugins','network-manager','udisks2','lxpolkit','sudo','ca-certificates','labwc','greetd','gtkgreet','qt6-wayland','swayidle','swaylock','wlopm','foot','upower','dbus-user-session','libpam-systemd','libpam-modules','libpam-runtime','login','passwd','xdg-desktop-portal','xdg-desktop-portal-wlr','xdg-desktop-portal-gtk','slurp','grim','wireplumber',*qt]
        (control/'control').write_text('Package: macaque-classic\nVersion: '+VERSION+'\nArchitecture: amd64\nMaintainer: Drew Owen\nSection: x11\nPriority: optional\nDepends: '+', '.join(dependencies)+'\nDescription: Macaque Classic desktop and laptop controls\n Desktop update for an existing Macaque installation. Does not alter GRUB,\n disk partitions, the kernel, or user files. Native Control Strip builds\n against the installed Qt libraries during configuration.\n')
        scripts={'preinst':'''#!/bin/sh
set -eu
if [ -e /etc/macaque-live ]; then echo 'Install on a disk before updating the desktop.' >&2; exit 1; fi
if [ ! -f /etc/macaque-installed ] && { [ ! -f /opt/macaque-classic/desktop.py ] || { [ ! -f /usr/share/xsessions/macaque.desktop ] && [ ! -f /usr/share/wayland-sessions/macaque.desktop ]; }; }; then
 echo 'This desktop update requires an existing Macaque installation.' >&2; exit 1
fi
''','postinst':'''#!/bin/sh
set -eu
if [ "$1" = configure ]; then
 cd /opt/macaque-classic
 /usr/bin/python3 native/prepare.py
 g++ -std=c++17 -shared -fPIC -O2 $(pkg-config --cflags Qt6Widgets) native/embedded-strip.cpp $(pkg-config --libs Qt6Widgets) -o native/libclassic-strip-embedded.so.new
 mv native/libclassic-strip-embedded.so.new native/libclassic-strip-embedded.so
 if [ -f /etc/greetd/config.toml ] && [ ! -f /etc/greetd/config.toml.before-macaque ]; then
  cp -p /etc/greetd/config.toml /etc/greetd/config.toml.before-macaque
 fi
 if [ -f /etc/pam.d/greetd ] && [ ! -f /etc/pam.d/greetd.before-macaque ]; then
  cp -p /etc/pam.d/greetd /etc/pam.d/greetd.before-macaque
 fi
 install -m 644 /usr/share/macaque/greetd.pam /etc/pam.d/greetd
 install -m 644 /usr/share/macaque/greetd.toml /etc/greetd/config.toml
 if [ -d /run/systemd/system ]; then
  systemctl disable lightdm.service 2>/dev/null || true
  systemctl enable --force greetd.service
 fi
 echo 'Macaque Wayland installed. Save your work and reboot to use the new login/session.'
fi
''','postrm':'''#!/bin/sh
set -eu
case "$1" in remove|purge) rm -f /opt/macaque-classic/native/libclassic-strip-embedded.so /opt/macaque-classic/native/libclassic-strip-embedded.so.new ;; esac
'''}
        for name,text in scripts.items():p=control/name;p.write_text(text);p.chmod(0o755)
        for p in root.rglob('*'):
            if p.is_dir():p.chmod(0o755)
        hashes=[]
        for p in sorted(root.rglob('*')):
            if p.is_file() and 'DEBIAN' not in p.relative_to(root).parts:hashes.append(hashlib.md5(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root)))
        (control/'md5sums').write_text('\n'.join(hashes)+'\n')
        target=output/f'macaque-classic_{VERSION}_amd64.deb'
        subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(target)],check=True)
        (output/(target.name+'.sha256')).write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
        return target
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(ROOT/'packages'));args=parser.parse_args();print(build(args.output))
