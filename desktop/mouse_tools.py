import json
from pathlib import Path
from PySide6.QtCore import Qt,QMimeData,QPoint,QTimer
from PySide6.QtGui import QDrag,QGuiApplication,QCursor,QPixmap,QPainter,QColor,QPen
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
        if target in paths or not target.is_dir() or target.name.endswith('.app'):target=self.owner.path
        if paths and target==self.owner.path and all(p.parent==target for p in paths) and not e.modifiers()&Qt.ControlModifier:
            selected=[self.item(i) for i in range(self.count()) if Path(self.item(i).data(Qt.UserRole)) in paths]
            if selected:
                origin=self.visualItemRect(selected[0]).topLeft();delta=e.position().toPoint()-origin
                for selected_item in selected:
                    point=self.visualItemRect(selected_item).topLeft()+delta
                    point.setX(max(0,round(point.x()/25)*25));point.setY(max(0,round(point.y()/25)*25))
                    self.setPositionForIndex(point,self.indexFromItem(selected_item))
                from classic_files import remember
                remember(self.owner)
            e.acceptProposedAction()
        elif paths and self.owner.managed:self.owner.d.transfer_paths(paths,target,bool(e.modifiers()&Qt.ControlModifier));e.acceptProposedAction()
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
        super().__init__(parent);self.setObjectName('desktopFileIcon');self.d=d;self.press=None;self.moved=False;self.setCheckable(True);self.setAcceptDrops(True)
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
def beachball_frame(angle=0):
    """Original spinning Mac OS X-inspired busy indicator."""
    canvas=QPixmap(32,32);canvas.fill(Qt.transparent)
    painter=QPainter(canvas);painter.setRenderHint(QPainter.Antialiasing)
    hues=['#e5484d','#f49d37','#e6d542','#4bb66b','#3b9cdb','#8754c6']
    for i,color in enumerate(hues):
        painter.setPen(Qt.NoPen);painter.setBrush(QColor(color))
        painter.drawPie(3,3,26,26,(90+angle-i*60)*16,-60*16)
    painter.setPen(QPen(QColor('#242424'),1.5));painter.setBrush(QColor('#f5f5f5'))
    painter.drawEllipse(11,11,10,10)
    painter.end()
    return QCursor(canvas,16,16)

class BeachballAnimator:
    """Animate only while Qt's normal wait cursor is active."""
    def __init__(self,app):
        self.app=app;self.angle=0;self.active=False
        self.timer=QTimer(app);self.timer.timeout.connect(self.tick);self.timer.start(90)
    def tick(self):
        current=self.app.overrideCursor()
        if current is None:
            self.active=False;return
        if not self.active and current.shape()!=Qt.WaitCursor:return
        self.active=True;self.angle=(self.angle+24)%360
        self.app.changeOverrideCursor(beachball_frame(self.angle))

def mouse_cursor(style):
    """Only the Classic Arrow replaces the normal pointer."""
    if style != 'Classic Arrow':return QCursor(Qt.ArrowCursor)
    canvas=QPixmap(32,32);canvas.fill(Qt.transparent)
    painter=QPainter(canvas);painter.setRenderHint(QPainter.Antialiasing)
    from PySide6.QtGui import QPolygon
    painter.setPen(QPen(QColor('#111111'),2));painter.setBrush(QColor('#ffffff'))
    painter.drawPolygon(QPolygon([QPoint(3,2),QPoint(3,26),QPoint(9,20),QPoint(14,29),QPoint(19,26),QPoint(14,17),QPoint(23,16)]))
    painter.end();return QCursor(canvas,3,2)

class MousePreferences(QWidget):
    app_name='Mouse'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Mouse options apply inside Macaque.'))
        layout.addWidget(QLabel('Pointer style'))
        pointer=QComboBox();pointer.addItems(['System Default','Classic Arrow','Mac OS X Beachball (Busy)']);pointer.setCurrentText('Mac OS X Beachball (Busy)' if d.state.get('mouse_style')=='Rainbow Wheel' else d.state.get('mouse_style','System Default'));pointer.currentTextChanged.connect(lambda value:self.save('mouse_style',value));layout.addWidget(pointer)
        layout.addWidget(QLabel('Mac OS X Beachball is a busy cursor, not the regular pointer.'))
        for key,title,default in [('single_click','Single-click desktop icons and file items',False),('snap_icons','Snap dragged desktop icons to a grid',False),('spring_folders','Spring-loaded folders while dragging',True)]:
            b=QCheckBox(title);b.setChecked(d.state.get(key,default));b.toggled.connect(lambda value,k=key:self.save(k,value));layout.addWidget(b)
        for key,title,low,high,default in [('double_click_ms','Double-click interval (ms)',200,1000,400),('drag_distance','Drag threshold (pixels)',3,30,10),('spring_delay_ms','Spring-loaded folder delay (ms)',300,2000,700)]:
            layout.addWidget(QLabel(title));spin=QSpinBox();spin.setRange(low,high);spin.setValue(d.state.get(key,default));spin.valueChanged.connect(lambda value,k=key:self.save(k,value));layout.addWidget(spin)
        layout.addWidget(QLabel('Double-click a window title bar'));combo=QComboBox();combo.addItems(['Roll up','Zoom']);combo.setCurrentIndex(1 if d.state.get('title_double')=='Zoom' else 0);combo.currentTextChanged.connect(lambda value:self.save('title_double',value));layout.addWidget(combo);layout.addWidget(QLabel('Drag desktop icons to arrange them.\nShift-drag desktop files into folders.\nDrag files between Macaque Files windows; Ctrl-drop copies.\nDrop files on Trash to move them to the recoverable Trash.\nShift/Ctrl select multiple files. Host folders remain read only.'));layout.addStretch()
    def save(self,key,value):self.d.state[key]=value;self.d.apply_mouse();self.d.persist()
