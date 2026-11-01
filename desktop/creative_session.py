#!/usr/bin/env python3
"""Nested native Wayland preview; never changes the host login configuration."""
import os,sys,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REQUIRED=('labwc','dbus-run-session','swayidle','swaylock','wlopm')
CONFIG=(ROOT/'labwc-rc.xml').read_text()
def main():
    missing=[n for n in REQUIRED if not shutil.which(n)]
    if missing:raise RuntimeError('Missing: '+', '.join(missing)+'. Run bash install-creative-apps.sh first.')
    if not os.environ.get('WAYLAND_DISPLAY') or not os.environ.get('XDG_RUNTIME_DIR'):raise RuntimeError('Run this preview from a Wayland host session, or boot the Macaque ISO.')
    with tempfile.TemporaryDirectory(prefix='macaque-wayland-') as temp:
        config=Path(temp);(config/'rc.xml').write_text(CONFIG)
        # Preview has no system-installed helpers. Native desktop shortcuts remain.
        (config/'rc.xml').write_text(CONFIG.replace('/usr/local/bin/macaque-action terminal','foot').replace('/usr/local/bin/macaque-lock','true'))
        env=dict(os.environ,WLR_BACKENDS='wayland',WLR_XWAYLAND='/usr/bin/false',MACAQUE_WAYLAND_SESSION='1')
        env.pop('DISPLAY',None);env.pop('XAUTHORITY',None);env.pop('DBUS_SESSION_BUS_ADDRESS',None)
        import shlex
        command=shlex.join([sys.executable,str(ROOT/'wayland_session.py'),'--preview'])
        return subprocess.call(['dbus-run-session','--','labwc','-C',str(config),'-S',command],env=env)
if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,OSError) as ex:print('Wayland preview:',ex,file=sys.stderr);sys.exit(1)
