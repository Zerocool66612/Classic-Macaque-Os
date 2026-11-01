#!/usr/bin/python3
"""Run native Wayland desktop/services; labwc -S owns the session lifetime."""
import os,sys,subprocess,signal,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def native_environment(base):
    env=dict(base)
    if not env.get('WAYLAND_DISPLAY') or not env.get('XDG_RUNTIME_DIR'):raise RuntimeError('The Wayland compositor did not supply its display/runtime socket.')
    for key in ['DISPLAY','XAUTHORITY','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','LD_LIBRARY_PATH','SESSION_MANAGER','QT_QPA_FONTDIR']:env.pop(key,None)
    env.update(MACAQUE_NATIVE_SESSION='1',MACAQUE_WAYLAND_SESSION='1',QT_QPA_PLATFORM='wayland',GDK_BACKEND='wayland',SDL_VIDEODRIVER='wayland',XDG_SESSION_TYPE='wayland',XDG_SESSION_DESKTOP='macaque',XDG_CURRENT_DESKTOP='Macaque:wlroots',GTK_USE_PORTAL='1',QT_QPA_PLATFORMTHEME='')
    return env

def main():
    env=native_environment(os.environ)
    if '--preview' in sys.argv:env['MACAQUE_PREVIEW_SESSION']='1'
    logdir=Path.home()/'.local/state/macaque';logdir.mkdir(parents=True,exist_ok=True);children=[]
    with (logdir/'session.log').open('ab',buffering=0) as log:
        try:
            if shutil.which('dbus-update-activation-environment'):
                subprocess.run(['dbus-update-activation-environment',*(['--systemd'] if '--preview' not in sys.argv else []),'WAYLAND_DISPLAY','XDG_CURRENT_DESKTOP','XDG_SESSION_TYPE','QT_QPA_PLATFORM','GDK_BACKEND','SDL_VIDEODRIVER','DISPLAY=','XAUTHORITY='],env=env,stdout=log,stderr=log,timeout=10)
            if '--preview' not in sys.argv and shutil.which('lxpolkit'):children.append(subprocess.Popen(['lxpolkit'],env=env,stdout=log,stderr=log))
            if '--preview' not in sys.argv:children.append(subprocess.Popen([sys.executable,str(ROOT/'wayland_power.py'),'daemon'],env=env,stdout=log,stderr=log))
            desktop=subprocess.Popen([sys.executable,str(ROOT/'desktop.py')],env=env,stdout=log,stderr=log);children.append(desktop)
            def stopped(*_):
                if desktop.poll() is None:desktop.terminate()
            signal.signal(signal.SIGTERM,stopped);signal.signal(signal.SIGINT,stopped)
            code=desktop.wait()
            if code and shutil.which('foot'):
                subprocess.run(['foot','--title=Macaque startup diagnostics','/bin/sh','-c','tail -n 70 "$HOME/.local/state/macaque/session.log"; printf "\\nPress Enter to return to login"; read answer'],env=env)
            return code
        finally:
            for p in reversed(children):
                if p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=4)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as ex:print('Macaque Wayland session:',ex,file=sys.stderr);sys.exit(1)
