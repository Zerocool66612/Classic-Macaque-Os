"""Theme asset and staging checks; never run grub-install or touch a real /boot."""
from pathlib import Path
import runpy,tempfile,re,subprocess
ROOT=Path(__file__).resolve().parent.parent
stage=runpy.run_path(str(ROOT/'iso/stage-grub.py'))
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)/'installed';stage['installed'](root)
 theme=root/'boot/grub/themes/macaque';text=(theme/'theme.txt').read_text()
 assert text.count('{')==text.count('}')
 assert '+ boot_menu {' in text and 'id = "__timeout__"' in text
 for filename in re.findall(r'(?:desktop-image:|file =)\s*"([^"]+)"',text):assert (theme/filename).is_file(),filename
 for pattern in re.findall(r'pixmap_style = "([^"]+)"',text):
  for side in ['nw','n','ne','w','c','e','sw','s','se']:assert (theme/pattern.replace('*',side)).is_file()
 conf=(root/'etc/default/grub.d/60-macaque-theme.cfg').read_text();assert 'GRUB_TIMEOUT=7' in conf and 'GRUB_THEME="/boot/grub/themes/macaque/theme.txt"' in conf
 assert 'GRUB_CMDLINE' not in conf and 'GRUB_GFXPAYLOAD' not in conf
 assert not (root/'boot/grub/grub.cfg').exists()
 config=Path(tmp)/'config';stage['live'](config);binary=config/'includes.binary'
 live=(binary/'boot/grub/theme.cfg').read_text();assert 'set theme=/boot/grub/themes/macaque/theme.txt' in live
 for path in ['isolinux','syslinux']:
  assert (binary/path/'splash.png').read_bytes().startswith(b'\x89PNG')
  assert 'menu rows 10' in (binary/path/'stdmenu.cfg').read_text()
 assert not (binary/'boot/grub/grub.cfg').exists() # Keep live-build's boot entries.
 for f in ['live-theme.cfg','60-macaque-theme.cfg']:subprocess.run(['bash','-n',str(ROOT/'iso/grub-theme'/f)],check=True)
 subprocess.run(['bash','-n',str(ROOT/'iso/install-grub-theme.sh')],check=True)
print('PASS: GRUB assets/nine-slice references, live UEFI and BIOS staging, installed config, retained generated boot entries, shell syntax. Firmware boot not tested.')
