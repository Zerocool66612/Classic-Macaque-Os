"""Exercise install sequencing and failure gates with a temporary target and mocked GRUB."""
import tempfile,importlib.util,json
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('checked',Path(__file__).with_name('grub-install-checked.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.checked_args(['--target=i386-pc','--force','/dev/example'])==['/usr/sbin/grub-install','--recheck','--target=i386-pc','/dev/example']
for text in ['menuentry test { root=old-uuid; }','root=new-uuid']:
 try:m.verify_config(text,'new-uuid')
 except RuntimeError:pass
 else:raise AssertionError('Invalid boot menu accepted')
for bad in [False,True]:
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp)
  for name,data in {'etc/macaque-installed':'target','boot/vmlinuz-test':'kernel','boot/initrd.img-test':'initramfs','boot/grub/device.map':'stale','boot/grub/i386-pc/normal.mod':'module','boot/grub/grub.cfg':"menuentry 'Macaque' { search --fs-uuid "+('old' if bad else 'new-uuid')+'; }'}.items():
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
  commands=[]
  with patch.object(m,'Path',lambda p:root/str(p).lstrip('/')),patch.object(m,'output',return_value='new-uuid'),patch.object(m.os,'geteuid',return_value=0),patch.object(m.subprocess,'run',side_effect=lambda a,**kw:commands.append(a)):
   try:m.main(['--target=i386-pc','--force','/dev/example'])
   except RuntimeError:
    assert bad
   else:assert not bad
  assert commands[0]==['/usr/sbin/grub-install','--recheck','--target=i386-pc','/dev/example']
  assert commands[1]==['/usr/sbin/update-grub']
  assert (root/'boot/grub/device.map.before-macaque-install').read_text()=='stale'
  report=json.loads((root/'var/log/macaque-bootloader.json').read_text());assert (report['status']=='failed')==bad
print('GRUB fresh-probe arguments, configuration regeneration, UUID failure gates and diagnostic-report tests passed (disk writes mocked).')
