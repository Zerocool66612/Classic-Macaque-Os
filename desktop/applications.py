from pathlib import Path
import json,random,os,calendar
from PySide6.QtCore import Qt,QTimer,QDate,QSize,Signal,QFileSystemWatcher
from PySide6.QtGui import QFont,QTextDocument,QTextCursor,QShortcut,QKeySequence
from PySide6.QtWidgets import *
from model import calculate,APP_NAMES,CONTROL_PANELS
from visuals import icon,app_kind
from mouse_tools import FileIcons,FileList

from menu_compat import Menu as QMenu

class Finder(QWidget):
    app_name='Macaque Files'
    def __init__(self,desktop,path):
        super().__init__();self.d=desktop;self.path=Path(path);self.history=[];self.future=[];self.mode='icons';self.window=None;self.sort_mode='Name';self.show_hidden=False
        layout=QVBoxLayout(self);layout.setContentsMargins(8,6,8,4);layout.setSpacing(6)
        tools=QHBoxLayout();self.back=QPushButton('◀');self.back.setToolTip('Back');self.back.clicked.connect(self.go_back);tools.addWidget(self.back)
        up=QPushButton('↑');up.setToolTip('Enclosing folder');up.clicked.connect(self.go_up);tools.addWidget(up)
        forward=QPushButton('▶');forward.setToolTip('Forward');forward.clicked.connect(self.go_forward);tools.addWidget(forward)
        self.location=QLabel();tools.addWidget(self.location,1)
        refresh=QPushButton('Refresh');refresh.clicked.connect(self.refresh);tools.addWidget(refresh)
        self.new_button=QPushButton('New Folder');self.new_button.clicked.connect(self.new_folder);tools.addWidget(self.new_button)
        self.switch=QPushButton('List View');self.switch.clicked.connect(self.toggle_view);tools.addWidget(self.switch);layout.addLayout(tools)
        self.splitter=QSplitter();layout.addWidget(self.splitter,1);self.sidebar=QListWidget();self.sidebar.setMaximumWidth(170);self.sidebar.itemActivated.connect(lambda item:self.open(Path(item.data(Qt.UserRole))));self.splitter.addWidget(self.sidebar);self.stack=QStackedWidget();self.icons=FileIcons(self);self.icons.setViewMode(QListWidget.IconMode);self.icons.setIconSize(QSize(48,48));self.icons.setGridSize(QSize(125,90));self.icons.setResizeMode(QListWidget.Adjust);self.icons.setMovement(QListWidget.Static);self.icons.setDragEnabled(True);self.icons.setWordWrap(True)
        self.list=FileList(self);self.list.setHeaderLabels(['Name','Kind','Size','Modified']);self.list.setRootIsDecorated(False);self.list.setAlternatingRowColors(True)
        self.stack.addWidget(self.icons);self.stack.addWidget(self.list);self.splitter.addWidget(self.stack);self.splitter.setStretchFactor(1,1)
        navigation=QHBoxLayout();self.address=QLineEdit();self.address.setPlaceholderText('Go to a folder…');self.address.returnPressed.connect(self.go_address);navigation.addWidget(self.address,1);pin=QPushButton('Pin folder');pin.clicked.connect(self.pin_folder);navigation.addWidget(pin);layout.insertLayout(1,navigation)
        options=QHBoxLayout();self.filter=QLineEdit();self.filter.setPlaceholderText('Filter this folder…');self.filter.textChanged.connect(self.refresh);options.addWidget(self.filter,1);self.sort=QComboBox();self.sort.addItems(['Name','Modified','Size','Type']);self.sort.currentTextChanged.connect(self.change_sort);options.addWidget(self.sort);self.hidden=QCheckBox('Hidden files');self.hidden.toggled.connect(self.hidden_changed);options.addWidget(self.hidden);layout.insertLayout(2,options)
        self.status=QLabel();layout.addWidget(self.status);self.watcher=QFileSystemWatcher(self);self.refresh_timer=QTimer(self);self.refresh_timer.setSingleShot(True);self.refresh_timer.timeout.connect(self.refresh);self.watcher.directoryChanged.connect(lambda *a:self.refresh_timer.start(150));self.key_refresh=QShortcut(QKeySequence('F5'),self);self.key_refresh.setContext(Qt.WidgetWithChildrenShortcut);self.key_refresh.activated.connect(self.refresh);self.key_location=QShortcut(QKeySequence('Ctrl+L'),self);self.key_location.setContext(Qt.WidgetWithChildrenShortcut);self.key_location.activated.connect(lambda:(self.address.setFocus(),self.address.selectAll()))
        self.icons.itemDoubleClicked.connect(lambda i:self.open(Path(i.data(Qt.UserRole))) if not self.d.state.get('single_click',False) else None)
        self.icons.itemClicked.connect(lambda i:self.open(Path(i.data(Qt.UserRole))) if self.d.state.get('single_click',False) and not QApplication.keyboardModifiers()&(Qt.ControlModifier|Qt.ShiftModifier) else None)
        self.list.itemClicked.connect(lambda i,c:self.open(Path(i.data(0,Qt.UserRole))) if self.d.state.get('single_click',False) and not QApplication.keyboardModifiers()&(Qt.ControlModifier|Qt.ShiftModifier) else None)
        self.list.itemDoubleClicked.connect(lambda i,c:self.open(Path(i.data(0,Qt.UserRole))) if not self.d.state.get('single_click',False) else None)
        for widget in (self.icons,self.list):widget.setContextMenuPolicy(Qt.CustomContextMenu);widget.customContextMenuRequested.connect(lambda pos,w=widget:self.context(w,pos))
        self.d.disk_changed.connect(self.refresh);self.refresh()
    def attach(self,window):self.window=window;self.refresh()
    def refresh(self,*args):
        selected=self.selected() if hasattr(self,'icons') else None
        if not self.path.exists():self.path=self.d.disk.root
        self.managed=self.path.resolve().is_relative_to(self.d.disk.root.resolve());self.new_button.setEnabled(self.managed);self.icons.clear();self.list.clear();entries=[]
        try:
            entries=list(self.path.iterdir())
            def key(path):
                try:
                    st=path.stat();value=-st.st_mtime if self.sort_mode=='Modified' else -st.st_size if self.sort_mode=='Size' else path.suffix.casefold() if self.sort_mode=='Type' else path.name.casefold()
                except OSError:value=0 if self.sort_mode in ('Modified','Size') else ''
                return (not path.is_dir(),value,path.name.casefold())
            entries.sort(key=key)
        except OSError as ex:self.d.error(ex)
        for p in entries:
            if p.name.startswith('.') and not self.show_hidden:continue
            if self.filter.text().casefold() not in p.name.casefold():continue
            isapp=p.name.endswith('.app');kind=app_kind(p.stem) if isapp else 'folder' if p.is_dir() else 'note';name=p.stem if isapp else p.name
            item=QListWidgetItem(icon(kind),name);item.setData(Qt.UserRole,str(p));item.setToolTip(p.name);self.icons.addItem(item)
            try:
                st=p.stat();size='—' if p.is_dir() else self.d.format_bytes(st.st_size);date=self.d.file_date(st.st_mtime)
            except OSError:size,date='—','—'
            row=QTreeWidgetItem([name,'Application' if isapp else 'Folder' if p.is_dir() else 'Document',size,date]);row.setIcon(0,icon(kind));row.setData(0,Qt.UserRole,str(p));self.list.addTopLevelItem(row)
            if selected==p:self.icons.setCurrentItem(item);self.list.setCurrentItem(row)
        watched=self.watcher.directories()
        if watched!=[str(self.path)]:
            if watched:self.watcher.removePaths(watched)
            self.watcher.addPath(str(self.path))
        self.address.setText(str(self.path));self.refresh_sidebar()
        self.list.resizeColumnToContents(0);self.list.resizeColumnToContents(1);self.location.setText('Macaque HD' if self.path==self.d.disk.root else self.path.name);self.location.setToolTip(str(self.path));self.back.setEnabled(bool(self.history));self.status.setText(f'{self.icons.count()} items · '+('Macaque HD' if self.managed else 'Host folder · read only'))
        if self.window:self.window.rename(self.location.text())
    def selected(self):
        item=self.icons.currentItem() if self.mode=='icons' else self.list.currentItem()
        return Path(item.data(Qt.UserRole) if self.mode=='icons' else item.data(0,Qt.UserRole)) if item else None
    def open(self,path):
        if path.name.endswith('.app') and path.stem in APP_NAMES+CONTROL_PANELS:self.d.launch(path.stem)
        elif path.is_dir():
            self.history.append(self.path);self.future=[];self.path=path;self.refresh();self.d.play_sound('open')
        else:self.d.open_document(path)
    def go_back(self):
        if self.history:self.future.append(self.path);self.path=self.history.pop();self.refresh()
    def refresh_sidebar(self):
        self.sidebar.clear();roots=[('Macaque HD',self.d.disk.root)]+[(name,self.d.disk.root/name) for name in ['Documents','Desktop','Downloads','Pictures','Applications']]
        roots += [(Path(path).name,Path(path)) for path in self.d.state.get('favorite_folders',[])]
        seen=set()
        for title,path in roots:
            if path.exists() and str(path) not in seen:
                item=QListWidgetItem(icon('folder'),title);item.setData(Qt.UserRole,str(path));item.setToolTip(str(path));self.sidebar.addItem(item);seen.add(str(path))
    def pin_folder(self):
        if not self.path.resolve().is_relative_to(self.d.disk.root.resolve()):self.d.error('Pin folders from Macaque HD.');return
        items=self.d.state.setdefault('favorite_folders',[]);path=str(self.path)
        if path in items:items.remove(path)
        else:items.append(path);self.d.state['favorite_folders']=items[-20:]
        self.d.persist();self.refresh_sidebar()
    def go_forward(self):
        if self.future:self.history.append(self.path);self.path=self.future.pop();self.refresh()
    def go_address(self):
        path=Path(self.address.text()).expanduser()
        if path.is_dir():self.open(path)
        else:self.d.error('That folder does not exist.')
    def change_sort(self,mode):self.sort_mode=mode;self.refresh()
    def hidden_changed(self,value):self.show_hidden=value;self.refresh()
    def can_close(self):
        self.refresh_timer.stop()
        if self.watcher.directories():self.watcher.removePaths(self.watcher.directories())
        return True
    def go_up(self):
        if self.path!=self.d.disk.root and self.path.parent!=self.path:self.open(self.path.parent)
    def toggle_view(self):
        self.mode='list' if self.mode=='icons' else 'icons';self.stack.setCurrentIndex(1 if self.mode=='list' else 0);self.switch.setText('Icon View' if self.mode=='list' else 'List View')
    def new_folder(self):
        name,ok=QInputDialog.getText(self,'New Folder','Name:',text='untitled folder')
        if ok:self.d.operation(lambda:self.d.disk.new_folder(self.path,name))
    def rename_selected(self):
        p=self.selected()
        if p:
            name,ok=QInputDialog.getText(self,'Rename','New name:',text=p.name)
            if ok:self.d.operation(lambda:self.d.disk.rename(p,name))
    def duplicate_selected(self):
        p=self.selected()
        if p:self.d.operation(lambda:self.d.disk.duplicate(p))
    def trash_selected(self):
        p=self.selected()
        if p:self.d.operation(lambda:self.d.disk.trash_item(p),'trash')
    def info(self):
        p=self.selected() or self.path;self.d.get_info(p)
    def context_menu(self,widget,pos):
        item=widget.itemAt(pos)
        if item:
            if not item.isSelected():widget.clearSelection();widget.setCurrentItem(item);item.setSelected(True)
            paths=[Path(i.data(Qt.UserRole) if widget is self.icons else i.data(0,Qt.UserRole)) for i in widget.selectedItems()]
        else:widget.clearSelection();paths=[]
        menu=self.d.file_context_menu(paths,self.path,self.open)
        if not item:
            menu.addSeparator();menu.addAction('Refresh',self.refresh);menu.addAction('Select All',widget.selectAll);menu.addAction('Change View',self.toggle_view)
            sort=menu.addMenu('Sort By')
            for name in ['Name','Modified','Size','Type']:sort.addAction(name,lambda checked=False,n=name:self.sort.setCurrentText(n))
            hidden=menu.addAction('Show Hidden Files');hidden.setCheckable(True);hidden.setChecked(self.show_hidden);hidden.toggled.connect(self.hidden.setChecked)
            pin=menu.addAction('Pin / Unpin Folder',self.pin_folder);pin.setEnabled(self.managed)
        return menu
    def context(self,widget,pos):
        menu=self.context_menu(widget,pos);menu.exec(widget.viewport().mapToGlobal(pos))

class SimpleText(QWidget):
    app_name='Macaque Text'
    def __init__(self,d,path=None):
        super().__init__();self.d=d;self.path=Path(path) if path else None;self.window=None
        layout=QVBoxLayout(self);layout.setContentsMargins(5,5,5,4);self.editor=QTextEdit();self.editor.setAcceptRichText(False);self.editor.setFont(QFont('DejaVu Sans Mono',12));layout.addWidget(self.editor,1)
        self.status=QLabel();layout.addWidget(self.status);self.editor.textChanged.connect(self.changed)
        if self.path:self.editor.setPlainText(self.path.read_text());self.editor.document().setModified(False)
        self.changed()
    def attach(self,w):self.window=w;self.changed()
    def changed(self):
        text=self.editor.toPlainText();self.status.setText(f'{len(text.split())} words · {len(text)} characters')
        if self.window:self.window.rename((self.path.name if self.path else 'Untitled')+(' •' if self.editor.document().isModified() else ''))
    def save(self,save_as=False):
        path=self.path
        if save_as or not path:
            result,_=QFileDialog.getSaveFileName(self,'Save Text',str(path or self.d.disk.root/'Documents'/'Untitled.txt'),'Text (*.txt);;All files (*)')
            if not result:return False
            path=Path(result)
        try:
            path.write_text(self.editor.toPlainText());self.path=path;self.editor.document().setModified(False);self.changed();self.d.add_recent(path);self.d.disk_changed.emit();self.d.play_sound('save');return True
        except OSError as ex:self.d.error(ex);return False
    def can_close(self):
        if not self.editor.document().isModified():return True
        choice=QMessageBox.question(self,'Save changes?','Save changes to this document before closing?',QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel,QMessageBox.Save)
        return self.save() if choice==QMessageBox.Save else choice==QMessageBox.Discard
    def find(self):
        text,ok=QInputDialog.getText(self,'Find','Find text:')
        if ok and text:
            if not self.editor.find(text):self.editor.moveCursor(QTextCursor.Start);self.editor.find(text)

class Sticky(QWidget):
    app_name='Macaque Notes'
    def __init__(self,d,key=None):
        super().__init__();self.d=d;self.key=key or d.new_sticky();self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.persist)
        layout=QVBoxLayout(self);layout.setContentsMargins(3,3,3,3);self.editor=QTextEdit();self.editor.setAcceptRichText(False);self.editor.setObjectName('stickyEditor');self.editor.setPlainText(d.stickies.get(self.key,''));layout.addWidget(self.editor);self.editor.textChanged.connect(lambda:self.timer.start(300))
    def persist(self):self.timer.stop();self.d.stickies[self.key]=self.editor.toPlainText();self.d.persist()
    def can_close(self):self.persist();return True

class Calculator(QWidget):
    app_name='Calculator'
    def __init__(self,d):
        super().__init__();layout=QVBoxLayout(self);self.input=QLineEdit();self.input.setAlignment(Qt.AlignRight);self.input.setObjectName('calculatorDisplay');layout.addWidget(self.input);self.input.returnPressed.connect(self.equals)
        self.history=QLabel('Arithmetic · sqrt(x) · pi · e');self.history.setWordWrap(True);layout.addWidget(self.history);grid=QGridLayout();layout.addLayout(grid)
        for i,key in enumerate(['C','(',')','/','7','8','9','*','4','5','6','-','1','2','3','+','0','.','⌫','=']):
            b=QPushButton(key);b.setMinimumSize(53,38);grid.addWidget(b,i//4,i%4);b.clicked.connect(lambda _,k=key:self.press(k))
    def press(self,key):
        if key=='C':self.input.clear()
        elif key=='⌫':self.input.backspace()
        elif key=='=':self.equals()
        else:self.input.insert(key)
    def equals(self):
        try:
            original=self.input.text();result=calculate(original);value=format(result,'.12g');self.input.setText(value);self.history.setText(original+' = '+value)
        except Exception as ex:self.history.setText(str(ex))

class Sherlock(QWidget):
    app_name='Macaque Search'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Macaque Search — Find files on Macaque HD'));self.input=QLineEdit();self.input.setPlaceholderText('File or folder name…');layout.addWidget(self.input);self.results=QListWidget();layout.addWidget(self.results,1);self.status=QLabel('Searches the managed disk; double-click a result to open.');layout.addWidget(self.status)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.search);self.input.textChanged.connect(lambda:self.timer.start(200));self.input.returnPressed.connect(self.search);self.results.itemDoubleClicked.connect(lambda i:d.open_item(Path(i.data(Qt.UserRole))))
    def search(self):
        query=self.input.text().strip().casefold();self.results.clear()
        if not query:return
        count=0;examined=0
        for path in self.d.disk.root.rglob('*'):
            examined+=1
            if query in path.name.casefold():
                i=QListWidgetItem(icon('folder' if path.is_dir() else 'note'),str(path.relative_to(self.d.disk.root)));i.setData(Qt.UserRole,str(path));self.results.addItem(i);count+=1
            if examined>=10000 or count>=300:break
        self.status.setText(f'{count} results · searched up to {examined} items')

class Puzzle(QWidget):
    app_name='Macaque Tiles'
    def __init__(self,d):
        super().__init__();self.moves=0;self.tiles=list(range(1,16))+[0];layout=QVBoxLayout(self);self.status=QLabel();layout.addWidget(self.status);grid=QGridLayout();layout.addLayout(grid);self.buttons=[]
        for i in range(16):
            b=QPushButton();b.setMinimumSize(48,46);b.clicked.connect(lambda _,i=i:self.move(i));grid.addWidget(b,i//4,i%4);self.buttons.append(b)
        new=QPushButton('New Game');new.clicked.connect(self.shuffle);layout.addWidget(new);self.shuffle()
    def adjacent(self,a,b):return abs(a//4-b//4)+abs(a%4-b%4)==1
    def move(self,i):
        empty=self.tiles.index(0)
        if self.adjacent(i,empty):self.tiles[i],self.tiles[empty]=self.tiles[empty],self.tiles[i];self.moves+=1;self.refresh()
    def shuffle(self):
        self.tiles=list(range(1,16))+[0]
        for _ in range(150):
            empty=self.tiles.index(0);choice=random.choice([i for i in range(16) if self.adjacent(i,empty)]);self.tiles[empty],self.tiles[choice]=self.tiles[choice],self.tiles[empty]
        if self.tiles==list(range(1,16))+[0]:self.tiles[14],self.tiles[15]=self.tiles[15],self.tiles[14]
        self.moves=0;self.refresh()
    def refresh(self):
        for i,value in enumerate(self.tiles):self.buttons[i].setText(str(value) if value else '');self.buttons[i].setEnabled(bool(value))
        self.status.setText('Solved!' if self.tiles==list(range(1,16))+[0] else f'{self.moves} moves · slide a tile into the empty square')

class Trash(QWidget):
    app_name='Macaque Files'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Items stay here until you empty the Trash.'));self.list=QListWidget();layout.addWidget(self.list,1);row=QHBoxLayout();restore=QPushButton('Put Away');restore.clicked.connect(self.restore);empty=QPushButton('Empty Trash…');empty.clicked.connect(d.empty_trash);row.addWidget(restore);row.addWidget(empty);layout.addLayout(row);d.disk_changed.connect(self.refresh);self.list.setContextMenuPolicy(Qt.CustomContextMenu);self.list.customContextMenuRequested.connect(self.context);self.refresh()
    def context(self,pos):
        item=self.list.itemAt(pos)
        if item:self.list.setCurrentItem(item)
        menu=QMenu(self);restore=menu.addAction('Put Back',self.restore);restore.setEnabled(item is not None);menu.addAction('Empty Trash…',self.d.empty_trash);menu.exec(self.list.viewport().mapToGlobal(pos))
    def refresh(self):
        self.list.clear()
        for key,info in self.d.disk.trash_items().items():
            i=QListWidgetItem(icon('note'),info['name']+' — '+info['original']);i.setData(Qt.UserRole,key);self.list.addItem(i)
    def restore(self):
        item=self.list.currentItem()
        if item:self.d.operation(lambda:self.d.disk.restore(item.data(Qt.UserRole)))

class Scrapbook(QWidget):
    app_name='Macaque Clips'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);row=QHBoxLayout();paste=QPushButton('Add Clipboard Text');paste.clicked.connect(self.paste);remove=QPushButton('Remove');remove.clicked.connect(self.remove);row.addWidget(paste);row.addWidget(remove);layout.addLayout(row);self.list=QListWidget();self.view=QTextEdit();self.view.setReadOnly(True);layout.addWidget(self.list);layout.addWidget(self.view);self.list.currentRowChanged.connect(self.select);self.refresh()
    def refresh(self):
        self.list.clear()
        for text in self.d.scraps:self.list.addItem(text[:70].replace('\n',' '))
    def select(self,i):self.view.setPlainText(self.d.scraps[i] if 0<=i<len(self.d.scraps) else '')
    def paste(self):
        text=QApplication.clipboard().text()
        if text:self.d.scraps.insert(0,text[:100000]);self.d.scraps=self.d.scraps[:30];self.d.persist();self.refresh();self.list.setCurrentRow(0)
    def remove(self):
        i=self.list.currentRow()
        if i>=0:self.d.scraps.pop(i);self.d.persist();self.refresh()

HELP='''<h2>Welcome to Macaque Classic</h2><p>An independent Macaque desktop, with your native Control Strip and traffic-light windows.</p><h3>Macaque Files</h3><p>Double-click desktop icons. Use Icon or List View, go up a folder, create folders, rename, duplicate, and move documents to Trash. File → Get Info shows where a file is stored. Macaque HD is a managed folder in your Linux user data; it does not replace your physical disk.</p><h3>Windows</h3><p>Drag striped title bars, resize from the lower-right grip. Red closes, yellow minimizes, green maximizes/restores. Double-click a title bar for Window Roll-up. Use the Window menu to restore a minimized window.</p><h3>Documents</h3><p>Macaque Text saves plain text and asks before discarding changes. Macaque Notes save automatically. Closing a sticky leaves it in the Macaque Notes submenu; delete one from Controls → More Options → Desktop Actions → Manage Macaque Notes.</p><h3>Control Strip</h3><p>This is your actual C++ Classic Control Strip 2.0.6. Click a module, then Customize… for themes, module order, and custom icons. Right-click the handle for position. View → Show Control Strip restores a hidden strip. App and settings shortcuts are routed to internal Macaque windows. Audio controls still operate on the host audio service.</p><h3>Classic extras</h3><p>Try Macaque Search, Calculator, the sliding Macaque Tiles, Macaque Clips and Date & Time. Macaque Clips reads clipboard text only when you click Add Clipboard Text. Screen Saver is a visual demo; it does not lock your computer.</p><h3>Shortcuts</h3><p>F6: Search Classic (apps/files on Macaque HD). Ctrl+N: new Macaque Text document. Ctrl+O: open document. Ctrl+S: save. Ctrl+W: close active window. Ctrl+F: find in text or open Macaque Search. F11: fullscreen. Ctrl+Q: quit.</p><h3>Where things live</h3><p>Preferences, notes, managed files and Trash persist in your application data directory. Help → Show Data Folder opens it in Macaque Files.</p><h3>Project status</h3><p>Version 0.12 is a native Linux desktop application. It is not yet a login session, window manager, bootable operating system, or emulator for original Mac applications. Traffic-light controls affect prototype windows. Your standalone strip's settings remain separate.</p>'''
