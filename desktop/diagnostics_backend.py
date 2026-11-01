#!/usr/bin/python3
"""Bounded, local-only support bundle. Never collects credentials or uploads data."""
import json,os,re,subprocess,sys,tempfile,time,zipfile,platform
from pathlib import Path
LIMIT=48000

def redact(text):
 text=re.sub(r'(?im)^.*(?:password|passwd|psk|secret|token|authorization)\s*[:=].*$', '[credential-like line omitted]',text)
 text=re.sub(r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b','[device address]',text)
 text=re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b','[IP address]',text)
 home=str(Path.home())
 if home!='/':text=text.replace(home,'[home]')
 return text

def tail(path):
 try:
  with Path(path).open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-LIMIT));return redact(f.read(LIMIT).decode(errors='replace'))
 except OSError as ex:return 'Unavailable: '+str(ex)
def command(args):
 try:r=subprocess.run(args,capture_output=True,text=True,timeout=8);return redact((r.stdout+r.stderr)[-LIMIT:])
 except (OSError,subprocess.SubprocessError) as ex:return 'Unavailable: '+str(ex)
def installer():
 p=Path('/var/log/macaque-installer/last.json')
 try:data=json.loads(p.read_text())
 except (OSError,ValueError):return {'message':'No installer run has been recorded in this boot.','log':''}
 log=Path(data.get('log',''))
 if log.parent!=p.parent or not log.name.startswith('installer-'):return {'message':'Installer log reference is invalid.','log':''}
 if data.get('running') and not Path('/proc',str(data.get('pid',0))).exists():data['running']=False;data['message']='Installer process is no longer running. Review the log and the wizard result; completion is unconfirmed.'
 data['log_text']=tail(log);return data
def collect():
 root=Path.home()/'.local/state/macaque';data={
  'summary.txt':f'Macaque diagnostics\nKernel: {platform.release()}\nMachine: {platform.machine()}\nSession type: {os.environ.get("XDG_SESSION_TYPE","unknown")}\nWayland display set: {bool(os.environ.get("WAYLAND_DISPLAY"))}\n',
  'system.txt':tail('/etc/os-release'),
  'session.log':tail(root/'session.log'),'compositor.log':tail(root/'compositor.log'),
  'login-journal.txt':command(['journalctl','-b','-u','greetd','--no-pager','-n','100','-o','cat']),
  'boot-journal.txt':command(['journalctl','-b','-k','--no-pager','-n','80','-o','cat']),
  'services.txt':command(['systemctl','--no-pager','--plain','is-active','NetworkManager','bluetooth','power-profiles-daemon','greetd']),
  'installer.txt':json.dumps(installer(),indent=2),
 }
 return {k:redact(v) for k,v in data.items()}
def action(p):
 if p['action']=='installer-status':return installer()
 data=collect()
 if p['action']=='diagnostics-status':return {'text':'\n\n'.join('=== '+k+' ===\n'+v for k,v in data.items())[:160000]}
 if p['action']!='diagnostics-export':raise ValueError('Unknown diagnostics request.')
 directory=Path(p['directory'])
 if not directory.is_absolute():raise ValueError('Choose an absolute report folder.')
 directory.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix='Macaque diagnostics '+time.strftime('%Y-%m-%d %H-%M-%S')+' ',suffix='.zip',dir=directory)
 try:
  with os.fdopen(fd,'wb') as file:
   with zipfile.ZipFile(file,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for key,value in data.items():archive.writestr(key,value)
  return {'path':name,'message':'Report saved locally. Review before sharing; no upload was made.'}
 except BaseException:Path(name).unlink(missing_ok=True);raise
if __name__=='__main__':
 try:print(json.dumps(action(json.loads(sys.stdin.read(16384)))))
 except Exception as ex:print(ex,file=sys.stderr);sys.exit(1)
