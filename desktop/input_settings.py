#!/usr/bin/python3
"""Generate a user-owned labwc config; never edit system input devices directly."""
import json,os,sys,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
DEFAULT={'tap':True,'naturalScroll':False,'disableWhileTyping':True,'pointerSpeed':0.0}
def folder():return Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'macaque'
def values():
 try:return validate(json.loads((folder()/'touchpad.json').read_text()))
 except (OSError,ValueError,TypeError):return dict(DEFAULT)
def validate(data):
 if not isinstance(data,dict):raise ValueError("Touchpad settings must be an object.")
 result={}
 for key,default in DEFAULT.items():
  value=data.get(key,default)
  if key=='pointerSpeed':
   if type(value) not in (int,float) or not -1<=value<=1:raise ValueError('Pointer speed must be -1 to 1.')
  elif type(value) is not bool:raise ValueError('Touchpad switches must be true or false.')
  result[key]=value
 return result
def atomic(path,text):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.macaque-')
 try:
  with os.fdopen(fd,'w') as f:f.write(text)
  os.replace(temp,path)
 finally:Path(temp).unlink(missing_ok=True)
def render(source='/etc/xdg/macaque/labwc/rc.xml'):
 root=ET.parse(source).getroot();lib=root.find('libinput')
 if lib is None:lib=ET.SubElement(root,'libinput')
 for device in list(lib):
  if device.tag=='device' and device.get('category')=='touchpad':lib.remove(device)
 device=ET.SubElement(lib,'device',category='touchpad')
 for key,value in values().items():ET.SubElement(device,key).text=('yes' if value else 'no') if type(value) is bool else str(value)
 dest=folder()/'generated-labwc';dest.mkdir(parents=True,exist_ok=True);atomic(dest/'rc.xml',ET.tostring(root,encoding='unicode'));return dest
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--render':print(render(sys.argv[2]))
 else:raise SystemExit('Use --render SOURCE')
