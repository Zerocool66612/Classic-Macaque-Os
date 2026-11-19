"""GRUB target selection, fresh UUID validation, finalization and refusal gates."""
import tempfile,importlib.util,json,subprocess
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('checked',Path(__file__).with_name('grub-install-checked.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cmd=m.checked_args(['--target=i386-pc','--force','/dev/example'])
assert '--force' not in cmd and '--boot-directory=/boot' in cmd and cmd[-1]=='/dev/example'
assert any(a.startswith('--modules=') and 'search_fs_uuid' in a for a in cmd)
with patch.object(m,'output',return_value=json.dumps({'blockdevices':[{'name':'/dev/example1','type':'part','children':[{'name':'/dev/example','type':'disk'}]}]})):
 assert m.bios_install_target(['--target=i386-pc','/dev/example'],'/dev/example1')=='/dev/example'
 for args in [['--target=i386-pc','/dev/other'],['--target=i386-pc','/dev/example1'],['--target=i386-pc']]:
  try:m.bios_install_target(args,'/dev/example1')
  except RuntimeError:pass
  else:raise AssertionError('Unsafe or missing BIOS disk accepted')
for bad in [False,True]:
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp)
  for name,data in {'etc/macaque-installed':'target','boot/vmlinuz-test':'kernel','boot/initrd.img-test':'initramfs','boot/grub/device.map':'stale','boot/grub/i386-pc/normal.mod':'module','boot/grub/grub.cfg':"menuentry 'Macaque' {\n search --fs-uuid "+('old' if bad else 'new-uuid')+';\n linux /boot/vmlinuz-test root=UUID='+('old' if bad else 'new-uuid')+' ro\n}\n'}.items():
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
  (root/'dev/example').parent.mkdir(parents=True,exist_ok=True);(root/'dev/example').touch()
  commands=[]
  def probe(args):
   assert not (root/'boot/grub/device.map').exists()
   if '--output' in args:return 'disk'
   if '--target=device' in args:return '/dev/example1'
   return 'new-uuid'
  with patch.object(m,'Path',lambda p:root/str(p).lstrip('/')),patch.object(m,'output',side_effect=probe),patch.object(m,'physical_disks',return_value={'/dev/example'}),patch.object(m.os.path,'realpath',side_effect=lambda p:p),patch.object(m.os,'geteuid',return_value=0),patch.object(m.subprocess,'run',side_effect=lambda a,**kw:(commands.append(a) or subprocess.CompletedProcess(a,0,'',''))):
   try:m.main(['--target=i386-pc','--force','/dev/example'])
   except RuntimeError:assert bad
   else:assert not bad
  assert commands[0]==cmd
  assert commands[1]==['/usr/sbin/update-grub']
  if bad:assert len(commands)==2
  else:
   assert commands[2]==['/usr/bin/debconf-set-selections'] and commands[-1]==['/bin/sync']
  report=json.loads((root/'var/log/macaque-bootloader.json').read_text())
  assert (report['status']=='failed')==bad and report['install_device']=='/dev/example'
  assert (root/'boot/grub/device.map.before-macaque-install').read_text()=='stale'
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);p=root/'var/log/macaque-bootloader.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'arguments':['--target=i386-pc','/dev/example']}))
  with patch.object(m,'Path',lambda p:root/str(p).lstrip('/')),patch.object(m,'main') as main:
   m.finalize();main.assert_called_once_with(['--target=i386-pc','/dev/example'])
print('PASS: whole-disk selection, stale-map removal before probes, generated menu before fresh core, remembered update target and final-job argument reuse. Disk writes mocked.')
