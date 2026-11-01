import os,tempfile,json
os.environ.update(QT_QPA_PLATFORM='offscreen',MACAQUE_SILENT='1')
from unittest.mock import patch
from PySide6.QtCore import QObject,Signal,QTimer
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtTest import QTest
from desktop import Desktop
import reliability_panels as panels
app=QApplication([])
class FakeTask(QObject):
 done=Signal(bool,str);calls=[];fail=False
 @staticmethod
 def helper(name):return ['fixture',name]
 def __init__(self,parent,argv,payload=None,timeout=0):
  super().__init__(parent);self.calls.append((argv,payload));op=payload.get('action') if payload else ''
  data={'touchpad-status':{'tap':True,'naturalScroll':False,'disableWhileTyping':True,'pointerSpeed':.2},'display-status':{'outputs':[{'name':'eDP-1','description':'Laptop','modes':['1920x1080@60.000000Hz'],'current':'1920x1080@60.000000Hz','scale':1,'position':[0,0],'transform':'normal'}]},'profiles-status':{'profiles':['balanced','power-saver'],'active':'balanced','details':'Fixture profiles'},'audio-status':{'outputs':[{'name':'speaker','description':'Speakers','muted':False,'percent':50}],'inputs':[{'name':'mic','description':'Microphone','muted':False,'percent':40}],'default_output':'speaker','default_input':'mic'},'bluetooth-status':{'adapter':'/org/bluez/hci0','powered':True,'devices':[{'path':'/org/bluez/hci0/dev_1','name':'Headset','paired':True,'connected':False}]},'diagnostics-status':{'text':'Fixture report'},'installer-status':{'message':'Installer failed: fixture','log_text':'Fixture failure details'}}.get(op,{'message':'Applied'})
  QTimer.singleShot(0,lambda:self.done.emit(not FakeTask.fail,'Hardware unavailable (fixture)' if FakeTask.fail else json.dumps(data)))
with tempfile.TemporaryDirectory() as temp,patch.object(panels,'Task',FakeTask):
 d=Desktop(temp);d.state.update(startup_files=False,startup_notes=False,startup_welcome=False,reduce_motion=True);d.show();QTest.qWait(30)
 for name in ('Touchpad','Displays','Power Profiles','Bluetooth','Audio Devices','Recovery & Diagnostics','Installer Status'):
  frame=d.launch(name);QTest.qWait(20);assert frame.content.job is None,name;assert d.launch(name) is frame
 touch=d.launch('Touchpad').content;touch.fields['naturalScroll'].setChecked(True);touch.apply();QTest.qWait(20);assert FakeTask.calls[-1][1]['values']['naturalScroll'] is True
 display=d.launch('Displays').content;assert display.output.currentData()=='eDP-1' and display.mode.currentText()=='1920x1080@60.000000Hz'
 audio=d.launch('Audio Devices').content;audio.change('audio-input-volume',audio.input,percent=30);QTest.qWait(20);assert any(p and p.get('percent')==30 for _,p in FakeTask.calls)
 bluetooth=d.launch('Bluetooth').content;bluetooth.items.setCurrentRow(0)
 with patch.object(panels.QMessageBox,'question',return_value=QMessageBox.No):
  before=len(FakeTask.calls);bluetooth.change('bluetooth-forget');assert len(FakeTask.calls)==before
 profiles=d.launch('Power Profiles').content;assert profiles.profiles.count()==2
 FakeTask.fail=True;profiles.refresh();QTest.qWait(20);assert 'unavailable' in profiles.status.text();FakeTask.fail=False
 installer=d.launch('Installer Status').content;assert 'failure details' in installer.text.toPlainText()
 with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'0'}):installer.restart();assert 'only' in installer.status.text()
 d.quitting=True;d.hide()
print('Seven Classic reliability panels, singleton routes, input/audio operations, forget cancellation, failure feedback and preview reboot guard passed (hardware mocked).')
