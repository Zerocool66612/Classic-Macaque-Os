"""Check startup/login integration without touching host services or authenticating."""
import importlib.util, tempfile, configparser, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'iso'/f'{name}.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)/'image';load('prepare').prepare(root)
 cfg=configparser.ConfigParser(interpolation=None);cfg.read(root/'etc/lightdm/lightdm-gtk-greeter.conf');g=cfg['greeter']
 assert g['user-background']=='false'
 for key in ['background','default-user-image']:assert (root/g[key].lstrip('/')).is_file()
 assert (root/'usr/share/themes'/g['theme-name']/'gtk-3.0/gtk.css').is_file()
 assert '~power' in g['indicators'] and '~a11y' in g['indicators'] and '~layout' in g['indicators']
 theme=root/'usr/share/plymouth/themes/macaque';cfg.read(theme/'macaque.plymouth');assert cfg['Plymouth Theme']['ModuleName']=='script'
 script=(theme/'macaque.script').read_text()
 for asset in re.findall(r'Image\("([^"]+)"\)',script):assert (theme/asset).is_file()
 for fn in ['SetBootProgressFunction','SetDisplayPasswordFunction','SetDisplayQuestionFunction']:assert fn in script
 load('installed-setup').configure(root)
 assert not (root/'etc/lightdm/lightdm.conf.d/50-macaque.conf').exists()
 assert 'greeter-session=lightdm-gtk-greeter' in (root/'etc/lightdm/lightdm.conf.d/40-macaque-greeter.conf').read_text()
 assert 'splash' in (root/'etc/default/grub.d/50-macaque-splash.cfg').read_text()
 assert (root/'etc/lightdm/lightdm-gtk-greeter.conf').is_file()
 assert (theme/'startup.png').is_file()
print('Boot artwork references, login configuration and installed-theme preservation checks passed.')
