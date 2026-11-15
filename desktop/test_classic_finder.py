"""Behavior checks for spatial windows and managed classic file features."""
import os,tempfile,json
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from unittest.mock import patch,MagicMock
from PySide6.QtWidgets import QApplication,QPushButton,QCheckBox,QComboBox
from PySide6.QtCore import Qt,QPointF,QMimeData
from PySide6.QtTest import QTest
from PySide6.QtGui import QDropEvent
from mouse_tools import MIME
from desktop import Desktop
from classic_files import make_alias,alias_target,set_metadata,metadata,remember,running_menu
from menu_compat import Menu
app=QApplication([])
with tempfile.TemporaryDirectory() as t:
 with patch('desktop.SoundTheme',return_value=MagicMock()):d=Desktop(Path(t))
 d.state['reduce_motion']=True;d.show();QTest.qWait(30)
 root=d.disk.root/'Documents';folder=root/'Spatial';folder.mkdir();source=folder/'draft.txt';source.write_text('template')
 w=d.open_finder(folder);f=w.content;QTest.qWait(20)
 assert d.open_finder(folder) is w
 w.resize(710,410);w.move(170,110);f.toggle_view();f.sort.setCurrentText('Modified');remember(f)
 w.close();QTest.qWait(20);w=d.open_finder(folder);f=w.content
 assert (w.width(),w.height(),w.x(),w.y())==(710,410,170,110)
 assert f.mode=='list' and f.sort_mode=='Modified'
 f.open(root);assert f.path==folder and d.open_finder(root).content.path==root
 alias=make_alias(d,source);assert alias_target(d,alias)==source
 opened=d.open_item(alias);assert opened.content.path==source
 opened.close();QTest.qWait(20)
 bad=folder/'bad.mcalias';bad.write_text(json.dumps({'format':'macaque-alias-1','target':'../../outside'}))
 try:alias_target(d,bad);raise AssertionError('escaped managed disk')
 except ValueError:pass
 set_metadata(d,source,label='Project',stationery=True)
 moved=d.disk.rename(source,'renamed.txt');assert metadata(d,moved)['label']=='Project';assert alias_target(d,alias)==moved
 copywindow=d.open_document(moved);assert copywindow.content.path!=moved
 copywindow.content.editor.setPlainText('new copy');copywindow.content.save();assert moved.read_text()=='template'
 info=d.get_info(moved);assert any(c.currentText()=='Project' for c in info.content.findChildren(QComboBox))
 assert any(c.isChecked() for c in info.content.findChildren(QCheckBox))
 f.refresh();f.mode='icons';f.stack.setCurrentIndex(0)
 for i in range(f.icons.count()):f.icons.item(i).setSelected(True)
 selected=set(f.selected_paths());f.refresh();assert set(f.selected_paths())==selected and len(selected)>1
 menu=Menu(d);d.activate_window(w);running_menu(d,menu);menu.actions()[0].trigger();assert w.property('classic_hidden') and w.isHidden()
 d.switch_workspace(1);d.switch_workspace(0);assert w.isHidden()
 running_menu(d,menu);menu.actions()[2].trigger();assert not w.property('classic_hidden') and not w.isHidden()
 search=d.launch('Macaque Search').content;search.input.setText('label:Project');search.search();assert search.results.count()==1 and 'renamed.txt' in search.results.item(0).text()
 # A same-folder drag moves icon positions without moving or duplicating files.
 f.mode='icons';f.stack.setCurrentIndex(0);QTest.qWait(20)
 mime=QMimeData();mime.setData(MIME,json.dumps([str(moved)]).encode())
 item=next(f.icons.item(i) for i in range(f.icons.count()) if f.icons.item(i).data(Qt.UserRole)==str(moved))
 before=f.icons.visualItemRect(item).topLeft()
 event=QDropEvent(QPointF(400,220),Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier)
 f.icons.dropEvent(event);assert event.isAccepted() and moved.exists()
 assert f.icons.visualItemRect(item).topLeft()!=before
 remember(f);saved_position=d.state['folder_views'][str(folder)]['positions'][str(moved)]
 f.refresh();assert [f.icons.visualItemRect(next(f.icons.item(i) for i in range(f.icons.count()) if f.icons.item(i).data(Qt.UserRole)==str(moved))).x(),f.icons.visualItemRect(next(f.icons.item(i) for i in range(f.icons.count()) if f.icons.item(i).data(Qt.UserRole)==str(moved))).y()]==saved_position
 # Delete in the filter edits text; it must never trash the selected files.
 f.filter.setText('renamed');f.filter.setFocus();f.filter.selectAll();QTest.keyClick(f.filter,Qt.Key_Delete);assert f.filter.text()=='' and moved.exists()
 # Eject requests wait for initial discovery, and reject a replaced drive identity.
 from removable_drives import RemovableDrives
 with patch.object(RemovableDrives,'refresh'):
  panel=RemovableDrives(d)
 volume={'device':'/dev/fixture1','identity':'9:1','uuid':'fixture','name':'USB','size':1024,'mounts':['/media/fixture']}
 panel.job=object();panel.eject_volume(volume);assert panel.pending_eject==volume
 panel.job=None;panel.populate([{'model':'Fixture','volumes':[volume]}])
 with patch.object(panel,'eject') as eject:
  panel.eject_volume({**volume,'identity':'9:2'});eject.assert_not_called()
  panel.eject_volume(volume);eject.assert_called_once()
 # Closing and restarting preserves metadata and folder view records.
 d.persist();assert json.loads(d.state_path.read_text())['folder_views']
 d.quitting=True;d.close()
print('PASS: spatial reuse/geometry/view; aliases and boundary guards; labels survive rename; stationery preserves original; Get Info; multi-selection; hide/show across workspaces.')
