import os,tempfile
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtCore import QObject,Signal
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtTest import QTest
from desktop import Desktop
import session_actions as actions
class FakeTask(QObject):
 done=Signal(bool,str)
 calls=[]
 def __init__(self,parent,argv,**kw):super().__init__(parent);self.calls.append(argv)
app=QApplication([])
env={'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0','MACAQUE_WAYLAND_SESSION':'1','LABWC_PID':'123'}
assert actions.command('poweroff',env)==['systemctl','poweroff'] and actions.command('reboot',env)==['systemctl','reboot'] and actions.command('logout',env)==['labwc','--exit']
for action in ('poweroff','reboot','logout'):
 try:actions.command(action,dict(env,MACAQUE_PREVIEW_SESSION='1'));raise AssertionError()
 except ValueError:pass
with tempfile.TemporaryDirectory() as t:
 d=Desktop(Path(t));d.show();QTest.qWait(60);d.system_menu();texts=[a.text() for a in d.top_bar.system.actions()];assert all(s in texts for s in ('Shut Down…','Restart…','Log Out…'))
 with patch.dict(os.environ,env),patch.object(actions,'Task',FakeTask),patch.object(QMessageBox,'question',return_value=QMessageBox.No):d.session_action('reboot');assert not FakeTask.calls
 with patch.dict(os.environ,env),patch.object(actions,'Task',FakeTask),patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):
  w=d.launch('Macaque Text')
  with patch.object(w.content,'can_close',return_value=False):d.session_action('poweroff');assert not FakeTask.calls
  with patch.object(w.content,'can_close',return_value=True):
   for action,expected in [('poweroff',['systemctl','poweroff']),('reboot',['systemctl','reboot']),('logout',['labwc','--exit'])]:
    d.session_action(action);assert FakeTask.calls[-1]==expected;job=d._session_job;d.session_action(action);assert d._session_job is job;job.done.emit(True,'')
  with patch.object(QMessageBox,'warning') as warn:
   d.session_action('reboot');d._session_job.done.emit(False,'Permission denied');warn.assert_called_once()
 d.quitting=True;d.close()
print('Top-left power menu, exact native commands, preview/cancel/unsaved-work guards, busy suppression and service-failure feedback passed; no actual power actions executed.')
