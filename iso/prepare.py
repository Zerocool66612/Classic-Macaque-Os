"""Create only the files included in the live image; no host configuration edits."""
from pathlib import Path
import shutil,sys,zipfile
ROOT=Path(__file__).resolve().parent.parent

def prepare(dest):
    dest=Path(dest)
    if dest.exists() and any(dest.iterdir()):raise SystemExit('Use an empty destination for image files.')
    shutil.copytree(ROOT/'desktop',dest/'opt/macaque-classic',ignore=shutil.ignore_patterns('__pycache__','.venv','.git','*.so','*.so.*'))
    for wheel in (ROOT/'vendor').glob('chess-*.whl'):
        with zipfile.ZipFile(wheel) as z:z.extractall(dest/'opt/macaque-classic')
    def write(path,text,mode=0o644):
        f=dest/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text);f.chmod(mode)
    shutil.copytree(ROOT/'iso/branding',dest/'usr/share/macaque-installer-branding')
    write('usr/local/libexec/macaque-grub-install',(ROOT/'iso/grub-install-checked.py').read_text(),0o755)
    startup=ROOT/'iso/startup'
    shutil.copytree(startup/'plymouth',dest/'usr/share/plymouth/themes/macaque')
    write('usr/share/plymouth/themes/macaque/macaque.plymouth',(startup/'macaque.plymouth').read_text())
    write('usr/share/plymouth/themes/macaque/macaque.script',(startup/'macaque.script').read_text())
    write('usr/share/themes/Macaque Platinum/gtk-3.0/gtk.css',(startup/'gtk.css').read_text())
    write('etc/lightdm/lightdm-gtk-greeter.conf',(startup/'lightdm-gtk-greeter.conf').read_text())
    write('etc/lightdm/lightdm.conf.d/40-macaque-greeter.conf','[Seat:*]\ngreeter-session=lightdm-gtk-greeter\n')
    for source,target in [('login.png','usr/share/backgrounds/macaque-login.png'),('user.png','usr/share/pixmaps/macaque-user.png')]:
        f=dest/target;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(startup/source,f)
    write('etc/default/grub.d/50-macaque-splash.cfg','GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"\nGRUB_DISTRIBUTOR="Macaque Classic"\n')

    write('usr/local/libexec/macaque-offline-bootloader.py',(ROOT/'iso/offline-bootloader.py').read_text(),0o755)
    write('usr/local/libexec/macaque-cache-bootloader.sh',(ROOT/'iso/cache-bootloader.sh').read_text(),0o755)
    write('usr/local/libexec/macaque-swap-helper.py',(ROOT/'iso/swap-helper.py').read_text(),0o755)
    write('etc/macaque-live','Macaque installer live preview\n')
    write('usr/local/libexec/macaque-installed-setup.py',(ROOT/'iso/installed-setup.py').read_text(),0o755)
    write('usr/local/libexec/macaque-configure-installer.py',(ROOT/'iso/configure-installer.py').read_text(),0o755)
    write('usr/local/bin/macaque-session',(ROOT/'iso/macaque-session').read_text(),0o755)
    write('etc/xdg/macaque/openbox.xml',(ROOT/'iso/openbox.xml').read_text())
    write('usr/share/xsessions/macaque.desktop','[Desktop Entry]\nName=Macaque Classic\nComment=Classic desktop live preview\nExec=/usr/local/bin/macaque-session\nType=Application\nDesktopNames=Macaque\n')
    write('etc/lightdm/lightdm.conf.d/50-macaque.conf','[Seat:*]\nautologin-user=macaque\nautologin-user-timeout=0\nautologin-session=macaque\nuser-session=macaque\n')
    write('etc/skel/.local/share/MacaqueOS/MacaqueClassic/desktop-state.json','{"startup_welcome":true,"startup_files":true,"startup_notes":false,"mode":"dark"}\n')
    write('usr/share/macaque-build/README.txt',(ROOT/'README.md').read_text())
    write('usr/share/macaque-build/checks.log','Checks have not run yet. The chroot hook replaces this file.\n')
if __name__=='__main__':prepare(sys.argv[1])
