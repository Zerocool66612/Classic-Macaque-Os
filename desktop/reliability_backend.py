#!/usr/bin/python3
"""Allowlisted user-session hardware operations; no shell or root fallback."""
import json,os,re,subprocess,sys,time,math,struct,wave,tempfile
from pathlib import Path

def run(args):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=15)
def native():
 if os.environ.get('MACAQUE_NATIVE_SESSION')!='1' or os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':raise ValueError('Use the installed/live Macaque session to change hardware.')
def audio_status():
 sinks=json.loads(run(['pactl','--format=json','list','sinks']));sources=json.loads(run(['pactl','--format=json','list','sources']))
 def item(x):
  volumes=[v.get('value_percent','0%') for v in x.get('volume',{}).values()];percent=round(sum(float(v.rstrip('%')) for v in volumes)/len(volumes)) if volumes else 0
  return {'name':x['name'],'description':x.get('description',x['name']),'muted':bool(x.get('mute',False)),'percent':max(0,min(100,percent))}
 return {'outputs':[item(x) for x in sinks],'inputs':[item(x) for x in sources if x.get('monitor_of_sink') in (None,4294967295,'4294967295')],'default_output':run(['pactl','get-default-sink']).strip(),'default_input':run(['pactl','get-default-source']).strip()}
def profiles():
 text=run(['powerprofilesctl','list']);choices=re.findall(r'^\s*\*?\s*(power-saver|balanced|performance):',text,re.M)
 return {'profiles':list(dict.fromkeys(choices)),'active':run(['powerprofilesctl','get']).strip(),'details':text}
def bluetooth(payload):
 import dbus
 bus=dbus.SystemBus();manager=dbus.Interface(bus.get_object('org.bluez','/'),'org.freedesktop.DBus.ObjectManager');objects=manager.GetManagedObjects();adapters=[str(p) for p,v in objects.items() if 'org.bluez.Adapter1' in v]
 if not adapters:raise ValueError('No Bluetooth adapter detected.')
 adapter=payload.get('adapter') or adapters[0]
 if adapter not in adapters:raise ValueError('Bluetooth adapter disappeared.')
 obj=bus.get_object('org.bluez',adapter);api=dbus.Interface(obj,'org.bluez.Adapter1');op=payload['action']
 if op=='bluetooth-power':
  if type(payload.get('enabled')) is not bool:raise ValueError('Choose Bluetooth on or off.')
  dbus.Interface(obj,'org.freedesktop.DBus.Properties').Set('org.bluez.Adapter1','Powered',dbus.Boolean(payload['enabled']))
 elif op=='bluetooth-scan':
  api.StartDiscovery()
  try:time.sleep(5)
  finally:api.StopDiscovery()
 elif op in ('bluetooth-connect','bluetooth-disconnect','bluetooth-forget'):
  path=payload.get('device');device=objects.get(path,{}).get('org.bluez.Device1')
  if not device or not str(path).startswith(adapter+'/'):raise ValueError('Choose a current device from this adapter.')
  if op=='bluetooth-forget':api.RemoveDevice(dbus.ObjectPath(path))
  else:
   if op=='bluetooth-connect' and not device.get('Paired',False):raise ValueError('Pair this device using Pair New Device first.')
   interface=dbus.Interface(bus.get_object('org.bluez',path),'org.bluez.Device1')
   getattr(interface,'Connect' if op=='bluetooth-connect' else 'Disconnect')(timeout=12)
 objects=manager.GetManagedObjects();devices=[]
 for path,values in objects.items():
  d=values.get('org.bluez.Device1')
  if d and str(path).startswith(adapter+'/'):devices.append({'path':str(path),'name':str(d.get('Alias',d.get('Name','Bluetooth device'))),'paired':bool(d.get('Paired',False)),'connected':bool(d.get('Connected',False))})
 return {'adapter':adapter,'powered':bool(objects[adapter]['org.bluez.Adapter1'].get('Powered',False)),'devices':devices}
def action(p):
 op=p['action']
 read_only=op in ('audio-status','profiles-status','display-status','touchpad-status','bluetooth-status')
 if not read_only:native()
 if op.startswith('bluetooth-'):return bluetooth(p)
 if op=='audio-status':return audio_status()
 if op in ('audio-output','audio-input','audio-input-volume','audio-input-mute'):
  info=audio_status();kind='outputs' if op=='audio-output' else 'inputs';name=p.get('name')
  if name not in [x['name'] for x in info[kind]]:raise ValueError('Choose an available audio device.')
  if op=='audio-input-volume':
   value=p.get('percent')
   if type(value) is not int or not 0<=value<=100:raise ValueError('Microphone level must be 0–100%.')
   run(['pactl','set-source-volume',name,str(value)+'%'])
  else:run(['pactl',{'audio-output':'set-default-sink','audio-input':'set-default-source','audio-input-mute':'set-source-mute'}[op],name,*(['toggle'] if op=='audio-input-mute' else [])])
  return {'message':'Audio device updated.'}
 if op=='audio-test':
  fd,name=tempfile.mkstemp(suffix='.wav');os.close(fd)
  try:
   with wave.open(name,'wb') as w:
    w.setparams((1,2,24000,0,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<h',int(1800*math.sin(2*math.pi*440*i/24000))) for i in range(14400)))
   run(['paplay',name]);return {'message':'Test tone played on the default output.'}
  finally:Path(name).unlink(missing_ok=True)
 if op=='profiles-status':return profiles()
 if op=='profile-set':
  if p.get('profile') not in profiles()['profiles']:raise ValueError('That power profile is not supported by this machine.')
  run(['powerprofilesctl','set',p['profile']]);return {'message':'Power profile changed.'}
 if op.startswith('touchpad-'):
  from input_settings import values,validate,atomic,folder,render
  if op=='touchpad-status':return values()
  if op!='touchpad-apply':raise ValueError('Unknown touchpad action.')
  atomic(folder()/'touchpad.json',json.dumps(validate(p['values'])));render();run(['labwc','--reconfigure']);return {'message':'Touchpad settings saved and compositor reloaded. They affect touchpads only.'}
 if op.startswith('display-'):
  import display_settings as d
  if op=='display-status':return {'outputs':d.status()}
  if op=='display-preview':return d.preview(p['value'])
  if op in ('display-keep','display-revert'):return d.finish(p['token'],op=='display-keep')
 raise ValueError('Unknown reliability request.')
if __name__=='__main__':
 try:print(json.dumps(action(json.loads(sys.stdin.read(32768)))))
 except Exception as ex:print(str(ex.output).strip() if isinstance(ex,subprocess.CalledProcessError) else str(ex),file=sys.stderr);sys.exit(1)
