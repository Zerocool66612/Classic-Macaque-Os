import os,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtTest import QTest
from shiboken6 import isValid
from desktop import Desktop
from window_motion import Transition,EFFECTS
from window_motion_icon import white_monkey
from modern_desktop import Settings
app=QApplication([])
with tempfile.TemporaryDirectory() as data:
 d=Desktop(data);d.state.update(startup_files=False,startup_notes=False);d.show();QTest.qWait(30)
 image=white_monkey().pixmap(64,64).toImage()
 pixels=[image.pixelColor(x,y) for x in range(64) for y in range(64) if image.pixelColor(x,y).alpha()]
 assert pixels and all(c.red()==c.green()==c.blue()==255 for c in pixels)
 for effect in EFFECTS:
  d.state.update(open_effect=effect,close_effect=effect,animation_speed='Quick')
  w=d.window('Motion test',QWidget());QTest.qWait(40)
  assert (w.graphicsEffect() is not None)==(effect!='None')
  QTest.qWait(210);assert w.graphicsEffect() is None and w.isVisible()
  w.close();QTest.qWait(240);assert not isValid(w)
 d.state.update(reduce_motion=True);w=d.window('Reduced',QWidget());QTest.qWait(30);assert w.graphicsEffect() is None;w.close();QTest.qWait(30)
 d.state.update(reduce_motion=False,open_effect='Soft Zoom');w=d.window('Rapid close',QWidget());QTest.qWait(20);w.close();QTest.qWait(250)
 class Veto(QWidget):
  def can_close(self):return False
 w=d.window('Unsaved',Veto());QTest.qWait(250);w.close();QTest.qWait(20);assert w.isVisible()
 settings=Settings(d);assert len(settings.motion_choices)==2
 d.state.update(reduce_motion=True);w=d.window('Space test',QWidget());d.state['reduce_motion']=False;QTest.qWait(20);d.switch_workspace(1);QTest.qWait(250);assert not w.isVisible()
 d.quitting=True;d.hide()
print('Motion/icon checks passed')
