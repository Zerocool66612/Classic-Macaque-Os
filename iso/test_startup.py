"""Check boot artwork and native Wayland login staging without host mutations."""
import importlib.util,tempfile,configparser,re,tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'iso'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)/'image';load('prepare').prepare(root)
 config=root/'etc/greetd/config.toml';cfg=tomllib.loads(config.read_text())
 assert cfg['default_session']['user']=='_greetd' and cfg['initial_session']['user']=='macaque'
 assert (root/'usr/local/bin/macaque-greeter').is_file()
 assert (root/'usr/share/wayland-sessions/macaque.desktop').is_file()
 assert not (root/'etc/lightdm').exists() and not (root/'usr/share/xsessions').exists()
 theme=root/'usr/share/plymouth/themes/macaque';ini=configparser.ConfigParser();ini.read(theme/'macaque.plymouth');assert ini['Plymouth Theme']['ModuleName']=='script'
 script=(theme/'macaque.script').read_text()
 for asset in re.findall(r'Image\("([^"]+)"\)',script):assert (theme/asset).is_file()
 for fn in ['SetBootProgressFunction','SetDisplayPasswordFunction','SetDisplayQuestionFunction']:assert fn in script
 load('installed-setup').configure(root)
 assert 'initial_session' not in tomllib.loads(config.read_text())
 assert (root/'etc/systemd/system/display-manager.service').readlink()==Path('/usr/lib/systemd/system/greetd.service')
 assert (root/'etc/macaque-installed').is_file() and not (root/'etc/macaque-live').exists()
 assert 'splash' in (root/'etc/default/grub.d/50-macaque-splash.cfg').read_text()
 assert (root/'usr/share/backgrounds/macaque-login.png').is_file()
print('Boot artwork, Wayland greeter staging, live-only autologin removal and installed login checks passed.')
