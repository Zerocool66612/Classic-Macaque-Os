import os,tempfile
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from desktop import Desktop
from window_controls import classic_controls
app=QApplication([])
from pathlib import Path
from PySide6.QtGui import QImage
import runpy
with tempfile.TemporaryDirectory() as staged:
 runpy.run_path(str(Path(__file__).resolve().parent.parent/'iso/stage-wayland.py'))['stage'](staged)
 for name in ['close','iconify','max','max_toggled']:
  image=QImage(str(Path(staged)/'usr/share/themes/Macaque Platinum/openbox-3'/ (name+'.xbm')))
  assert not image.isNull() and image.width()==16 and image.height()==16,name
with tempfile.TemporaryDirectory() as path:
 d=Desktop(path);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True);d.show();QTest.qWait(30)
 w=d.text_window('Window controls fixture','Test controls');QTest.qWait(30)
 buttons=w.bar.control_buttons
 assert classic_controls(d.state)
 assert buttons['Close'].x()<w.bar.label.x()<buttons['Minimize'].x()<buttons['Zoom'].x()
 for mode in ['light','dark']:
  d.set_mode(mode);QTest.qWait(20);assert not buttons['Close'].grab().isNull()
 d.set_preference('window_buttons','Traffic lights');QTest.qWait(20)
 assert buttons['Close'].x()<buttons['Minimize'].x()<buttons['Zoom'].x()<w.bar.label.x()
 d.set_preference('window_buttons','Classic');QTest.qWait(20)
 QTest.mouseClick(buttons['Zoom'],Qt.LeftButton);QTest.qWait(20);assert w.isMaximized()
 QTest.mouseClick(buttons['Zoom'],Qt.LeftButton);QTest.qWait(20);assert not w.isMaximized()
 QTest.mouseClick(buttons['Minimize'],Qt.LeftButton);QTest.qWait(20);assert w.isMinimized()
 w.showNormal();QTest.qWait(20);QTest.mouseClick(buttons['Close'],Qt.LeftButton);QTest.qWait(30)
 assert w not in d.area.subWindowList()
 d.quitting=True;d.close()
print('PASS: classic/traffic button placement, live switching, light/dark rendering, close, minimize and zoom/restore.')
