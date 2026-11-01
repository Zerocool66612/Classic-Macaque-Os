"""Validate service boundaries and filesystem actions without real hardware writes."""
import json,tempfile,subprocess,sys
from pathlib import Path
from unittest.mock import patch
import removable_backend as usb
from wifi_backend import validate
from power_backend import settings_commands,backlights
from update_backend import releases,download,PREFIX
from maintenance import metadata,digest,installed_target
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);assert not installed_target(root);(root/'etc').mkdir();(root/'etc/macaque-installed').touch();assert installed_target(root);(root/'etc/macaque-live').touch();assert not installed_target(root)
assert validate({'ssid':'Cafe:North','security':'wpa-psk','password':'abcdefgh','interface':'wlan0'})[:2]==('Cafe:North','wpa-psk')
for payload in [{'ssid':''},{'ssid':'A'*33},{'ssid':'Cafe','security':'enterprise'},{'ssid':'Cafe','security':'wpa-psk','password':'short'}]:
 try:validate(payload)
 except ValueError:pass
 else:raise AssertionError('Invalid Wi-Fi credentials accepted')
node={'name':'/dev/testusb1','path':'/dev/testusb1','type':'part','fstype':'vfat','label':'Camera','size':100000,'uuid':'test-uuid','maj:min':'8:17','mountpoints':[None]}
disk={'name':'/dev/testusb','path':'/dev/testusb','type':'disk','tran':'usb','rm':False,'model':'Fixture USB','maj:min':'8:16','children':[node]}
raw={'blockdevices':[disk]};items=usb.removable(raw);assert len(items)==1;volume=items[0]['volumes'][0];commands=[]
usb.action({**volume,'action':'mount'},lambda:items,lambda args,**kw:commands.append(args));assert commands==[['udisksctl','mount','--block-device','/dev/testusb1']]
for mount in ['/','/boot','/boot/efi','/home','/run/live/medium','[SWAP]']:
 node['mountpoints']=[mount];assert not usb.removable(raw)
node['mountpoints']=[None]
try:usb.action({**volume,'identity':'8:99','action':'mount'},lambda:items,lambda *a,**k:(_ for _ in ()).throw(AssertionError('Unexpected command')))
except ValueError:pass
else:raise AssertionError('Changed device accepted')
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);media=root/'USB';media.mkdir();local=root/'Macaque HD';(local/'Documents').mkdir(parents=True);(media/'photo.txt').write_text('photo')
 node['mountpoints']=[str(media)];items=usb.removable(raw);volume=items[0]['volumes'][0]
 usb.action({**volume,'action':'import','source':str(media/'photo.txt'),'local_root':str(local)},lambda:items);assert (local/'Documents/photo.txt').read_text()=='photo'
 usb.action({**volume,'action':'import','source':str(media/'photo.txt'),'local_root':str(local)},lambda:items);assert (local/'Documents/photo 2.txt').exists()
 (local/'Documents/export.txt').write_text('export');usb.action({**volume,'action':'export','source':str(local/'Documents/export.txt'),'local_root':str(local)},lambda:items);assert (media/'export.txt').read_text()=='export'
 (media/'outside-link').symlink_to(local/'Documents/export.txt')
 try:usb.action({**volume,'action':'import','source':str(media/'outside-link'),'local_root':str(local)},lambda:items)
 except ValueError:pass
 else:raise AssertionError('Symlink import accepted')
 try:usb.action({**volume,'action':'import','source':str(local/'Documents/export.txt'),'local_root':str(local)},lambda:items)
 except ValueError:pass
 else:raise AssertionError('Import outside volume accepted')
 # Busy media must never reach power-off; no --force is used.
 calls=[]
 def busy(args,**kw):calls.append(args);raise subprocess.CalledProcessError(1,args,stderr='busy')
 try:usb.action({**volume,'action':'eject'},lambda:items,busy)
 except subprocess.CalledProcessError:pass
 assert len(calls)==1 and 'power-off' not in calls[0] and '--force' not in calls[0]
 # Successful ejection rechecks that every volume became unmounted.
 current=json.loads(json.dumps(items))
 def unmount(args,**kw):
  calls.append(args)
  if 'unmount' in args:current[0]['volumes'][0]['mounts']=[]
 calls=[];usb.action({**volume,'action':'eject'},lambda:current,unmount);assert calls[-1]==['udisksctl','power-off','--block-device','/dev/testusb']
values={'blank_ac':10,'blank_battery':5,'dim_ac':120,'dim_battery':60,'lid_ac':0,'lid_battery':1}
assert len(settings_commands(values))==8
for key,value in [('dim_ac',0),('lid_ac',2),('blank_ac',121),('dim_ac','60')]:
 try:settings_commands({**values,key:value})
 except ValueError:pass
 else:raise AssertionError('Unsafe power value accepted')
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'fixture';p.mkdir();(p/'max_brightness').write_text('1000');(p/'brightness').write_text('400');assert backlights(temp)[0]['percent']==40
asset='macaque-classic_0.29_amd64.deb';url=PREFIX+'v0.29-preview/'+asset
fixtures=[{'tag_name':'v0.29-preview','prerelease':True,'assets':[{'name':asset,'browser_download_url':url},{'name':asset+'.sha256','browser_download_url':url+'.sha256'}]}]
assert len(releases(fixtures))==1
fixtures[0]['assets'][0]['browser_download_url']='https://example.org/evil.deb';assert releases(fixtures)==[]
package=Path(__file__).resolve().parent.parent/'packages'/asset
if package.exists():
 assert metadata(package)['version']=='0.29'
 with tempfile.TemporaryDirectory() as temp:
  item={'name':asset,'url':url,'checksum_url':url+'.sha256'}
  checksum=(digest(package)+'  '+asset+'\n').encode()
  with patch('update_backend.read_url',side_effect=lambda u,n:checksum if u.endswith('.sha256') else package.read_bytes()):
   result=download(item,temp);assert digest(result['path'])==digest(package)
  with patch('update_backend.read_url',side_effect=lambda u,n:checksum if u.endswith('.sha256') else b'corrupted'):
   try:download(item,temp)
   except ValueError:pass
   else:raise AssertionError('Corrupted desktop download accepted')
print('Wi-Fi validation, removable-system guards/import/export/busy eject, power validation and update checksum tests passed; system writes mocked.')
