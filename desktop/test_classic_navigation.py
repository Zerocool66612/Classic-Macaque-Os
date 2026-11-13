import os,tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtCore import Qt,QPointF,QMimeData
from PySide6.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from unittest.mock import patch,MagicMock
from desktop import Desktop
from mouse_tools import MIME
import json
app=QApplication([])
with tempfile.TemporaryDirectory() as t:
 with patch('desktop.SoundTheme',return_value=MagicMock()):d=Desktop(Path(t))
 d.state['reduce_motion']=True;d.show();QTest.qWait(50)
 w=d.launch('Macaque Text');w.content.editor.setPlainText('Unsaved text stays');size=w.size();minimum=w.minimumSize();maximum=w.maximumSize()
 QTest.mouseClick(w.bar.shade_button,Qt.LeftButton);assert w.shaded and w.height()==34 and not w.content.isVisible()
 QTest.mouseClick(w.bar.shade_button,Qt.LeftButton);assert not w.shaded and w.size()==size and w.minimumSize()==minimum and w.maximumSize()==maximum and w.content.editor.toPlainText()=='Unsaved text stays'
 fwin=d.launch('Macaque Files');f=fwin.content;root=d.disk.root/'Documents';outer=root/'Spring';inner=outer/'Nested';inner.mkdir(parents=True);source=root/'sample.txt';source.write_text('drag test');f.open(root);history=list(f.history)
 mime=QMimeData();mime.setData(MIME,json.dumps([str(source)]).encode())
 for view,mode in [(f.icons,'icons'),(f.list,'list')]:
  f.mode=mode;f.stack.setCurrentWidget(view);f.path=root;f.refresh();QTest.qWait(50)
  items=[view.item(i) for i in range(view.count())] if mode=='icons' else [view.topLevelItem(i) for i in range(view.topLevelItemCount())]
  item=next(i for i in items if (i.text() if mode=='icons' else i.text(0))=='Spring')
  rect=view.visualItemRect(item);pos=rect.center()
  enter=QDragEnterEvent(pos,Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier);app.sendEvent(view.viewport(),enter)
  move=QDragMoveEvent(pos,Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier);view.dragMoveEvent(move)
  assert f.spring.hover_timer.isActive();QTest.qWait(750);assert f.path==outer
  f.spring.hover(inner,[source]);QTest.qWait(750);assert f.path==inner
  f.spring.finish();assert f.path==root and f.history==history
 f.mode='icons';f.stack.setCurrentWidget(f.icons);f.path=root;f.refresh()
 f.spring.hover(outer,[source]);QTest.qWait(750)
 with patch.object(d,'transfer_paths') as transfer:
  drop=QDropEvent(QPointF(f.icons.viewport().width()-5,f.icons.viewport().height()-5),Qt.CopyAction,mime,Qt.LeftButton,Qt.ControlModifier)
  f.icons.dropEvent(drop)
  transfer.assert_called_once_with([source],outer,True)
 QTest.qWait(20);assert f.path==root
 f.spring.hover(source.parent,[source.parent]);assert not f.spring.hover_timer.isActive()
 d.state['spring_folders']=False;f.spring.hover(outer,[source]);assert not f.spring.hover_timer.isActive();d.state['spring_folders']=True
 f.spring.hover(outer,[source]);f.spring.leave();QTest.qWait(750);assert f.path==root
 f.spring.hover(outer,[source]);QTest.qWait(750);assert f.path==outer
 f.spring.leave();QTest.qWait(250);assert f.path==root
 w.content.editor.document().setModified(False);d.quitting=True;d.close()
print('PASS: shade button preserves edits/constraints; icon and list drag-hover; nested spring navigation; cancellation and settings.')
