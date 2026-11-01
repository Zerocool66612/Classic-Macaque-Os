#!/usr/bin/python3
"""Live-only root Qt client; compositor socket remains owned by the live user."""
import os,stat,sys,tempfile,subprocess,json,time,pwd
from pathlib import Path

def socket_for(uid,name):
    if not name or '/' in name or name in ('.','..'):raise ValueError('Invalid Wayland socket name.')
    runtime=Path('/run/user')/str(uid);p=runtime/name
    r=runtime.stat();s=p.lstat()
    if r.st_uid!=uid or stat.S_IMODE(r.st_mode)!=0o700 or s.st_uid!=uid or not stat.S_ISSOCK(s.st_mode):raise ValueError('Invalid live session socket.')
    return p

def record(path,data):
    fd,name=tempfile.mkstemp(prefix='.status-',dir=path.parent)
    with os.fdopen(fd,'w') as f:json.dump(data,f)
    os.chmod(name,0o644);os.replace(name,path)

def monitor(command,env,uid,logdir=Path('/var/log/macaque-installer')):
    logdir=Path(logdir);logdir.mkdir(mode=0o755,parents=True,exist_ok=True)
    info=logdir.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.geteuid():raise ValueError('Installer log directory has unexpected ownership/type.')
    fd,name=tempfile.mkstemp(prefix='installer-',suffix='.log',dir=logdir);os.fchmod(fd,0o600);os.fchown(fd,uid,pwd.getpwuid(uid).pw_gid)
    status=logdir/'last.json';data={'running':False,'log':name,'started':time.time(),'message':'Starting installer…'}
    try:
        with os.fdopen(fd,'wb') as log:
            process=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
            data.update(running=True,pid=process.pid,message='Installer running. Use its wizard for progress and disk-change confirmation.');record(status,data)
            code=process.wait()
        data.update(running=False,returncode=code,ended=time.time(),message='Installer wizard closed normally. Confirm completion on its final page; cancellation can also exit normally.' if code==0 else 'Installer exited with an error. Open Recovery & Diagnostics and review the installer log.')
        record(status,data);return code
    except Exception as ex:
        data.update(running=False,message='Installer could not be monitored: '+str(ex));record(status,data);raise

def main():
    if os.geteuid()!=0 or not Path('/etc/macaque-live').is_file() or 'boot=live' not in Path('/proc/cmdline').read_text().split():raise SystemExit('Only available from the Macaque live installer.')
    uid=int(os.environ.get('SUDO_UID','0'))
    if uid<=0 or len(sys.argv)!=2:raise SystemExit('Start from the live user desktop.')
    socket=socket_for(uid,sys.argv[1])
    with tempfile.TemporaryDirectory(prefix='macaque-installer-',dir='/run') as runtime:
        env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','LANG':'C.UTF-8','QT_QPA_PLATFORM':'wayland','XDG_SESSION_TYPE':'wayland','XDG_RUNTIME_DIR':runtime,'WAYLAND_DISPLAY':str(socket)}
        return monitor(['/usr/bin/calamares'],env,uid)
if __name__=='__main__':sys.exit(main())
