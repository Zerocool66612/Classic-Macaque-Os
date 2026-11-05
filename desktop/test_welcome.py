import os,tempfile,uuid,stat
from pathlib import Path
from unittest.mock import Mock,patch
os.environ['QT_QPA_PLATFORM']='offscreen'
from first_run import claim_welcome
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from welcome_animation import WelcomeAnimation
with tempfile.TemporaryDirectory() as t:
 root=Path(t)/'root';state=Path(t)/'state';(root/'etc').mkdir(parents=True)
 env={'MACAQUE_NATIVE_SESSION':'1'}
 def claim(e=env,c=''):return claim_welcome(root,state,e,c)
 assert not claim()
 (root/'etc/macaque-installed').touch();assert not claim()
 token=str(uuid.uuid4());(root/'etc/macaque-welcome-install-id').write_text(token)
 assert not claim({},'') and not claim(dict(env,MACAQUE_PREVIEW_SESSION='1'),'')
 assert not claim(env,'boot=live quiet')
 (root/'etc/macaque-live').touch();assert not claim();(root/'etc/macaque-live').unlink()
 assert claim();assert not claim();assert stat.S_IMODE((state/('welcome-'+token+'.seen')).stat().st_mode)==0o600
 # New install token enables one new greeting; invalid tokens never become paths.
 (root/'etc/macaque-welcome-install-id').write_text('../../unsafe');assert not claim()
 (root/'etc/macaque-welcome-install-id').write_text(str(uuid.uuid4()));assert claim();assert not claim()
 blocked=Path(t)/'file';blocked.touch();assert not claim_welcome(root,blocked,env,'')
app=QApplication([])
class Parent(QWidget):
 def __init__(self):super().__init__();self.sound_theme=Mock();self.play_sound=Mock();self.state={}
d=Parent();w=WelcomeAnimation(d);w.show();QTest.qWait(20);assert w.timer.isActive()
assert not hasattr(w,'skip') and not hasattr(w,'mute')
QTest.keyClick(w,Qt.Key_Escape);QTest.keyClick(w,Qt.Key_Return);w.reject();w.accept();w.close();assert w.isVisible() and w.timer.isActive()
w.chime();d.play_sound.assert_called_once_with('welcome')
for t in (0.,1.,3.,6.,8.,10.,14.9):w.t=t;assert not w.grab().isNull()
w.clock=Mock();w.clock.elapsed.return_value=15001;w.tick();assert not w.isVisible() and not w.timer.isActive()
print('Installed/native/live/preview guards, durable once-only claim, private marker, failed-write behavior, animated frames, non-skippable completion, Escape/Return/close/reject guards passed.')

# Actual desktop startup waits for the intro; Skip continues into Welcome Center.
from desktop import Desktop
with tempfile.TemporaryDirectory() as t,patch('first_run.claim_welcome',return_value=True) as claim:
 desktop=Desktop(Path(t));desktop.show();QTest.qWait(80)
 assert desktop.welcome_intro.isVisible() and not desktop.area.subWindowList()
 desktop.welcome_intro.clock=Mock();desktop.welcome_intro.clock.elapsed.return_value=15001;desktop.welcome_intro.tick();QTest.qWait(350)
 assert any(w.windowTitle()=='Setup Assistant' for w in desktop.area.subWindowList());claim.assert_called_once()
 desktop.quitting=True;desktop.close()
print('Actual desktop first-run deferral and completion -> Setup Assistant continuation passed.')
