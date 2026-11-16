"""Preflight the disposable-loop reattachment used by installed boot CI."""
import os,runpy,subprocess,tempfile
from pathlib import Path
node=runpy.run_path(str(Path(__file__).with_name('test-installed-boot.py')))['partition_node']
def run(args,**kw):return subprocess.run(args,check=True,timeout=30,**kw)
if os.geteuid()!=0:raise SystemExit('Run only in the disposable privileged builder.')
with tempfile.TemporaryDirectory(prefix='macaque-loop-preflight-') as temp:
 root=Path(temp);image=root/'test.raw';mount=root/'mount';mount.mkdir()
 with image.open('wb') as f:f.truncate(96*1024**2)
 loop=None;mounted=False
 try:
  loop=subprocess.check_output(['losetup','--find','--show',str(image)],text=True).strip()
  run(['sfdisk',loop],input='label: dos\n\nstart=2048,type=83\n',text=True)
  run(['losetup','--detach',loop]);loop=None
  for index in range(4):
   loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip();part=node(loop)
   if index==0:run(['mkfs.ext4','-F',str(part)])
   run(['mount',str(part),str(mount)]);mounted=True
   if index==0:(mount/'check.txt').write_text('loop reattach fixture')
   assert (mount/'check.txt').read_text()=='loop reattach fixture'
   run(['umount',str(mount)]);mounted=False
   run(['losetup','--detach',loop]);loop=None
 finally:
  if mounted:run(['umount',str(mount)])
  if loop:run(['losetup','--detach',loop])
print('PASS: freshly allocated disposable disk mounts correctly across four detach/reattach cycles.')
