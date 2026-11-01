"""Allowlisted native programs in the Macaque desktop session."""
import os,shutil,subprocess
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
CREATIVE_APPS={
 'GIMP':('gimp',['--new-instance']),
 'Audacity':('audacity',[]),
 'OBS Studio':('obs',['--multi']),
}

def child_environment(base,config):
    env=dict(base)
    if base.get('MACAQUE_WAYLAND_SESSION')=='1':
        from wayland_session import native_environment
        env=native_environment(base);env['XDG_CONFIG_HOME']=str(config);return env
    for key in ('WAYLAND_DISPLAY','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','QT_QPA_FONTDIR','LD_LIBRARY_PATH','SESSION_MANAGER'):
        env.pop(key,None)
    env.update(QT_QPA_PLATFORM='xcb',GDK_BACKEND='x11',SDL_VIDEODRIVER='x11',XDG_SESSION_TYPE='x11',XDG_CURRENT_DESKTOP='Macaque',QT_QPA_PLATFORMTHEME='',GTK_USE_PORTAL='0',XDG_CONFIG_HOME=str(config))
    return env

class CreativeApps:
    def __init__(self,d):self.d=d;self.processes={};self.logs=[]
    def launch(self,name):
        if os.environ.get('MACAQUE_NATIVE_SESSION')!='1':
            return self.d.text_window(name+' · Creative Session required','To run GIMP, Audacity and OBS inside Macaque, close this desktop and run:\n\nbash run-creative.sh\n\nFirst-time setup: bash install-creative-apps.sh\n\nThe regular prototype cannot contain native application windows.')
        old=self.processes.get(name)
        if old and old.poll() is None:
            return self.d.text_window(name+' is running','Use Alt+Tab inside the Macaque session to switch to '+name+'.')
        program,args=CREATIVE_APPS[name];executable=shutil.which(program)
        if not executable:return self.d.text_window(name+' is not installed','Close Macaque and run bash install-creative-apps.sh from the extracted folder. Then start bash run-creative.sh again.')
        # Audacity can redirect to a running host instance. Refuse rather than risk
        # raising that host window. Our own tracked session instance is handled above.
        if name=='Audacity':
            try:
                if subprocess.run(['pgrep','-u',str(os.getuid()),'-x','audacity'],stdout=subprocess.DEVNULL,timeout=2).returncode==0:
                    return self.d.text_window('Close the other Audacity instance','Quit Audacity on your host desktop before launching it inside Macaque.')
            except (OSError,subprocess.TimeoutExpired):
                return self.d.text_window('Audacity check unavailable','The process check failed. Install procps with the setup script and try again.')
        config=self.d.base/'creative-config';config.mkdir(exist_ok=True)
        logs=self.d.base/'creative-logs';logs.mkdir(exist_ok=True)
        try:
            log=(logs/(program+'.log')).open('ab');self.logs.append(log)
            process=subprocess.Popen([executable,*args],env=child_environment(os.environ,config),stdout=log,stderr=subprocess.STDOUT)
            self.processes[name]=process
        except OSError as ex:return self.d.text_window(name+' launch failed',str(ex))
        from PySide6.QtCore import QTimer
        def check():
            if process.poll() is not None and process.returncode:
                self.d.text_window(name+' exited',f'{name} exited with code {process.returncode}.\nLog: {logs/(program+".log")}\n\nThis Wayland session requires a Wayland-capable build. See the log for backend or graphics errors.')
        QTimer.singleShot(2500,check)
    def can_close(self):
        running=[name for name,p in self.processes.items() if p.poll() is None]
        if running:
            QMessageBox.information(self.d,'Creative apps are still open','Save your work and quit these apps before closing Macaque:\n\n'+', '.join(running)+'\n\nUse Alt+Tab to switch between them.');return False
        return True
