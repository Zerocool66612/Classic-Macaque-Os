#!/usr/bin/python3
"""Live-only root Qt client; compositor socket remains owned by the live user."""
import os,stat,sys,tempfile,subprocess
from pathlib import Path

def socket_for(uid,name):
    if not name or '/' in name or name in ('.','..'):raise ValueError('Invalid Wayland socket name.')
    runtime=Path('/run/user')/str(uid);p=runtime/name
    r=runtime.stat();s=p.lstat()
    if r.st_uid!=uid or stat.S_IMODE(r.st_mode)!=0o700 or s.st_uid!=uid or not stat.S_ISSOCK(s.st_mode):raise ValueError('Invalid live session socket.')
    return p

def main():
    if os.geteuid()!=0 or not Path('/etc/macaque-live').is_file() or 'boot=live' not in Path('/proc/cmdline').read_text().split():raise SystemExit('Only available from the Macaque live installer.')
    uid=int(os.environ.get('SUDO_UID','0'))
    if uid<=0 or len(sys.argv)!=2:raise SystemExit('Start from the live user desktop.')
    socket=socket_for(uid,sys.argv[1])
    with tempfile.TemporaryDirectory(prefix='macaque-installer-',dir='/run') as runtime:
        env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','LANG':'C.UTF-8','QT_QPA_PLATFORM':'wayland','XDG_SESSION_TYPE':'wayland','XDG_RUNTIME_DIR':runtime,'WAYLAND_DISPLAY':str(socket)}
        return subprocess.call(['/usr/bin/calamares'],env=env)
if __name__=='__main__':sys.exit(main())
