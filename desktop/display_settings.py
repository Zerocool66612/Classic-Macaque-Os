"""wlr-randr output changes with an independent 20-second rollback guard."""
import fcntl,json,os,re,subprocess,sys,time,uuid
from pathlib import Path
from input_settings import atomic,folder

def run(args):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT,timeout=12)
def outputs(text):
 result=[];item=None
 for line in text.splitlines():
  if line and not line[0].isspace():
   item={'name':line.split()[0],'description':line,'enabled':False,'modes':[],'scale':1.0,'position':[0,0],'transform':'normal','current':None};result.append(item)
  elif item:
   s=line.strip()
   if s.startswith('Enabled:'):item['enabled']=s.split(':',1)[1].strip()=='yes'
   mode=re.match(r'(\d+)x(\d+) px, ([\d.]+) Hz(?:\s*\(([^)]*)\))?',s)
   if mode:
    name=f'{mode[1]}x{mode[2]}@{float(mode[3]):.6f}Hz';item['modes'].append(name)
    if 'current' in (mode[4] or ''):item['current']=name
   if s.startswith('Scale:'):item['scale']=float(s.split(':',1)[1])
   if s.startswith('Position:'):item['position']=[int(x) for x in s.split(':',1)[1].strip().split(',')]
   if s.startswith('Transform:'):item['transform']=s.split(':',1)[1].strip()
 return result
def status():return outputs(run(['wlr-randr']))
def command(value,available):
 output=next((x for x in available if x['name']==value.get('name')),None)
 if not output or value.get('mode') not in output['modes']:raise ValueError('Choose a mode reported by the connected display.')
 scale=value.get('scale');x=value.get('x');y=value.get('y');rotation=value.get('transform','normal')
 if type(scale) not in (int,float) or not .5<=scale<=3:raise ValueError('Scale must be 0.5–3.')
 if any(type(v) is not int or abs(v)>20000 for v in (x,y)):raise ValueError('Display positions must be whole numbers within ±20000.')
 if rotation not in ('normal','90','180','270'):raise ValueError('Unsupported rotation.')
 return ['wlr-randr','--output',output['name'],'--on','--mode',value['mode'],'--scale',str(scale),'--pos',f'{x},{y}','--transform',rotation]
def snapshot_command(item):
 args=['wlr-randr','--output',item['name']]
 if not item['enabled']:return args+['--off']
 if not item['current']:raise ValueError('Current display mode is unavailable; refusing an unsafe preview.')
 return args+['--on','--mode',item['current'],'--scale',str(item['scale']),'--pos',','.join(map(str,item['position'])),'--transform',item['transform']]
def statepath():
 runtime=Path(os.environ['XDG_RUNTIME_DIR']);return runtime/'macaque-display-preview.json'
def locked():
 p=statepath().with_suffix('.lock');f=p.open('a');os.chmod(p,0o600);fcntl.flock(f,fcntl.LOCK_EX);return f
def load():
 try:return json.loads(statepath().read_text())
 except (OSError,ValueError):return {}
def preview(value):
 current=status();args=command(value,current);old=next(x for x in current if x['name']==value['name']);restore=snapshot_command(old)
 run([*args,'--dryrun'])
 with locked():
  oldstate=load()
  if oldstate.get('pending'):raise ValueError('Confirm or revert the previous display preview first.')
  token=uuid.uuid4().hex;atomic(statepath(),json.dumps({'pending':True,'token':token,'restore':restore,'value':value}))
  # Guard starts before changing hardware and survives the settings window.
  try:subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--guard',token],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
  except Exception:
   atomic(statepath(),json.dumps({'pending':False}));raise
  run(args) # On failure the guard remains armed for rollback.
 return {'message':'Preview applied. Keep the change within 20 seconds or it will revert.','token':token}
def finish(token,keep):
 with locked():
  data=load()
  if not data.get('pending') or data.get('token')!=token:raise ValueError('The display preview expired or was already handled.')
  if keep:
   try:saved=json.loads((folder()/'displays.json').read_text())
   except (OSError,ValueError):saved={}
   saved[data['value']['name']]=data['value'];atomic(folder()/'displays.json',json.dumps(saved))
  else:run(data['restore'])
  atomic(statepath(),json.dumps({'pending':False}))
 return {'message':'Display change kept.' if keep else 'Display change reverted.'}
def guard(token):
 time.sleep(20)
 try:finish(token,False)
 except (ValueError,OSError,subprocess.SubprocessError):pass

def restore_saved():
 try:items=json.loads((folder()/'displays.json').read_text()).values()
 except (OSError,ValueError):return
 available=status()
 for value in items:
  try:
   args=command(value,available);run([*args,'--dryrun']);run(args)
  except (ValueError,subprocess.SubprocessError):continue
if __name__=='__main__':
 if sys.argv[1:2]==['--guard'] and len(sys.argv)==3:guard(sys.argv[2])
 elif sys.argv[1:]==['--restore']:restore_saved()
