import os,tempfile,json,zipfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtCore import Qt,QPoint,QPointF,QEvent,QMimeData
from PySide6.QtGui import QMouseEvent,QDropEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from unittest.mock import patch
import chess
from desktop import Desktop
from model import Disk,APP_NAMES
from mouse_tools import MIME
from wallpapers import NAMES,render
app=QApplication([]);app.setOrganizationName('MacaqueTests');app.setApplicationName('Expansion09')
with tempfile.TemporaryDirectory() as temp:
 d=Desktop(temp);d.show();app.processEvents();d.error=lambda ex:(_ for _ in ()).throw(AssertionError(str(ex)))
 assert 'Blender' not in APP_NAMES
 for w in d.area.subWindowList():w.close()
 # Legal move handling, undo, checkmate, special rules and saved game reopening.
 w=d.launch('Chess');game=w.content;game.set_mode(1);game.click(chess.E2);game.click(chess.E5);assert not game.board.move_stack
 game.click(chess.E2);game.click(chess.E4);assert game.board.peek()==chess.Move.from_uci('e2e4');game.undo();assert not game.board.move_stack
 for move in ['f2f3','e7e5','g2g4','d8h4']:game.board.push_uci(move)
 game.refresh();assert 'Game over' in game.status.text();game.save();w.close();w=d.launch('Chess');assert w.content.board.is_checkmate();w.close()
 b=chess.Board('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');assert chess.Move.from_uci('e1g1') in b.legal_moves
 b=chess.Board('8/8/8/3pP3/8/8/8/4K2k w - d6 0 1');assert b.is_en_passant(chess.Move.from_uci('e5d6'))
 # Persistent Tasks.
 w=d.launch('Tasks');w.content.add('Test the new desktop');w.content.items.item(0).setCheckState(Qt.Checked);w.close();w=d.launch('Tasks');assert w.content.items.item(0).checkState()==Qt.Checked;w.close()
 # Paint stroke/undo really change pixels.
 w=d.launch('Macaque Paint');canvas=w.content.canvas;before=canvas.image.copy();QTest.mousePress(canvas,Qt.LeftButton,pos=QPoint(20,20));QTest.mouseRelease(canvas,Qt.LeftButton,pos=QPoint(20,20));assert canvas.image!=before;canvas.revert();assert canvas.image==before;canvas.dirty=False;w.close()
 # Actual Finder drop handler: move then Ctrl-copy, no overwrites.
 source=d.disk.root/'Documents'/'drag.txt';source.write_text('keep this');target=d.disk.new_folder(d.disk.root,'Drop target');finder=d.open_finder(target).content
 assert finder.icons.dragEnabled() and finder.list.dragEnabled()
 mime=QMimeData();mime.setData(MIME,json.dumps([str(source)]).encode());event=QDropEvent(QPointF(5,5),Qt.MoveAction,mime,Qt.LeftButton,Qt.NoModifier);finder.icons.dropEvent(event);assert (target/source.name).read_text()=='keep this' and not source.exists()
 copied=target/source.name;mime.setData(MIME,json.dumps([str(copied)]).encode());other=d.open_finder(d.disk.root/'Documents').content;event=QDropEvent(QPointF(5,5),Qt.CopyAction,mime,Qt.LeftButton,Qt.ControlModifier);other.icons.dropEvent(event);assert copied.exists() and source.exists()
 try:d.disk.move_to(target,target/'inside')
 except (ValueError,OSError):pass
 else:raise AssertionError('recursive move was allowed')
 try:d.disk.move_to(d.disk.root/'Applications',d.disk.root/'Documents')
 except ValueError:pass
 else:raise AssertionError('protected move was allowed')
 # Desktop icon position persists after a real mouse drag.
 button=d.icons[0];old=button.pos();QTest.mousePress(button,Qt.LeftButton,pos=QPoint(20,20))
 move=QMouseEvent(QEvent.MouseMove,QPointF(70,70),QPointF(button.mapToGlobal(QPoint(70,70))),Qt.NoButton,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(button,move);QTest.mouseRelease(button,Qt.LeftButton,pos=QPoint(70,70));assert button.pos()!=old;assert 'Macaque HD' in d.state['icon_positions'];saved=button.pos();d.arrange_icons();assert button.pos()==saved
 # Mouse preference actually affects Qt and desktop launch mode.
 d.state['double_click_ms']=650;d.state['drag_distance']=15;d.apply_mouse();assert app.doubleClickInterval()==650 and app.startDragDistance()==15
 with patch.object(d,'open_finder') as open_folder:
  d.state['single_click']=True;QTest.mouseClick(button,Qt.LeftButton);open_folder.assert_called_once()
 d.state['single_click']=False
 for name in ['Clockwork','Media Player','Archive Viewer','Character Map','Teapot Studio','Wallpapers','Mouse']:
  w=d.launch(name);app.processEvents();assert not w.grab().isNull()
  if name=='Teapot Studio':assert len(w.content.view.faces)>500;w.content.view.tick();assert not w.content.view.grab().isNull()
  if name=='Archive Viewer':
   path=Path(temp)/'sample.zip'
   with zipfile.ZipFile(path,'w') as z:z.writestr('../never-extract.txt','safe listing only')
   w.content.load(path);assert w.content.items.topLevelItemCount()==1;assert not (Path(temp).parent/'never-extract.txt').exists()
  w.close()
 for name in NAMES:assert not render(name,320,180).isNull()
 # Wallpaper preference survives a new Desktop.
 d.change_appearance('wallpaper','Lunar Peaks');d.close();app.processEvents();d=Desktop(temp);assert d.state['wallpaper']=='Lunar Peaks';d.close()
print('PASS: new app construction; chess moves/undo/mate/save; Tasks save; Paint stroke/undo; actual Finder move/copy drop handlers; move guards; desktop mouse drag and saved positions; click preferences; teapot render; ZIP listing; all wallpapers and persistence')
