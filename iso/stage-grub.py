"""Stage artwork/configuration only; never install a bootloader or touch disks."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'grub-theme'
def theme(dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    for p in ASSETS.iterdir():
        if p.suffix=='.png' or p.name=='theme.txt':shutil.copy2(p,dest/p.name)
def installed(root):
    root=Path(root);theme(root/'boot/grub/themes/macaque')
    conf=root/'etc/default/grub.d/60-macaque-theme.cfg';conf.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ASSETS/conf.name,conf)
def live(config):
    config=Path(config);binary=config/'includes.binary';theme(binary/'boot/grub/themes/macaque')
    shutil.copy2(ASSETS/'live-theme.cfg',binary/'boot/grub/theme.cfg')
    # BIOS retains Debian's generated menu, kernel arguments and utility entries.
    for folder in ['isolinux','syslinux']:
        dest=binary/folder;dest.mkdir(parents=True,exist_ok=True);shutil.copy2(ASSETS/'bios-splash.png',dest/'splash.png')
        (dest/'stdmenu.cfg').write_text('''menu background splash.png
menu color title * #ffffffff #00000000 none
menu color border * #00000000 #00000000 none
menu color unsel * #ffe4eded #00000000 none
menu color sel * #ffffffff #ff367b9c none
menu color hotsel * #ffffffff #ff367b9c none
menu color hotkey * #ffffffff #00000000 none
menu color tabmsg * #ffe0eeee #00000000 none
menu color timeout_msg * #ffe0eeee #00000000 none
menu color timeout * #ffffffff #00000000 none
menu margin 8
menu vshift 10
menu rows 10
menu helpmsgrow 23
menu cmdlinerow 24
menu timeoutrow 25
menu tabmsgrow 26
menu tabmsg Arrow keys: select   ENTER: start   TAB: edit
''')
if __name__=='__main__':
    import sys
    if len(sys.argv)!=3 or sys.argv[1] not in ('live','installed'):raise SystemExit('Usage: stage-grub.py live|installed DEST')
    globals()[sys.argv[1]](sys.argv[2])
