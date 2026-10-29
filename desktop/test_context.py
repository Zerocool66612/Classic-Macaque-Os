import os,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from pathlib import Path
from PySide6.QtCore import Qt,QPoint,QTimer
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QInputDialog
from desktop import Desktop
from applications import Finder,SimpleText
app=QApplication([])
def action(menu,label):return next(a for a in menu.actions() if a.text()==label)
with tempfile.TemporaryDirectory() as data,tempfile.TemporaryDirectory() as host:
 d=Desktop(data);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True);d.show();QTest.qWait(20)
 errors=[];d.error=lambda e:errors.append(str(e))
 source=d.disk.root/'Documents'/'one.txt';source.write_text('one');two=source.with_name('two.txt');two.write_text('two');target=d.disk.root/'Downloads'
 m=d.file_context_menu([source,two],source.parent);action(m,'Copy').trigger();d.paste_items(target);assert (target/source.name).read_text()=='one' and (target/two.name).exists()
 action(m,'Cut').trigger();d.paste_items(d.disk.root/'Desktop');assert not source.exists() and d.context_clipboard is None
 source=d.disk.root/'Desktop'/'one.txt';m=d.file_context_menu([source],source.parent);action(m,'Duplicate').trigger();assert source.with_name('one copy.txt').exists()
 original=QInputDialog.getText;QInputDialog.getText=lambda *a,**k:('renamed.txt',True)
 action(m,'Rename…').trigger();source=source.with_name('renamed.txt');assert source.exists()
 QInputDialog.getText=lambda *a,**k:('new.txt',True);d.new_text_file(target);assert (target/'new.txt').exists();QInputDialog.getText=original
 m=d.file_context_menu([source],source.parent);action(m,'Move to Trash').trigger();assert not source.exists();key=next(k for k,v in d.disk.trash_items().items() if v['name']=='renamed.txt');d.disk.restore(key);assert source.exists()
 for path in [d.disk.root/'Applications',Path(host)]:
  m=d.file_context_menu([path],path)
  assert not action(m,'Rename…').isEnabled() and not action(m,'Move to Trash').isEnabled()
  empty=d.file_context_menu([],path);assert not action(empty,'New Folder…').isEnabled()
 f=Finder(d,d.disk.root/'Desktop');w=d.window('Files',f);QTest.qWait(20)
 for widget in [f.icons,f.list]:
  f.mode='icons' if widget is f.icons else 'list';f.stack.setCurrentWidget(widget)
  for i in range(widget.count() if widget is f.icons else widget.topLevelItemCount()):
   item=widget.item(i) if widget is f.icons else widget.topLevelItem(i);item.setSelected(True)
  item=widget.item(0) if widget is f.icons else widget.topLevelItem(0)
  pos=widget.visualItemRect(item).center();menu=f.context_menu(widget,pos);action(menu,'Copy').trigger();assert len(d.context_clipboard[0])>=2
 text=SimpleText(d);text.editor.setPlainText('standard text');text.editor.selectAll();menu=text.editor.createStandardContextMenu();assert any('Copy' in a.text() for a in menu.actions())
 assert all(b.contextMenuPolicy()==Qt.CustomContextMenu for b in d.icons)
 captured=[]
 def inspect_popup():
  menu=QApplication.activePopupWidget();assert menu is not None;captured.append([a.text() for a in menu.actions()]);menu.close()
 QTimer.singleShot(10,inspect_popup);f.context(f.icons,f.icons.visualItemRect(f.icons.item(0)).center());assert 'Copy' in captured[-1]
 QTimer.singleShot(10,inspect_popup);w.bar.contextMenuEvent(QContextMenuEvent(QContextMenuEvent.Mouse,QPoint(10,10),w.bar.mapToGlobal(QPoint(10,10))));assert 'Close' in captured[-1] and 'Move to Workspace' in captured[-1]
 QTimer.singleShot(10,inspect_popup);d.fixed_icon_menu(d.icons[-1],'Trash',lambda:None,QPoint(5,5));assert 'Empty Trash…' in captured[-1]
 # Exercise the actual background mouse gesture, not only the menu builder.
 for pos in [QPoint(1050,600),QPoint(600,740)]:
  QTimer.singleShot(10,inspect_popup);QTest.mouseClick(d.area.viewport(),Qt.RightButton,Qt.NoModifier,pos)
  assert 'New Folder…' in captured[-1] and 'Settings…' in captured[-1]
 assert not errors,errors
 d.quitting=True;d.hide()
print('Context menu checks passed')
