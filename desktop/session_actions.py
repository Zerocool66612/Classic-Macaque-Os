"""Confirmed native-session power controls. No forced termination or sudo."""
import os
from PySide6.QtWidgets import QMessageBox
from system_tasks import Task
LABELS={'poweroff':('Shut Down','Shut down this computer now?'),'reboot':('Restart','Restart this computer now?'),'logout':('Log Out','Log out and return to the login screen?')}
def command(action,env=None):
    env=os.environ if env is None else env
    if action not in LABELS:raise ValueError('Unknown session action.')
    if env.get('MACAQUE_NATIVE_SESSION')!='1' or env.get('MACAQUE_PREVIEW_SESSION')=='1':raise ValueError('Use the native Macaque session. Power actions are disabled in the desktop preview.')
    if action=='logout':
        if env.get('MACAQUE_WAYLAND_SESSION')!='1' or not env.get('LABWC_PID','').isdigit():raise ValueError('The Macaque Wayland compositor could not be identified.')
        return ['labwc','--exit']
    return ['systemctl',action]
def request(d,action):
    try:argv=command(action)
    except ValueError as e:QMessageBox.information(d,'Macaque session',str(e));return
    if getattr(d,'_session_job',None):return
    if d.installer_busy():QMessageBox.information(d,'Installer running','Finish the installation wizard before ending this session.');return
    title,prompt=LABELS[action]
    if QMessageBox.question(d,title,prompt+'\nYou will be asked to save open Macaque documents.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
    for window in d.area.subWindowList():
        if hasattr(window.content,'can_close') and not window.content.can_close():return
    if not d.app_support.can_close():return
    if hasattr(d,'creative_apps') and not d.creative_apps.can_close():return
    d.persist();d._session_job=Task(d,argv,timeout=60000)
    def finished(ok,text):
        d._session_job=None
        if not ok:QMessageBox.warning(d,title+' failed',text)
    d._session_job.done.connect(finished)
