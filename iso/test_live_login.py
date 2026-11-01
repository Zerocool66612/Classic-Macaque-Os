"""Account operations are mocked; no host accounts or services are changed."""
import importlib.util,tempfile,types,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('live_login',ROOT/'iso/live-login.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);(root/'etc').mkdir();(root/'proc').mkdir();(root/'proc/cmdline').write_text('boot=live quiet');calls=[]
 def run(args,**kw):calls.append((args,kw))
 user=types.SimpleNamespace(pw_uid=1000,pw_dir='/home/macaque')
 try:m.prepare(root,run,lambda _:user)
 except ValueError:pass
 else:raise AssertionError('Installed target accepted')
 assert not calls
 (root/'etc/macaque-live').touch();m.prepare(root,run,lambda _:user)
 assert calls[0][0]==['chpasswd'] and calls[0][1]['input']=='macaque:live\n'
 calls.clear();(root/'proc/cmdline').write_text('quiet')
 try:m.prepare(root,run,lambda _:user)
 except ValueError:pass
 else:raise AssertionError('Non-live boot accepted')
 assert not calls
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)/'image';runpy.run_path(str(ROOT/'iso/prepare.py'))['prepare'](root)
 assert 'Restart=no' in (root/'etc/systemd/system/greetd.service.d/50-macaque-live.conf').read_text()
 assert '--autologin macaque' in (root/'etc/systemd/system/getty@tty2.service.d/50-macaque-live.conf').read_text()
 assert (root/'etc/systemd/system/getty.target.wants/getty@tty2.service').is_symlink()
 pam=(root/'etc/pam.d/greetd').read_text();assert '@include common-auth' in pam and 'pam_permit.so' not in pam and '@include login' not in pam
 runpy.run_path(str(ROOT/'iso/installed-setup.py'))['configure'](root)
 for name in ['greetd.service.d/50-macaque-live.conf','getty@tty2.service.d/50-macaque-live.conf','macaque-live-login.service']:
  assert not (root/'etc/systemd/system'/name).exists()
 assert not (root/'etc/systemd/system/getty.target.wants/getty@tty2.service').is_symlink()
 assert not (root/'usr/local/libexec/macaque-live-login').exists()
 assert '@include common-auth' in (root/'etc/pam.d/greetd').read_text()
print('Live-only account guards, startup ordering, PAM policy and installed recovery cleanup passed (account operations mocked).')
