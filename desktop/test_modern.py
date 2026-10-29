import os,tempfile,json
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtCore import Qt,QEvent,QCoreApplication
from PySide6.QtWidgets import QApplication,QCheckBox,QComboBox
from PySide6.QtTest import QTest
from desktop import Desktop
app=QApplication([]);app.setOrganizationName('MacaqueTests');app.setApplicationName('Modern010')
with tempfile.TemporaryDirectory() as temp:
 d=Desktop(temp);d.show();QTest.qWait(40)
 assert d.top_bar.height()==32
 for width in (640,800,1000,1360,1920):
  d.resize(width,850);QTest.qWait(20);d.clock();bar=d.top_bar
  assert bar.clock.geometry().right()<bar.width(),(width,bar.clock.geometry(),bar.width())
  visible=[b for b in bar.findChildren(type(bar.clock)) if b.isVisible() and b.parent()==bar]
  for a,b in zip(sorted(visible,key=lambda b:b.x()),sorted(visible,key=lambda b:b.x())[1:]):assert a.geometry().right()<b.geometry().left(),(width,a.text(),b.text())
 d.resize(1360,880);QTest.qWait(20)
 d.state['do_not_disturb']=True;d.notify('Test activity','Saved inside Macaque');assert d.state['unread_notifications']==1;assert not getattr(d,'toast',None)
 center=d.notifications();assert d.state['unread_notifications']==0;assert 'Test activity' in center.content.items.item(0).text();center.content.clear();assert not d.state['notifications']
 d.state['do_not_disturb']=False;d.notify('Visible banner','Test notification');assert d.toast.isVisible();d.toast.hide()
 # Settings checkboxes are real controls, not static previews.
 settings=d.settings();checks={c.text():c for c in settings.content.findChildren(QCheckBox)}
 checks['Show desktop file icons'].click();assert all(b.isHidden() for b in d.icons)
 checks['Show desktop file icons'].click();assert all(not b.isHidden() for b in d.icons)
 checks['Center new windows'].click();w=d.launch('Calculator');assert abs(w.x()-(d.area.viewport().width()-w.width())//2)<=1
 assert all(b.isHidden() for b in d.top_bar.controls.values());assert all(b.isHidden() for b in d.top_bar.pins);assert not d.top_bar.more.isVisible();d.quick_settings(d.top_bar.quick_menu);assert any(a.text()=='Classic Sounds…' for a in d.top_bar.quick_menu.actions())
 d.set_preference('compact_bar',False);assert d.top_bar.height()==38;d.set_preference('compact_bar',True);assert d.top_bar.height()==32
 d.set_preference('clock_seconds',True);assert d.top_bar.clock.text().count(':')==2
 d.snap_window('left');assert w.x()==0 and w.width()==d.area.viewport().width()//2
 d.snap_window('right');assert w.x()==d.area.viewport().width()//2
 windows=[w for w in d.area.subWindowList() if not w.isMinimized()];d.show_desktop();assert all(w.isMinimized() for w in windows);d.show_desktop();assert all(not w.isMinimized() for w in windows)
 # Screenshot creates an actual PNG within the managed disk.
 d.capture_desktop();QTest.qWait(220);screens=list((d.disk.root/'Pictures').glob('*.png'));assert len(screens)==1 and screens[0].read_bytes().startswith(b'\x89PNG')
 d.state.update(startup_apps=['Tasks'],startup_files=False,startup_notes=False,startup_about=False,ui_density='Compact',text_size=14);d.persist()
 d.quitting=True;d.close();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
 d=Desktop(temp);d.show();QTest.qWait(50);assert [w.content.app_name for w in d.area.subWindowList()]==['Tasks'];assert d.state['text_size']==14 ;d.quitting=True;d.close()
print('PASS: compact top bar at 640–1920px without overlap; notifications/read/clear/DND; live settings; hidden-control overflow; density and seconds; centered windows; snap and show/restore desktop; actual PNG screenshot; startup apps and preferences persist')
