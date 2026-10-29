import os,tempfile,time
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtCore import Qt,QCoreApplication,QEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from desktop import Desktop
from browser_app import browser_url,Browser
from applications import Finder
app=QApplication([])
with tempfile.TemporaryDirectory() as tmp:
 d=Desktop(tmp);d.show();app.processEvents()
 for w in d.area.subWindowList():w.close()
 a=d.launch('Calculator');b=d.launch('Tasks');assert a.property('workspace')==0
 d.switch_workspace(1);assert not a.isVisible() and not b.isVisible();c=d.launch('Clockwork');assert c.isVisible() and c.property('workspace')==1
 d.move_to_workspace(c,2);assert not c.isVisible();d.activate_window(a);assert d.workspace==0 and a.isVisible();d.activate_window(c);assert d.workspace==2 and c.isVisible()
 d.show_desktop();assert c.isMinimized() and not a.isMinimized();d.show_desktop();assert not c.isMinimized()
 overview=d.launch('Workspaces').content;assert len(overview.lists)==4
 d.switch_workspace(3);QTest.qWait(15);assert not c.isVisible()
 # File manager history, filtering/sorting/hidden files and live watcher updates.
 folder=d.disk.new_folder(d.disk.root,'File Test');(folder/'Alpha.txt').write_text('a');(folder/'Zebra.txt').write_text('zz');(folder/'.secret').write_text('hidden')
 w=d.open_finder(folder);files=w.content;assert isinstance(files,Finder);assert files.icons.count()==2
 files.filter.setText('alpha');assert files.icons.count()==1;files.filter.clear();files.hidden.setChecked(True);assert files.icons.count()==3;files.hidden.setChecked(False)
 files.sort.setCurrentText('Size');assert files.icons.item(0).text()=='Zebra.txt'
 files.pin_folder();assert str(folder) in d.state['favorite_folders'];assert files.sidebar.count()>=6
 files.open(d.disk.root/'Documents');files.go_back();assert files.path==folder;files.go_forward();assert files.path==d.disk.root/'Documents'
 files.address.setText(str(folder));files.go_address();assert files.path==folder
 (folder/'Live.txt').write_text('arrived outside the app')
 for _ in range(30):
  QTest.qWait(20);time.sleep(.005)
  if files.icons.count()==3:break
 assert files.icons.count()==3
 # Browser refuses privileged/no-sandbox execution rather than weakening Chromium.
 assert browser_url('example.com').toString()=='https://example.com'
 for bad in ('file:///etc/passwd','javascript:alert(1)','https://user:pass@example.com'):
  try:browser_url(bad)
  except ValueError:pass
  else:raise AssertionError('Bad web navigation accepted')
 if hasattr(os,'geteuid') and os.geteuid()==0:
  web=d.launch('Macaque Web').content;assert isinstance(web,Browser) and not web.available and 'regular user' in web.status.text()
 assert d.launch('Welcome Center').content.app_name=='Welcome Center'
 d.state['workspace_names']=['Main','Writing','Art','Games'];d.persist();d.quitting=True;d.close()
print('PASS: workspace assignment/switch/move/activation and desktop restore isolation; overview; file manager filter/sort/hidden/history/favorites/location/live watcher; browser URL and privileged-execution guard; Welcome Center. Live WebEngine rendering remains unverified.')
