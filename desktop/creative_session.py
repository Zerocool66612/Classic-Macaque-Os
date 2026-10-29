#!/usr/bin/env python3
"""Experimental nested desktop. Never replaces or reconfigures the host WM."""
import os,sys,shutil,subprocess,tempfile,secrets,time,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REQUIRED=('Xephyr','openbox','xauth','xdpyinfo','dbus-run-session')
CONFIG='''<?xml version="1.0"?><openbox_config xmlns="http://openbox.org/3.4/rc">
<theme><name>Clearlooks</name><titleLayout>NLIMC</titleLayout></theme>
<focus><focusNew>yes</focusNew><followMouse>no</followMouse></focus>
<desktops><number>1</number></desktops>
<keyboard><keybind key="A-Tab"><action name="NextWindow"/></keybind><keybind key="A-F4"><action name="Close"/></keybind></keyboard>
<mouse><context name="Titlebar"><mousebind button="Left" action="Drag"><action name="Move"/></mousebind><mousebind button="Left" action="DoubleClick"><action name="ToggleMaximize"/></mousebind></context>
<context name="Close"><mousebind button="Left" action="Click"><action name="Close"/></mousebind></context>
<context name="Maximize"><mousebind button="Left" action="Click"><action name="ToggleMaximize"/></mousebind></context>
<context name="Minimize"><mousebind button="Left" action="Click"><action name="Iconify"/></mousebind></context>
<context name="Frame"><mousebind button="A-Left" action="Drag"><action name="Move"/></mousebind><mousebind button="A-Right" action="Drag"><action name="Resize"/></mousebind></context></mouse>
<applications><application title="Macaque Classic 0.20 — Macaque Desktop"><decor>no</decor><layer>below</layer><maximized>yes</maximized></application></applications>
</openbox_config>'''

def stop(process):
    if process and process.poll() is None:
        process.terminate()
        try:process.wait(timeout=4)
        except subprocess.TimeoutExpired:process.kill();process.wait()

def inside():
    # This branch runs under a private session bus as well as the nested DISPLAY.
    with tempfile.TemporaryDirectory(prefix='macaque-wm-') as temp:
        config=Path(temp)/'rc.xml';config.write_text(CONFIG)
        wm=subprocess.Popen(['openbox','--config-file',str(config)])
        desktop=None
        try:
            time.sleep(.5)
            if wm.poll() is not None:raise RuntimeError('The nested window manager could not start.')
            desktop=subprocess.Popen([sys.executable,str(ROOT/'desktop.py')])
            return desktop.wait()
        finally:
            stop(desktop);stop(wm)

def main():
    if '--inside' in sys.argv:return inside()
    missing=[name for name in REQUIRED if not shutil.which(name)]
    if missing:raise RuntimeError('Missing: '+', '.join(missing)+'. Run bash install-creative-apps.sh first.')
    if not os.environ.get('DISPLAY'):raise RuntimeError('An X11/XWayland host display is needed. Run this from your graphical Ubuntu desktop.')
    server=session=None
    with tempfile.TemporaryDirectory(prefix='macaque-session-') as temp:
        auth=Path(temp)/'Xauthority';auth.touch(mode=0o600)
        # Refuse occupied display numbers; Xephyr itself is the final authority.
        number=next((n for n in range(100,200) if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
        if number is None:raise RuntimeError('No free nested display number.')
        display=f':{number}'
        subprocess.run(['xauth','-f',str(auth),'add',display,'.',secrets.token_hex(16)],check=True,timeout=5)
        env=os.environ.copy();env.update(DISPLAY=display,XAUTHORITY=str(auth),MACAQUE_NATIVE_SESSION='1',QT_QPA_PLATFORM='xcb',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='Macaque',QT_QPA_PLATFORMTHEME='',GTK_USE_PORTAL='0')
        env.pop('WAYLAND_DISPLAY',None);env.pop('DBUS_SESSION_BUS_ADDRESS',None);env.pop('SESSION_MANAGER',None)
        logpath=Path.home()/'.local/share/MacaqueOS/creative-session.log';logpath.parent.mkdir(parents=True,exist_ok=True)
        with logpath.open('w') as log:
            try:
                # Outer Xephyr uses host DISPLAY/auth; clients receive the private pair.
                server=subprocess.Popen(['Xephyr',display,'-screen','1360x880','-resizeable','-no-host-grab','-nolisten','tcp','-auth',str(auth),'-noreset'],stdout=log,stderr=subprocess.STDOUT)
                deadline=time.monotonic()+12
                while True:
                    if server.poll() is not None:raise RuntimeError('Nested display failed. See '+str(logpath))
                    try:
                        if subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1).returncode==0:break
                    except subprocess.TimeoutExpired:pass
                    if time.monotonic()>deadline:raise RuntimeError('Nested display did not become ready. See '+str(logpath))
                    time.sleep(.15)
                print('Macaque Creative Session 0.20 · save and quit apps before closing the session.',flush=True)
                session=subprocess.Popen(['dbus-run-session','--',sys.executable,str(__file__),'--inside'],env=env,start_new_session=True)
                while session.poll() is None and server.poll() is None:time.sleep(.25)
                return session.returncode or 0
            finally:
                if session and session.poll() is None:
                    os.killpg(session.pid,signal.SIGTERM)
                    try:session.wait(timeout=4)
                    except subprocess.TimeoutExpired:os.killpg(session.pid,signal.SIGKILL);session.wait()
                stop(server)

if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,OSError,subprocess.SubprocessError) as ex:print('Creative Session: '+str(ex),file=sys.stderr);sys.exit(1)
    except KeyboardInterrupt:sys.exit(130)
