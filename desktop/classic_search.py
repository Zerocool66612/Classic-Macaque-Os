"""Search only the managed Classic volume. Never query host search services."""
import os
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QSize,QEvent
from PySide6.QtWidgets import *
from model import APP_NAMES
from creative_apps import CREATIVE_APPS
from visuals import icon,app_kind

def classic_files(root,query,limit=250,examined_limit=10000):
    root=Path(root).resolve();results=[];examined=0;truncated=False
    for parent,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not d.startswith('.') and not (Path(parent)/d).is_symlink())
        for name in dirs+sorted(files):
            p=Path(parent)/name;examined+=1
            if examined>examined_limit:return results,True
            if name.startswith('.') or p.is_symlink():continue
            try:
                if not p.resolve().is_relative_to(root):continue
            except OSError:continue
            if query.casefold() in name.casefold():
                results.append(p)
                if len(results)>=limit:return results,True
        # Application aliases are directories; don't walk inside them.
        dirs[:]=[name for name in dirs if not name.endswith('.app')]
    return results,truncated

class ClassicSearch(QWidget):
    app_name='Macaque Search'
    def __init__(self,d):
        super().__init__();self.d=d;self.entries=[];layout=QVBoxLayout(self);heading=QLabel('Search Classic');heading.setStyleSheet('font-size:21px;font-weight:bold');layout.addWidget(heading);layout.addWidget(QLabel('Apps, files and folders on Macaque HD · no host-desktop search'))
        self.input=QLineEdit();self.input.setPlaceholderText('Search the classic system…');self.input.installEventFilter(self);layout.addWidget(self.input);self.scope=QComboBox();self.scope.addItems(['Everything in Classic','Applications','Files and folders']);layout.addWidget(self.scope);self.results=QListWidget();self.results.setIconSize(QSize(24,24));layout.addWidget(self.results,1);self.status=QLabel('Type a name to search.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.search);self.input.textChanged.connect(lambda:self.timer.start(150));self.scope.currentIndexChanged.connect(self.search);self.input.returnPressed.connect(self.activate);self.results.itemActivated.connect(lambda _:self.activate());d.disk_changed.connect(self.search);self.search()
    def eventFilter(self,watched,event):
        if watched==self.input and event.type()==QEvent.KeyPress and event.key() in (Qt.Key_Down,Qt.Key_Up):
            if self.timer.isActive():self.search()
            if self.results.count():self.results.setFocus();self.results.setCurrentRow(0 if event.key()==Qt.Key_Down else self.results.count()-1)
            return True
        return super().eventFilter(watched,event)
    def add(self,label,detail,kind,callback):
        item=QListWidgetItem(icon(kind),label+'  ·  '+detail);item.setData(Qt.UserRole,len(self.entries));self.entries.append(callback);self.results.addItem(item)
    def search(self,*args):
        self.timer.stop();query=self.input.text().casefold().strip();self.results.clear();self.entries=[];scope=self.scope.currentIndex();truncated=False
        if scope in (0,1):
            for name in APP_NAMES:
                if query in name.casefold():self.add(name,'Optional creative app' if name in CREATIVE_APPS else 'Classic application',app_kind(name),lambda n=name:self.d.launch(n))
        if scope in (0,2) and query:
            paths,truncated=classic_files(self.d.disk.root,query)
            for path in paths:
                if path.name.endswith('.app'):continue
                self.add(path.name,str(path.relative_to(self.d.disk.root)),'folder' if path.is_dir() else 'note',lambda p=path:self.d.open_item(p))
        self.status.setText(f'{self.results.count()} results · Macaque HD only'+(' · result/scan limit reached; use a more specific name' if truncated else ''))
        if self.results.count():self.results.setCurrentRow(0)
    def activate(self):
        if self.timer.isActive():self.search()
        item=self.results.currentItem()
        if item:
            callback=self.entries[item.data(Qt.UserRole)];callback()
