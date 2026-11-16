"""Root-owned desktop package cache and bounded update receipts; no OS snapshots."""
import json,os,time
from pathlib import Path
from maintenance import metadata,digest
STORE=Path('/var/lib/macaque-classic/updates')
def installed_version():
 import subprocess
 try:return subprocess.check_output(['/usr/bin/dpkg-query','-W','-f=${Version}','macaque-classic'],text=True,timeout=10).strip()
 except (OSError,subprocess.SubprocessError):return ''
def older(version,current):
 import subprocess
 return bool(current) and subprocess.run(['/usr/bin/dpkg','--compare-versions',version,'lt',current],timeout=10).returncode==0
def status(store=None):
 root=Path(store) if store is not None else STORE;current=installed_version();packages=[]
 for p in sorted(root.glob('*.deb'))[:20]:
  try:
   if p.is_symlink() or not p.is_file():continue
   info=metadata(p);packages.append({**info,'path':str(p),'sha256':digest(p),'rollback':older(info['version'],current)})
  except (OSError,ValueError):continue
 try:history=json.loads((root/'history.json').read_text()[:128000])[-40:]
 except (OSError,ValueError,TypeError):history=[]
 return {'installed_version':current,'packages':packages,'history':history}
def cache_package(path,store=None):
 import shutil,tempfile
 root=Path(store) if store is not None else STORE;root.mkdir(parents=True,exist_ok=True);root.chmod(0o755)
 info=metadata(path);name='macaque-classic_'+info['version']+'_amd64.deb';target=root/name
 fd,temp=tempfile.mkstemp(prefix='.package-',dir=root)
 try:
  with os.fdopen(fd,'wb') as out,Path(path).open('rb') as source:shutil.copyfileobj(source,out)
  os.chmod(temp,0o644);os.replace(temp,target)
 finally:Path(temp).unlink(missing_ok=True)
 return target
def receipt(version,previous,result,action,store=None):
 root=Path(store) if store is not None else STORE;root.mkdir(parents=True,exist_ok=True)
 try:history=json.loads((root/'history.json').read_text())
 except (OSError,ValueError):history=[]
 history.append({'time':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'version':version,'previous':previous,'result':result,'action':action})
 target=root/'history.json';temp=root/'history.new';temp.write_text(json.dumps(history[-40:],indent=2));temp.chmod(0o644);os.replace(temp,target)
