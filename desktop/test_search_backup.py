import os,json,tempfile,zipfile,stat,time
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from desktop import Desktop
from classic_search import ClassicSearch,classic_files
from backup import create_backup,recover_backup
from extras import ArchiveViewer
app=QApplication([])
with tempfile.TemporaryDirectory() as temp:
 t=Path(temp);d=Desktop(t/'data');d.show();QTest.qWait(30)
 outside=t/'HOST-ONLY-needle.txt';outside.write_text('not part of the classic disk')
 inside=d.disk.root/'Documents'/'CLASSIC-needle.txt';inside.write_text('classic data');(d.disk.root/'Documents'/'external-link.txt').symlink_to(outside)
 (d.disk.root/'host-folder-link').symlink_to(t,target_is_directory=True)
 search=d.launch_palette().content;assert isinstance(search,ClassicSearch);assert d.launch_palette().content is search
 search.input.setText('needle');search.search();assert search.results.count()==1;assert 'CLASSIC-needle' in search.results.item(0).text();assert 'HOST-ONLY' not in search.results.item(0).text()
 paths,cut=classic_files(d.disk.root,'HOST');assert not paths
 search.input.setText('Chess');search.search();assert search.results.count()==1
 with patch.object(d,'launch') as launch:search.activate();launch.assert_called_once_with('Chess')
 search.input.setText('needle');search.search()
 with patch.object(d,'open_item') as open_file:search.activate();open_file.assert_called_once_with(inside)
 assert d.top_bar.buttons[0].text()=='' and not d.top_bar.buttons[0].icon().isNull();assert d.top_bar.buttons[0].menu()==d.top_bar.system
 # The application shortcut stays inside the MDI desktop.
 search.parentWidget();d.activateWindow();d.setFocus();QTest.keyClick(d,Qt.Key_F6);QTest.qWait(20);assert isinstance(d.active(),ClassicSearch)
 # Portable round-trip, empty directories, state snapshot and symlink exclusion.
 (d.disk.root/'Documents'/'Empty').mkdir();archive=t/'backup.zip';state={'stickies':{'note':'keep me'},'tasks':[{'text':'test','done':False}]};create_backup(d.disk.root,state,archive)
 with zipfile.ZipFile(archive) as z:assert not any('external-link' in p or 'host-folder-link' in p for p in z.namelist())
 recovered=Path(recover_backup(archive,d.disk.root/'Recovered Backups'));assert (recovered/'Macaque HD/Documents/CLASSIC-needle.txt').read_text()=='classic data';assert (recovered/'Macaque HD/Documents/Empty').is_dir();assert json.loads((recovered/'desktop-state.json').read_text())==state;assert inside.read_text()=='classic data'
 try:create_backup(d.disk.root,state,archive)
 except ValueError:pass
 else:raise AssertionError('Existing backup overwritten')
 # Reject traversal/symlink archives before any recovery tree is created.
 parent=t/'recovery-tests';parent.mkdir()
 for kind in ('traversal','symlink','oversized-info'):
  bad=t/(kind+'.zip')
  with zipfile.ZipFile(bad,'w') as z:
   z.writestr('backup-info.json',json.dumps({'format':'macaque-classic-backup','version':1}) if kind!='oversized-info' else ' '*70000)
   if kind=='traversal':z.writestr('Macaque HD/../../escape.txt','no')
   if kind=='symlink':
    info=zipfile.ZipInfo('Macaque HD/link');info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'/tmp')
  try:recover_backup(bad,parent)
  except (ValueError,KeyError):pass
  else:raise AssertionError('Unsafe backup accepted')
  assert not list(parent.iterdir())
 # Actual asynchronous UI completes its worker and reenables controls.
 panel=d.launch('Backup & Recovery').content;panel.start(create_backup,(d.disk.root,state,t/'worker-backup.zip'))
 for _ in range(150):
  QTest.qWait(20);time.sleep(.01)
  if panel.worker.isFinished() and panel.save.isEnabled():break
 assert panel.worker.isFinished() and panel.save.isEnabled() and (t/'worker-backup.zip').exists(),(panel.worker.isRunning(),panel.status.text())
 assert panel.status.text().startswith('Completed:')
 # ZIP files open in the internal archive viewer.
 assert isinstance(d.open_document(archive).content,ArchiveViewer)
 d.quitting=True;d.close()
print('PASS: Classic-only app/file search, no host/symlink results; search activation and F6; icon-only system menu; backup/recovery round-trip with state and empty folders, no overwrite, malicious archive rejection; internal ZIP association')
