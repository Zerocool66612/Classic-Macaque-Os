import os,tempfile,json
os.environ.update(QT_QPA_PLATFORM='offscreen',MACAQUE_SILENT='1')
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QObject,Signal,QTimer,Qt
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from desktop import Desktop
import laptop_controls
app=QApplication([])
class FakeTask(QObject):
 done=Signal(bool,str);calls=[]
 @staticmethod
 def helper(name):return ['fixture',name]
 def __init__(self,parent,argv,payload=None,timeout=0):
  super().__init__(parent);self.calls.append(payload)
  data={'audio':{'percent':55,'muted':False},'audio_error':'','backlights':[{'percent':45}],'batteries':[]} if payload['action']=='status' else {'kind':'Volume','percent':60,'muted':False}
  QTimer.singleShot(0,lambda:self.done.emit(True,json.dumps(data)))
with tempfile.TemporaryDirectory() as temp:
 d=Desktop(temp);d.state.update(startup_files=False,startup_notes=False,startup_welcome=False,reduce_motion=True);d.show();QTest.qWait(30)
 target=d.launch('Calculator');tool=d.launch('Screenshot');panel=tool.content;assert panel.target is target
 panel.mode.setCurrentText('Classic window');panel.capture();assert panel.busy and not panel.can_close();QTest.qWait(350)
 assert not panel.busy and panel.path.is_file() and not QPixmap(str(panel.path)).isNull();assert tool.isVisible()
 assert QPixmap(str(panel.path)).size()==target.size();panel.copy.click();assert not app.clipboard().pixmap().isNull()
 second=d.launch('Macaque Text');assert d.launch('Screenshot') is tool and panel.target is second
 old=panel.path;panel.capture();QTest.qWait(350);assert panel.path!=old and old.exists()
 with patch.object(laptop_controls,'Task',FakeTask):
  controls=d.launch('Laptop Controls').content;QTest.qWait(30);assert controls.volume.value()==55 and controls.brightness.value()==45
  controls.volume.setValue(62);controls.volume.sliderReleased.emit();QTest.qWait(30);assert {'action':'volume','percent':62} in FakeTask.calls
  d.hardware_keys.run('volume-up');d.hardware_keys.run('volume-down');QTest.qWait(40);assert d.hardware_keys.job is None and not d.hardware_keys.pending
  assert d.hardware_keys.label.isVisible() and 'Volume: 60%' in d.hardware_keys.label.text()
  controls.timer.stop()
 d.hardware_keys.timer.stop();d.quitting=True;d.hide()
print('Internal-window PNG capture, preview, clipboard, non-overwriting repeat, laptop sliders and queued hardware feedback passed offscreen (services mocked).')
