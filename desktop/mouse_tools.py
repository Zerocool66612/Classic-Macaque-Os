import json
from pathlib import Path
from PySide6.QtCore import Qt,QMimeData,QPoint,QTimer
from PySide6.QtGui import QDrag,QGuiApplication
from PySide6.QtWidgets import *
MIME='application/x-macaque-files'
def paths_from(mime):
    if not mime.hasFormat(MIME):return []
    try:
        values=json.loads(bytes(mime.data(MIME)))
        return [Path(p) for p in values] if isinstance(values,list) and all(isinstance(p,str) for p in values) else []
    except (ValueError,TypeError):return []
def file_drag(widget,paths):
    mime=QMimeData();mime.setData(MIME,json.dumps([str(p) for p in paths]).encode());drag=QDrag(widget);drag.setMimeData(mime)
    try:return drag.exec(Qt.CopyAction|Qt.MoveAction,Qt.MoveAction)
    finally:
        for view in QApplication.allWidgets():
            spring=getattr(view,'spring',None)
            if isinstance(spring,SpringFolders):spring.finish()
class SpringFolders:
    """Temporary navigation shared by icon and list views of one Finder."""
    def __init__(self, owner):
        self.owner=owner;self.target=None;self.original=None
        self.hover_timer=QTimer(owner);self.hover_timer.setSingleShot(True);self.hover_timer.timeout.connect(self.open_hovered)
        self.leave_timer=QTimer(owner);self.leave_timer.setSingleShot(True);self.leave_timer.timeout.connect(self.finish)
    def hover(self, target, sources):
        self.leave_timer.stop()
        try:
            target=Path(target) if target else None
            valid=(self.owner.d.state.get('spring_folders',True) and target and target.is_dir()
                   and not target.name.endswith('.app') and target.resolve().is_relative_to(self.owner.d.disk.root.resolve())
                   and all(target.resolve()!=p.resolve() and not target.resolve().is_relative_to(p.resolve()) for p in sources))
        except OSError:valid=False
        if not valid:target=None
        if target==self.target:return
        self.hover_timer.stop();self.target=target
        if target:self.hover_timer.start(max(300,min(2000,int(self.owner.d.state.get('spring_delay_ms',700)))))
    def open_hovered(self):
        target=self.target;self.target=None
        if not target or not target.is_dir():return
        if self.original is None:self.original=(self.owner.path,list(self.owner.history),list(self.owner.future))
        self.owner.path=target;self.owner.refresh()
    def leave(self):
        self.hover_timer.stop();self.target=None;self.leave_timer.start(200)
    def finish(self):
        self.hover_timer.stop();self.leave_timer.stop();self.target=None
        if self.original is not None:
            self.owner.path,self.owner.history,self.owner.future=self.original;self.original=None;self.owner.refresh()

class SpringView:
    def spring_target(self,e):
        item=self.itemAt(e.position().toPoint())
        return Path(item.data(0,Qt.UserRole) if isinstance(self,QTreeWidget) else item.data(Qt.UserRole)) if item else None
    def dragMoveEvent(self,e):
        self.dragEnterEvent(e)
        self.owner.spring.hover(self.spring_target(e) if e.isAccepted() else None,paths_from(e.mimeData()))
    def dragLeaveEvent(self,e):
        self.owner.spring.leave();e.accept()

class FileIcons(SpringView,QListWidget):
    def __init__(self,owner):super().__init__();self.owner=owner;self.setDragEnabled(True);self.setAcceptDrops(True);self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    def dragMoveEvent(self,e):SpringView.dragMoveEvent(self,e)
    def dragLeaveEvent(self,e):SpringView.dragLeaveEvent(self,e)
    def startDrag(self,actions):file_drag(self,[Path(i.data(Qt.UserRole)) for i in self.selectedItems()])
    def dragEnterEvent(self,e):
        if paths_from(e.mimeData()) and self.owner.managed:e.acceptProposedAction()
        else:e.ignore()
    def dropEvent(self,e):
        self.owner.spring.hover_timer.stop();QTimer.singleShot(0,self.owner.spring.finish)
        paths=paths_from(e.mimeData());item=self.itemAt(e.position().toPoint());target=Path(item.data(Qt.UserRole)) if item else self.owner.path
        if not target.is_dir() or target.name.endswith('.app'):target=self.owner.path
        if paths and self.owner.managed:self.owner.d.transfer_paths(paths,target,bool(e.modifiers()&Qt.ControlModifier));e.acceptProposedAction()
        else:e.ignore()
class FileList(SpringView,QTreeWidget):
    def __init__(self,owner):super().__init__();self.owner=owner;self.setDragEnabled(True);self.setAcceptDrops(True);self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    def dragMoveEvent(self,e):SpringView.dragMoveEvent(self,e)
    def dragLeaveEvent(self,e):SpringView.dragLeaveEvent(self,e)
    def startDrag(self,actions):file_drag(self,[Path(i.data(0,Qt.UserRole)) for i in self.selectedItems()])
    def dragEnterEvent(self,e):
        if paths_from(e.mimeData()) and self.owner.managed:e.acceptProposedAction()
        else:e.ignore()
    def dropEvent(self,e):
        self.owner.spring.hover_timer.stop();QTimer.singleShot(0,self.owner.spring.finish)
        paths=paths_from(e.mimeData());item=self.itemAt(e.position().toPoint());target=Path(item.data(0,Qt.UserRole)) if item else self.owner.path
        if not target.is_dir() or target.name.endswith('.app'):target=self.owner.path
        if paths and self.owner.managed:self.owner.d.transfer_paths(paths,target,bool(e.modifiers()&Qt.ControlModifier));e.acceptProposedAction()
        else:e.ignore()
class DesktopIcon(QToolButton):
    def __init__(self,d,parent):
        super().__init__(parent);self.d=d;self.press=None;self.moved=False;self.setCheckable(True);self.setAcceptDrops(True)
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:self.press=e.position().toPoint();self.moved=False
        super().mousePressEvent(e)
    def mouseMoveEvent(self,e):
        if self.press is not None and e.buttons()&Qt.LeftButton:
            if not self.moved and (e.position().toPoint()-self.press).manhattanLength()<self.d.state.get('drag_distance',10):return
            self.moved=True
            # Shift-drag a desktop file to a Finder window or another destination.
            path=self.property('filePath')
            if path and e.modifiers()&Qt.ShiftModifier:file_drag(self,[Path(path)]);self.press=None;return
            pos=self.pos()+e.position().toPoint()-self.press;self.move(max(0,min(self.parentWidget().width()-self.width(),pos.x())),max(0,min(self.parentWidget().height()-self.height(),pos.y())))
        else:super().mouseMoveEvent(e)
    def mouseReleaseEvent(self,e):
        moved=self.moved;self.press=None
        if moved:
            if self.d.state.get('snap_icons',False):self.move(round(self.x()/20)*20,round(self.y()/20)*20)
            self.d.state.setdefault('icon_positions',{})[self.property('iconKey')]=[self.x(),self.y()];self.d.persist();self.setDown(False)
        else:
            super().mouseReleaseEvent(e)
            if e.button()==Qt.LeftButton and self.d.state.get('single_click',False) and not self.property('suppressSingle') and not e.modifiers()&(Qt.ControlModifier|Qt.ShiftModifier):self.property('desktopCallback')()
            self.setProperty('suppressSingle',False)
        self.moved=False
    def dragEnterEvent(self,e):
        if paths_from(e.mimeData()) and self.property('dropTarget'):e.acceptProposedAction()
        else:e.ignore()
    def dragMoveEvent(self,e):self.dragEnterEvent(e)
    def dropEvent(self,e):
        target=self.property('dropTarget');paths=paths_from(e.mimeData())
        if paths and target:
            if target=='trash':self.d.trash_paths(paths)
            else:self.d.transfer_paths(paths,Path(target),bool(e.modifiers()&Qt.ControlModifier))
            e.acceptProposedAction()
class MousePreferences(QWidget):
    app_name='Mouse'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Mouse options apply inside Macaque.'))
        for key,title,default in [('single_click','Single-click desktop icons and file items',False),('snap_icons','Snap dragged desktop icons to a grid',False),('spring_folders','Spring-loaded folders while dragging',True)]:
            b=QCheckBox(title);b.setChecked(d.state.get(key,default));b.toggled.connect(lambda value,k=key:self.save(k,value));layout.addWidget(b)
        for key,title,low,high,default in [('double_click_ms','Double-click interval (ms)',200,1000,400),('drag_distance','Drag threshold (pixels)',3,30,10),('spring_delay_ms','Spring-loaded folder delay (ms)',300,2000,700)]:
            layout.addWidget(QLabel(title));spin=QSpinBox();spin.setRange(low,high);spin.setValue(d.state.get(key,default));spin.valueChanged.connect(lambda value,k=key:self.save(k,value));layout.addWidget(spin)
        layout.addWidget(QLabel('Double-click a window title bar'));combo=QComboBox();combo.addItems(['Roll up','Zoom']);combo.setCurrentIndex(1 if d.state.get('title_double')=='Zoom' else 0);combo.currentTextChanged.connect(lambda value:self.save('title_double',value));layout.addWidget(combo);layout.addWidget(QLabel('Drag desktop icons to arrange them.\nShift-drag desktop files into folders.\nDrag files between Macaque Files windows; Ctrl-drop copies.\nDrop files on Trash to move them to the recoverable Trash.\nShift/Ctrl select multiple files. Host folders remain read only.'));layout.addStretch()
    def save(self,key,value):self.d.state[key]=value;self.d.apply_mouse();self.d.persist()
