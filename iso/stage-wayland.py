"""Stage files only; never change the build host's display manager."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
def stage(dest,live=False):
    dest=Path(dest)
    def put(target,source,mode=0o644):
        p=dest/target;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,p);p.chmod(mode)
    for name in ['macaque-greeter','macaque-greeter-client','macaque-lock','macaque-action']:
        put('usr/local/bin/'+name,'wayland/'+name,0o755)
    put('etc/xdg/macaque/labwc/rc.xml','../desktop/labwc-rc.xml')
    put('etc/xdg/macaque/greeter/rc.xml','wayland/greeter/rc.xml')
    put('usr/share/themes/Macaque Platinum/openbox-3/themerc','wayland/themerc')
    put('usr/share/themes/Macaque Platinum/gtk-3.0/gtk.css','startup/gtk.css')
    put('usr/share/backgrounds/macaque-login.png','startup/login.png')
    put('etc/greetd/macaque.css','wayland/macaque.css')
    # Keep the package's greetd config as a conffile, and generate our config
    # explicitly at migration time. Fresh live images can use it immediately.
    config=(ROOT/'wayland/config.toml').read_text()
    target=dest/('etc/greetd/config.toml' if live else 'usr/share/macaque/greetd.toml')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(config+('\n[initial_session]\ncommand = "/usr/local/bin/macaque-session"\nuser = "macaque"\n' if live else ''))
    put('etc/xdg/xdg-desktop-portal/macaque-portals.conf','wayland/portals.conf')
    entry=dest/'usr/share/wayland-sessions/macaque.desktop';entry.parent.mkdir(parents=True,exist_ok=True)
    entry.write_text('[Desktop Entry]\nName=Macaque Classic (Wayland)\nExec=/usr/local/bin/macaque-session\nType=Application\nDesktopNames=Macaque;wlroots\n')
