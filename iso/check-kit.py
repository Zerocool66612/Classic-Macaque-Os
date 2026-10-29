"""Static/generation checks only. Does not claim to build or boot an ISO."""
import importlib.util,tempfile,subprocess,xml.etree.ElementTree as ET,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('prepare',root/'iso/prepare.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for name in ['build-iso.sh','iso/build-inside.sh','iso/0100-macaque.hook.chroot','iso/macaque-session','iso/cache-bootloader.sh']:
 subprocess.run(['bash','-n',str(root/name)],check=True)
ET.parse(root/'iso/openbox.xml')
subprocess.run(['python3',str(root/'iso/test_swap_helper.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_offline_installer.py')],check=True)
subprocess.run(['python3',str(root/'iso/test_startup.py')],check=True)
packages=set((root/'iso/packages.txt').read_text().split())
assert {'calamares','calamares-settings-debian','python3-pyside6.qttest','plymouth','plymouth-themes','lightdm-gtk-greeter','initramfs-tools'}<=packages
with tempfile.TemporaryDirectory() as temp:
 dest=Path(temp)/'image';module.prepare(dest)
 assert (dest/'opt/macaque-classic/desktop.py').exists()
 assert (dest/'usr/local/libexec/macaque-swap-helper.py').is_file()
 assert not list((dest/'opt/macaque-classic/native').glob('*.so'))
 assert (dest/'opt/macaque-classic/chess/__init__.py').exists()
 assert list((dest/'opt/macaque-classic').glob('chess-*.dist-info/*LICENSE*')) or list((dest/'opt/macaque-classic').glob('chess-*.dist-info/licenses/*'))
 assert 'autologin-user=macaque' in (dest/'etc/lightdm/lightdm.conf.d/50-macaque.conf').read_text()
 assert (dest/'usr/local/bin/macaque-session').stat().st_mode&0o111
 assert 'startup_welcome' in (dest/'etc/skel/.local/share/MacaqueOS/MacaqueClassic/desktop-state.json').read_text()
 try:module.prepare(dest)
 except SystemExit:pass
 else:raise AssertionError('Must refuse an occupied staging tree')
print('Build-kit generation and shell checks passed. ISO assembly and boot are untested.')
