#!/usr/bin/python3
"""CI-only disposable disk test of installer helpers and the real desktop updater.
No host disk is selected: only a newly-created image attached by losetup is written.
This is not an automated Calamares GUI or physical laptop test.
"""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,time,stat,re
from pathlib import Path
KIT=Path(__file__).resolve().parent.parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def run(args,**kwargs):
 print('RUN',args,flush=True);return subprocess.run(args,check=True,timeout=600,**kwargs)
def boot(image,extra,log,marker):
 args=['qemu-system-x86_64','-machine','pc','-accel','tcg','-m','2048','-smp','2','-display','none','-serial','file:'+str(log),'-monitor','none','-nic','none','-no-reboot',
       '-drive','file='+str(image)+',format=raw,if=none,id=osdisk',
       '-device','ide-hd,drive=osdisk,bus=ide.0,unit='+('1' if extra else '0')+',bootindex=1']
 if extra:
  args+=['-drive','file='+str(extra)+',format=raw,if=none,id=other','-device','ide-hd,drive=other,bus=ide.0,unit=0,bootindex=2']
 log.write_bytes(b'')
 with log.with_suffix('.qemu.log').open('wb') as errors:
  process=subprocess.Popen(args,stdout=errors,stderr=subprocess.STDOUT)
  try:
   deadline=time.monotonic()+300
   while time.monotonic()<deadline:
    if marker.encode() in log.read_bytes():return True
    if process.poll() is not None:return False
    time.sleep(.5)
   return False
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
def partition_node(loop):
 if not re.fullmatch(r'/dev/loop[0-9]+',loop):raise ValueError('Expected our newly allocated loop disk.')
 part=Path(loop+'p1');sysdev=Path('/sys/class/block')/(Path(loop).name+'p1')/'dev'
 for _ in range(100):
  if sysdev.exists():break
  time.sleep(.1)
 major,minor=map(int,sysdev.read_text().strip().split(':'));device=os.makedev(major,minor)
 if part.exists():
  current=part.stat()
  if not stat.S_ISBLK(current.st_mode):raise RuntimeError('Unexpected non-block partition node.')
  # Loop partition minors are allocated dynamically and can change on reattach.
  if current.st_rdev!=device:part.unlink()
 if not part.exists():os.mknod(part,stat.S_IFBLK|0o600,device)
 return part
def test(source,out,package):
 if os.geteuid()!=0:raise RuntimeError('Run in the privileged disposable ISO builder.')
 source=Path(source).resolve();out=Path(out).resolve();package=Path(package).resolve()
 if source==Path('/') or not (source/'usr/share/macaque-build/manifest.txt').is_file():raise ValueError('Expected the ISO readback filesystem.')
 out.mkdir(parents=True,exist_ok=True)
 result={'fresh_bios_disk_boot':False,'desktop_update_applied':False,'updated_bios_disk_boot_with_second_drive':False,'calamares_gui_tested':False,'uefi_install_tested':False,'physical_hardware_tested':False}
 report=out/'installed-boot-check.json'
 with tempfile.TemporaryDirectory(prefix='installed-smoke-',dir=out) as temp:
  temp=Path(temp);image=temp/'installed.raw';extra=temp/'other.raw';target=temp/'root';target.mkdir();loop=None;mounted=False;uuid_alias=None
  with image.open('wb') as f:f.truncate(12*1024**3)
  with extra.open('wb') as f:f.truncate(16*1024**2)
  def attach():
   nonlocal loop,mounted,uuid_alias
   loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip()
   if not loop.startswith('/dev/loop') or not loop[9:].isdigit():raise RuntimeError('Unexpected newly allocated loop device.')
   part=partition_node(loop)
   uuid=subprocess.check_output(['blkid','-s','UUID','-o','value',str(part)],text=True).strip()
   uuid_alias=Path('/dev/disk/by-uuid')/uuid;uuid_alias.parent.mkdir(parents=True,exist_ok=True)
   if uuid_alias.exists() or uuid_alias.is_symlink():raise RuntimeError('Unexpected preexisting UUID alias for disposable filesystem.')
   uuid_alias.symlink_to(part)
   run(['mount',str(part),str(target)]);mounted=True
   for folder in ['dev','proc','sys','run','tmp']:(target/folder).mkdir(exist_ok=True)
   run(['mount','--rbind','/dev',str(target/'dev')]);run(['mount','--make-rslave',str(target/'dev')])
   run(['mount','-t','proc','proc',str(target/'proc')]);run(['mount','--rbind','/sys',str(target/'sys')]);run(['mount','--make-rslave',str(target/'sys')])
   return str(part)
  def detach():
   nonlocal loop,mounted,uuid_alias
   if mounted:
    run(['umount','-R',str(target)]);mounted=False
   if uuid_alias:uuid_alias.unlink(missing_ok=True);uuid_alias=None
   if loop:run(['losetup','--detach',loop]);loop=None
  try:
   loop=subprocess.check_output(['losetup','--find','--show',str(image)],text=True).strip()
   if not loop.startswith('/dev/loop') or not loop[9:].isdigit():raise RuntimeError('Unexpected loop device.')
   run(['sfdisk',loop],input='label: dos\nunit: sectors\n\nstart=2048,type=83,bootable\n',text=True)
   run(['losetup','--detach',loop]);loop=None
   # Map the freshly-created partition before formatting; no physical-device input exists.
   loop=subprocess.check_output(['losetup','--find','--show','--partscan',str(image)],text=True).strip()
   if not loop.startswith('/dev/loop') or not loop[9:].isdigit():raise RuntimeError('Unexpected loop device.')
   part=partition_node(loop)
   run(['mkfs.ext4','-F',str(part)])
   run(['mount',str(part),str(target)]);mounted=True
   run(['rsync','-aHAX','--exclude=/dev/***','--exclude=/proc/***','--exclude=/sys/***','--exclude=/run/***',str(source)+'/',str(target)+'/'])
   run(['umount',str(target)]);mounted=False;run(['losetup','--detach',loop]);loop=None
   part=attach()
   setup=load('installed_setup',KIT/'iso/installed-setup.py');setup.configure(target)
   uuid=subprocess.check_output(['blkid','-s','UUID','-o','value',part],text=True).strip()
   (target/'etc/fstab').write_text('UUID='+uuid+' / ext4 defaults 0 1\n')
   conf=target/'etc/default/grub.d/99-ci-serial.cfg';conf.parent.mkdir(parents=True,exist_ok=True)
   conf.write_text('GRUB_TIMEOUT=1\nGRUB_CMDLINE_LINUX_DEFAULT="console=ttyS0,115200n8 systemd.unit=multi-user.target"\n')
   unit=target/'etc/systemd/system/macaque-ci-ready.service'
   unit.write_text('[Unit]\nDescription=Disposable installed-disk boot check\nAfter=local-fs.target\n[Service]\nType=oneshot\nExecStart=/bin/sh -c "echo MACAQUE_INSTALLED_READY_$(cat /etc/macaque-ci-phase) > /dev/ttyS0"\n[Install]\nWantedBy=multi-user.target\n')
   wants=unit.parent/'multi-user.target.wants';wants.mkdir(exist_ok=True);(wants/unit.name).symlink_to('../'+unit.name)
   (target/'etc/macaque-ci-phase').write_text('fresh')
   run(['chroot',str(target),'/usr/bin/python3','/usr/local/libexec/macaque-offline-bootloader.py','--calamares-target','bios'])
   helper='/usr/local/libexec/macaque-grub-install'
   run(['chroot',str(target),'/usr/bin/python3',helper,'--target=i386-pc',loop])
   run(['chroot',str(target),'/usr/bin/python3',helper,'--finalize'])
   detach()
   result['fresh_bios_disk_boot']=boot(image,None,out/'installed-fresh.log','MACAQUE_INSTALLED_READY_fresh')
   if not result['fresh_bios_disk_boot']:raise RuntimeError('Fresh installed disk did not reach userspace; ISO publication is blocked.')
   attach()
   sys.path.insert(0,str(KIT/'desktop'))
   import update_backend
   name='macaque-classic_0.41_amd64.deb';url=update_backend.PREFIX+'v0.41-desktop-preview/'+name
   previous=update_backend.download({'name':name,'url':url,'checksum_url':url+'.sha256'},target/'tmp')
   updater='/opt/macaque-classic/maintenance.py'
   # Bootstrap a genuine older package through the same maintenance path, then upgrade it.
   run(['chroot',str(target),'/usr/bin/python3',updater,'install-desktop','/tmp/'+Path(previous['path']).name,previous['sha256']],input='Y\n',text=True)
   assert subprocess.check_output(['chroot',str(target),'dpkg-query','-W','-f=${Version}','macaque-classic'],text=True).strip()=='0.41'
   document=target/'home/macaque-update-test.txt';document.write_text('preserve this document\n')
   settings=target/'home/macaque-update-test.json';settings.write_text('{"mode":"dark","interface_font":"Classic"}\n')
   before=(document.read_bytes(),settings.read_bytes(),(target/'boot/grub/grub.cfg').read_bytes())
   shutil.copy2(package,target/'tmp/new-desktop.deb')
   digest=hashlib.sha256(package.read_bytes()).hexdigest()
   run(['chroot',str(target),'/usr/bin/python3',updater,'install-desktop','/tmp/new-desktop.deb',digest],input='Y\n',text=True)
   version=subprocess.check_output(['chroot',str(target),'dpkg-query','-W','-f=${Version}','macaque-classic'],text=True).strip()
   assert version=='0.41.2',version
   assert before==(document.read_bytes(),settings.read_bytes(),(target/'boot/grub/grub.cfg').read_bytes())
   assert 'title="Macaque Classic *' in (target/'etc/xdg/macaque/labwc/rc.xml').read_text()
   history=json.loads((target/'var/lib/macaque-classic/updates/history.json').read_text())
   assert history[-1]['version']==version and history[-1]['result']=='installed'
   result.update(desktop_update_applied=True,updated_version=version)
   (target/'etc/macaque-ci-phase').write_text('updated')
   detach()
   result['updated_bios_disk_boot_with_second_drive']=boot(image,extra,out/'installed-updated.log','MACAQUE_INSTALLED_READY_updated')
   if not result['updated_bios_disk_boot_with_second_drive']:raise RuntimeError('Updated disk failed the two-drive boot check; ISO publication is blocked.')
  finally:
   try:detach()
   finally:report.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: fresh installed BIOS disk boot, real 0.41 -> 0.41.2 package update, preserved documents/settings/GRUB menu, and updated two-drive BIOS boot.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('output');parser.add_argument('package');args=parser.parse_args()
 test(args.source,args.output,args.package)
