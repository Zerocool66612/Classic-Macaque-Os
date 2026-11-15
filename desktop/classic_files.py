"""Classic Finder metadata. Aliases are data, never executable launchers."""
import json, os, stat
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QFormLayout,QLabel,QLineEdit,
    QPushButton,QCheckBox,QComboBox,QFileDialog,QListWidget,QAbstractItemView,QMessageBox)

LABELS={'None':None,'Essential':'#c94949','Hot':'#e18b35','In Progress':'#c4ac35',
        'Personal':'#4a9c62','Project':'#4886c5','Cool':'#9561b6','Review':'#888888'}

def key(d,path):return str(Path(path).absolute())
def file_key(path):
    st=Path(path).stat();return f'{st.st_dev}:{st.st_ino}'
def metadata(d,path):
    try:return d.state.setdefault('file_metadata',{}).get(file_key(path),{})
    except OSError:return {}
def set_metadata(d,path,**values):
    d.disk.editable(path)
    d.state.setdefault('file_metadata',{}).setdefault(file_key(path),{}).update(values)
    d.persist();d.disk_changed.emit()
def is_alias(path):return Path(path).suffix=='.mcalias'
def alias_target(d,path):
    path=d.disk.inside(path)
    if path.stat().st_size>16384:raise ValueError('Invalid alias.')
    data=json.loads(path.read_text())
    if data.get('format')!='macaque-alias-1':raise ValueError('Invalid alias.')
    target=d.disk.inside(d.disk.root/data['target'])
    if target==path or is_alias(target):raise ValueError('Aliases cannot point to another alias.')
    identity_matches=not data.get('identity') or (target.exists() and file_key(target)==data['identity'])
    if not identity_matches and data.get('identity'):
        # Find renamed originals without following symlinks or leaving Macaque HD.
        pending=[d.disk.root];count=0
        while pending and count<10000:
            folder=pending.pop()
            try:
                for candidate in folder.iterdir():
                    count+=1
                    if count>10000:break
                    if candidate.is_symlink():continue
                    if file_key(candidate)==data['identity']:return candidate
                    if candidate.is_dir():pending.append(candidate)
            except OSError:continue
        if target.exists():raise FileNotFoundError('The original was replaced. Locate it again.')
    return target

def make_alias(d,path):
    target=d.disk.inside(path)
    if is_alias(target):target=alias_target(d,target)
    destination=d.disk.unused(target.with_name(target.name+' alias.mcalias'))
    try:d.disk.editable(destination)
    except ValueError:destination=d.disk.unused(d.disk.root/'Desktop'/destination.name);d.disk.editable(destination)
    with destination.open('x') as f:json.dump({'format':'macaque-alias-1','target':str(target.relative_to(d.disk.root)),'identity':file_key(target),'folder':target.is_dir()},f)
    d.disk_changed.emit();return destination

def resolve_alias(d,path):
    try:
        target=alias_target(d,path)
        if target.exists():return target
    except FileNotFoundError:pass
    data=json.loads(Path(path).read_text())
    if data.get('folder'):chosen=QFileDialog.getExistingDirectory(d,'Locate Original Folder',str(d.disk.root))
    else:chosen,_=QFileDialog.getOpenFileName(d,'Locate Original',str(d.disk.root),'All files (*)')
    if not chosen:return None
    target=d.disk.inside(chosen)
    if is_alias(target):raise ValueError('Choose the original, rather than another alias.')
    d.disk.editable(path)
    d.disk.write_json(Path(path),{'format':'macaque-alias-1','target':str(target.relative_to(d.disk.root)),'identity':file_key(target),'folder':target.is_dir()})
    return target

def remember(f):
    if not f.window or getattr(f.spring,'original',None):return
    w=f.window
    geometry=w.normalGeometry() if w.isMaximized() else w.geometry()
    if w.shaded:
        geometry.setSize(w.saved_size)
    value={'geometry':[geometry.x(),geometry.y(),geometry.width(),geometry.height()],
        'mode':f.mode,'sort':f.sort_mode,'hidden':f.show_hidden,
        'positions':{str(f.icons.item(i).data(Qt.UserRole)): [f.icons.visualItemRect(f.icons.item(i)).x(),f.icons.visualItemRect(f.icons.item(i)).y()] for i in range(f.icons.count())}}
    f.d.state.setdefault('folder_views',{})[key(f.d,f.path)]=value;f.d.persist()

def restore(f):
    value=f.d.state.get('folder_views',{}).get(key(f.d,f.path),{})
    f.mode=value.get('mode','icons');f.stack.setCurrentIndex(1 if f.mode=='list' else 0)
    f.switch.setText('Icon View' if f.mode=='list' else 'List View')
    f.sort_mode=value.get('sort','Name');f.sort.blockSignals(True);f.sort.setCurrentText(f.sort_mode);f.sort.blockSignals(False)
    f.show_hidden=bool(value.get('hidden',False));f.hidden.blockSignals(True);f.hidden.setChecked(f.show_hidden);f.hidden.blockSignals(False)
    if f.window and len(value.get('geometry',[]))==4:
        x,y,w,h=value['geometry'];area=f.d.area.viewport()
        f.window.resize(max(280,min(w,area.width())),max(200,min(h,area.height())))
        f.window.move(max(0,min(x,area.width()-100)),max(0,min(y,area.height()-60)))

def decorate(f):
    positions=f.d.state.get('folder_views',{}).get(key(f.d,f.path),{}).get('positions',{})
    for i in range(f.icons.count()):
        item=f.icons.item(i);path=Path(item.data(Qt.UserRole));row=f.list.topLevelItem(i)
        data=metadata(f.d,path);color=LABELS.get(data.get('label'))
        if color:item.setForeground(QColor(color));row.setForeground(0,QColor(color))
        if is_alias(path):
            item.setText('↗ '+path.stem);row.setText(0,'↗ '+path.stem);row.setText(1,'Alias')
        if data.get('stationery'):item.setToolTip('Stationery pad · opens a new copy');row.setText(1,'Stationery pad')
        custom=data.get('icon')
        if custom and Path(custom).is_file():item.setIcon(QIcon(custom));row.setIcon(0,QIcon(custom))
        position=positions.get(str(path))
        if position and f.mode=='icons' and not f.filter.text():f.icons.setPositionForIndex(QPoint(*position),f.icons.indexFromItem(item))

def clean_up(f):
    f.d.state.setdefault('folder_views',{}).setdefault(key(f.d,f.path),{})['positions']={}
    f.icons.setMovement(QListWidget.Static);f.icons.doItemsLayout();f.icons.setMovement(QListWidget.Free);remember(f);f.refresh()

def info_panel(d,path):
    path=Path(path);st=path.stat();panel=QWidget();layout=QVBoxLayout(panel);form=QFormLayout();layout.addLayout(form)
    name=QLabel(path.name);name.setTextFormat(Qt.PlainText);form.addRow('Name',name)
    kind='Alias' if is_alias(path) else 'Folder' if path.is_dir() else 'Document'
    for label,value in [('Kind',kind),('Size',d.format_bytes(st.st_size)+(' (folder entry)' if path.is_dir() else '')),('Location',str(path.parent)),('Modified',d.file_date(st.st_mtime)),('Permissions',stat.filemode(st.st_mode))]:
        text=QLabel(value);text.setTextFormat(Qt.PlainText);text.setWordWrap(True);text.setTextInteractionFlags(Qt.TextSelectableByMouse);form.addRow(label,text)
    editable=d.editable_paths([path]);data=metadata(d,path)
    labels=QComboBox();labels.addItems(LABELS);labels.setCurrentText(data.get('label','None'));labels.setEnabled(editable);form.addRow('Label',labels)
    stationery=QCheckBox('Stationery pad — open a new copy');stationery.setChecked(bool(data.get('stationery')));stationery.setEnabled(editable and path.is_file() and not is_alias(path));layout.addWidget(stationery)
    icons=QPushButton('Choose Custom Icon…');icons.setEnabled(editable);layout.addWidget(icons)
    def choose():
        source,_=QFileDialog.getOpenFileName(panel,'Choose Icon',str(d.disk.root),'Images (*.png *.jpg *.svg *.webp)')
        if source:
            import shutil,uuid
            folder=d.base/'file-icons';folder.mkdir(exist_ok=True);dest=folder/(uuid.uuid4().hex+Path(source).suffix)
            if Path(source).stat().st_size>5*1024*1024:raise ValueError('Icon must be under 5 MB.')
            shutil.copyfile(source,dest);set_metadata(d,path,icon=str(dest))
    icons.clicked.connect(lambda:d.operation(choose))
    reset=QPushButton('Reset Icon');reset.setEnabled(editable);reset.clicked.connect(lambda:d.operation(lambda:set_metadata(d,path,icon=None)));layout.addWidget(reset)
    apply=QPushButton('Apply');apply.setEnabled(editable);apply.clicked.connect(lambda:d.operation(lambda:set_metadata(d,path,label=labels.currentText(),stationery=stationery.isChecked())));layout.addWidget(apply)
    layout.addStretch();return panel

def running_menu(d,menu):
    menu.clear();active=d.area.activeSubWindow()
    def app_name(w):return getattr(w.content,'app_name',w.windowTitle())
    def hide(others=False):
        for w in d.area.subWindowList():
            same=app_name(w)==app_name(active)
            if (not same) if others else same:w.setProperty('classic_hidden',True);w.hide()
    def show_all():
        for w in d.area.subWindowList():
            if w.property('classic_hidden'):
                w.setProperty('classic_hidden',False);w.setVisible(w.property('workspace')==d.workspace)
    menu.addAction('Hide Application',lambda:hide()).setEnabled(active is not None)
    menu.addAction('Hide Others',lambda:hide(True)).setEnabled(active is not None)
    menu.addAction('Show All',show_all)
    menu.addSeparator()
    for w in d.area.subWindowList():
        a=menu.addAction(('◇ ' if w.property('classic_hidden') else '')+w.windowTitle(),lambda checked=False,w=w:(w.setProperty('classic_hidden',False),d.activate_window(w)))
        a.setCheckable(True);a.setChecked(w is active)
