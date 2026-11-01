"""Verify target preparation and bundled-branding invariants without touching disks."""
import importlib.util,tempfile,shutil,json,hashlib,yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('offline',ROOT/'iso/offline-bootloader.py');offline=importlib.util.module_from_spec(spec);spec.loader.exec_module(offline)
spec=importlib.util.spec_from_file_location('config',ROOT/'iso/configure-installer.py');config=importlib.util.module_from_spec(spec);spec.loader.exec_module(config)
for firmware,package in [('bios','grub-pc'),('efi','grub-efi-amd64')]:
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);cache=root/'usr/share/macaque-bootloader';cache.mkdir(parents=True);f=cache/(package+'_test_amd64.deb');f.write_bytes(b'fixture-only-not-a-deb')
  (cache/'manifest.json').write_text(json.dumps({package:{'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}}));commands=[]
  offline.prepare(root,firmware,lambda args,input=None:commands.append(args))
  assert (root/'etc/default/grub').exists() and (root/'boot/grub').is_dir();assert any(a[0]=='/usr/bin/dpkg' for a in commands);assert not any('apt' in a[0] for a in commands)
  f.write_bytes(b'corrupted');commands.clear()
  try:offline.prepare(root,firmware,lambda args,input=None:commands.append(args))
  except ValueError:pass
  else:raise AssertionError('Corrupt cached package accepted')
  assert not commands
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);base=root/'etc/calamares';mods=base/'modules';mods.mkdir(parents=True)
 sequence=['partition','mount','unpackfs','users','displaymanager','sources-media','bootloader-config','grubcfg','bootloader','packages','sources-media-unmount','sources-final','umount']
 (base/'settings.conf').write_text(yaml.safe_dump({'sequence':[{'exec':sequence}]}))
 for name,content in {'displaymanager':{},'users':{'passwordRequirements':{'libpwquality':['dictcheck=1','minlen=8']},'defaultGroups':['sudo']},'welcome':{'requirements':{}},'packages':{'backend':'apt','operations':[{'remove':['live-boot']}]},'bootloader':{'efiBootLoader':'grub'}}.items():(mods/(name+'.conf')).write_text(yaml.safe_dump(content))
 shutil.copytree(ROOT/'iso/branding',root/'usr/share/macaque-installer-branding');config.configure(root)
 d=yaml.safe_load((base/'settings.conf').read_text());seq=d['sequence'][0]['exec'];assert 'bootloader-config' not in seq and 'sources-media' not in seq and 'sources-final' not in seq
 assert seq.index('shellprocess')<seq.index('grubcfg')<seq.index('bootloader');assert d['prompt-install']
 commands=yaml.safe_load((mods/'shellprocess.conf').read_text());assert not commands['dontChroot'] and 'offline-bootloader' in commands['script'][1] and '${gs[firmwareType]}' in commands['script'][1]
 desc=yaml.safe_load((base/'branding/macaque/branding.desc').read_text());assert desc['strings']['productName']=='Macaque Classic' and (base/'branding/macaque'/desc['slideshow']).is_file()
 for f in desc['images'].values():assert (base/'branding/macaque'/f).is_file()
 assert 'debian-logo' not in str(desc)
 assert yaml.safe_load((mods/'partition.conf').read_text())['initialSwapChoice']=='none'
 assert yaml.safe_load((mods/'packages.conf').read_text())['update_db'] is False
 assert yaml.safe_load((mods/'bootloader.conf').read_text())['grubInstall']=='/usr/local/libexec/macaque-grub-install'
 users=yaml.safe_load((mods/'users.conf').read_text());assert users['passwordRequirements']=={'minLength':8,'maxLength':128}
 assert users['allowWeakPasswords'] is False and users['defaultGroups']==['sudo']
 finished=yaml.safe_load((mods/'finished.conf').read_text());assert finished['restartNowMode']=='user-unchecked' and finished['restartNowCommand']=='systemctl reboot'
 config.configure(root)
 assert yaml.safe_load((mods/'users.conf').read_text())['passwordRequirements']=={'minLength':8,'maxLength':128}
print('Offline BIOS/EFI package selection, checksum guards, job sequence and Macaque branding checks passed (mocked package install).')
