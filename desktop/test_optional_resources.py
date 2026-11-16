"""Behavior checks for optional timers, deferred imports and font selection."""
import os,sys,tempfile,time,subprocess,json,runpy
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
# Test startup imports in a fresh interpreter; don't let other tests pre-load chess.
result=subprocess.check_output([sys.executable,'-c',"import sys,desktop,json;print(json.dumps([m for m in ('chess','chess_app','teapot','browser_app','backup') if m in sys.modules]))"],cwd=Path(__file__).parent,text=True)
assert json.loads(result)==[],result
from PySide6.QtWidgets import QApplication,QComboBox
from PySide6.QtTest import QTest
from PySide6.QtGui import QFontDatabase
from desktop import Desktop
from interface_fonts import family,license_text
app=QApplication([])
with tempfile.TemporaryDirectory() as t:
 d=Desktop(t);d.state.update(reduce_motion=True,startup_files=False,startup_notes=False);d.show();QTest.qWait(40)
 assert family(d.state)=='Chicago Kare' and 'Chicago Kare' in QFontDatabase.families()
 assert 'Permission is hereby granted' in license_text()
 assert 'Chicago Kare' in d.desktop_stylesheet() and 'Chicago Kare' in d.top_bar.styleSheet()
 settings=d.settings().content;choice=next(c for c in settings.findChildren(QComboBox) if c.accessibleName()=='Interface font')
 choice.setCurrentText('Standard');assert family(d.state)=='DejaVu Sans' and 'Chicago Kare' not in d.top_bar.styleSheet()
 choice.setCurrentText('Classic');assert family(d.state)=='Chicago Kare'
 # Teapot repaint timer stops for pause, shade, minimize and workspace hiding.
 w=d.launch('Teapot Studio');v=w.content.view;QTest.qWait(70);assert v.timer.isActive()
 v.set_running(False);assert not v.timer.isActive();angle=v.angle;QTest.qWait(70);assert v.angle==angle
 v.set_running(True);assert v.timer.isActive()
 w.shade();QTest.qWait(25);assert not v.timer.isActive()
 w.shade();QTest.qWait(25);assert v.timer.isActive()
 w.showMinimized();QTest.qWait(25);assert not v.timer.isActive()
 d.activate_window(w);QTest.qWait(25);assert v.timer.isActive()
 d.switch_workspace(1);QTest.qWait(25);assert not v.timer.isActive()
 d.switch_workspace(0);QTest.qWait(25);assert v.timer.isActive()
 # The overview only refreshes while visible.
 overview=d.launch('Workspaces');assert 'browser_app' not in sys.modules;QTest.qWait(25);assert overview.content.timer.isActive()
 overview.shade();QTest.qWait(25);assert not overview.content.timer.isActive()
 overview.shade();QTest.qWait(25);assert overview.content.timer.isActive()
 # A paused stopwatch has no repeating timer. Hidden running time stays correct.
 clockwindow=d.launch('Clockwork');clock=clockwindow.content;QTest.qWait(25);assert not clock.timer.isActive()
 clock.toggle();assert clock.timer.isActive();start=clock.value();clockwindow.shade();QTest.qWait(70);assert not clock.timer.isActive() and clock.value()>start
 clockwindow.shade();QTest.qWait(25);assert clock.timer.isActive();clock.toggle();assert not clock.timer.isActive()
 # Hidden countdown still alerts using a single deadline timer, exactly once.
 clockwindow.shade();QTest.qWait(25);events=[];d.play_sound=events.append
 clock.deadline=time.monotonic()+.08;clock.countdown_timer.start(80);QTest.qWait(130)
 assert clock.deadline is None and events==['notification'] and not clock.timer.isActive()
 clock.tick();assert events==['notification']
 # Deferred apps still launch; optional font change is persisted.
 game=d.launch('Chess');assert game.content.app_name=='Chess'
 d.persist();assert json.loads(d.state_path.read_text())['interface_font']=='Classic'
 d.quitting=True;d.close();QTest.qWait(20)
def check_system_font(root):
 assert (root/'usr/share/fonts/truetype/macaque/ChicagoKare-Regular.ttf').read_bytes()==(Path(__file__).parent/'fonts/chicago-kare/ChicagoKare-Regular.ttf').read_bytes()
 assert 'Copyright (c) 2024 Duane King' in (root/'usr/share/doc/macaque-classic/fonts/chicago-kare/LICENSE').read_text()
stager=Path(__file__).parent.parent/'iso/stage-fonts.py'
if stager.is_file():
 with tempfile.TemporaryDirectory() as t:
  runpy.run_path(str(stager))['stage'](t);check_system_font(Path(t))
else:
 # Installed/live checks validate the actual staged font, not a source-only helper.
 check_system_font(Path('/'))
print('PASS: deferred imports; classic/standard fonts and attribution; optional timers stop while paused/hidden/minimized; stopwatch time and hidden countdown alarm preserved; system-font staging.')
