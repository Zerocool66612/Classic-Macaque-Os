#!/usr/bin/python3
"""Native Wayland capture through grim/slurp. No shell and no overwrites."""
import json,os,re,subprocess,sys,tempfile,time
from pathlib import Path

def capture(payload):
    if os.environ.get('MACAQUE_WAYLAND_SESSION')!='1' or not os.environ.get('WAYLAND_DISPLAY'):raise ValueError('Full-screen and region capture require the Macaque Wayland session.')
    args=['grim','-t','png']
    if payload.get('cursor'):args.append('-c')
    if payload.get('region'):
        selected=subprocess.run(['slurp'],capture_output=True,text=True,timeout=120)
        if selected.returncode:return {'cancelled':True}
        geometry=selected.stdout.strip()
        if not re.fullmatch(r'-?\d+,-?\d+ [1-9]\d*x[1-9]\d*',geometry):raise ValueError('Could not read the selected screen region.')
        args += ['-g',geometry]
    directory=Path(payload['directory'])
    if not directory.is_absolute():raise ValueError('Use an absolute screenshot folder.')
    directory.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='Screenshot '+time.strftime('%Y-%m-%d %H-%M-%S')+' ',suffix='.png',dir=directory)
    path=Path(name)
    try:
        with os.fdopen(fd,'wb') as out:
            subprocess.run([*args,'-'],stdout=out,stderr=subprocess.PIPE,check=True,timeout=30)
        with path.open('rb') as f:
            if f.read(8)!=b'\x89PNG\r\n\x1a\n':raise ValueError('The compositor did not return a PNG image.')
        return {'path':str(path),'cancelled':False}
    except BaseException:
        path.unlink(missing_ok=True);raise
if __name__=='__main__':
    try:print(json.dumps(capture(json.loads(sys.stdin.read(16384)))))
    except Exception as ex:
        detail=ex.stderr.decode(errors='replace') if isinstance(ex,subprocess.CalledProcessError) and isinstance(ex.stderr,bytes) else str(ex)
        print(detail,file=sys.stderr);sys.exit(1)
