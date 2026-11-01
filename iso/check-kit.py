"""Static/generation checks only. Does not claim to build or boot an ISO."""
import importlib.util,tempfile,subprocess,xml.etree.ElementTree as ET,hashlib,os,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('prepare',root/'iso/prepare.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for name in ['build-iso.sh','iso/build-inside.sh','iso/0100-macaque.hook.chroot','iso/macaque-session','iso/cache-bootloader.sh']:
 subprocess.run(['bash','-n',str(root/name)],check=True)
ET.parse(root/'iso/wayland/labwc/rc.xml')
ET.parse(root/'iso/wayland/greeter/rc.xml')
subprocess.run(['python3',str(root/'iso/test_swap_helper.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_offline_installer.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_startup.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_live_login.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_installer_monitor.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_boot_check.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_wayland_session.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_bootloader_checked.py')],check=True)
packages=set((root/'iso/packages.txt').read_text().split())
assert {'calamares','calamares-settings-debian','python3-pyside6.qttest','plymouth','plymouth-themes','gtkgreet','initramfs-tools','python3-dbus','udisks2','labwc','qt6-wayland','greetd','lxpolkit','swaylock','swayidle','wlopm'}<=packages
with tempfile.TemporaryDirectory() as temp:
 dest=Path(temp)/'image';module.prepare(dest)
 assert (dest/'opt/macaque-classic/desktop.py').exists()
 desktop=dest/'opt/macaque-classic'
 assert (desktop/'labwc-rc.xml').read_bytes()==(dest/'etc/xdg/macaque/labwc/rc.xml').read_bytes()
 subprocess.run([sys.executable,str(desktop/'test_creative.py')],cwd=desktop,env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),check=True)
 assert (dest/'usr/local/libexec/macaque-swap-helper.py').is_file()
 assert not list((dest/'opt/macaque-classic/native').glob('*.so'))
 assert (dest/'opt/macaque-classic/chess/__init__.py').exists()
 assert list((dest/'opt/macaque-classic').glob('chess-*.dist-info/*LICENSE*')) or list((dest/'opt/macaque-classic').glob('chess-*.dist-info/licenses/*'))
 assert '[initial_session]' in (dest/'etc/greetd/config.toml').read_text()
 assert not (dest/'etc/lightdm').exists()
 assert (dest/'usr/local/bin/macaque-session').stat().st_mode&0o111
 assert 'startup_welcome' in (dest/'etc/skel/.local/share/MacaqueOS/MacaqueClassic/desktop-state.json').read_text()
 try:module.prepare(dest)
 except SystemExit:pass
 else:raise AssertionError('Must refuse an occupied staging tree')
print('Build-kit generation and shell checks passed. ISO assembly and boot are untested.')
