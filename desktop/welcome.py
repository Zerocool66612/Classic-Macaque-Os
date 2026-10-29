from pathlib import Path
from PySide6.QtCore import Qt,QSize
from PySide6.QtWidgets import *
from visuals import icon,app_kind
class Welcome(QWidget):
    app_name='Welcome Center'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);title=QLabel('Welcome to Macaque Classic');title.setStyleSheet('font-size:24px;font-weight:bold');layout.addWidget(title);layout.addWidget(QLabel('0.24 · Your classic desktop, with room to work.'));grid=QGridLayout();layout.addLayout(grid)
        for i,(label,app) in enumerate([('Browse the web','Macaque Web'),('Open files','Macaque Files'),('Download files','Downloads'),('Organize workspaces','Workspaces'),('Back up Classic','Backup & Recovery'),('Desktop settings','Settings')]):
            b=QToolButton();b.setText(label);b.setIcon(icon(app_kind(app)));b.setIconSize(QSize(32,32));b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon);b.setMinimumHeight(58);b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred);b.clicked.connect(lambda checked=False,name=app:d.launch(name));grid.addWidget(b,i//2,i%2)
        from installer_support import installer_available
        if installer_available():
            install=QPushButton('Install Macaque Classic…');install.setMinimumHeight(44);install.clicked.connect(d.launch_installer);layout.addWidget(install)
        terminal=QPushButton('Open Terminal');terminal.clicked.connect(d.launch_terminal);layout.addWidget(terminal)
        layout.addWidget(QLabel('Recent documents on Macaque HD'));self.recent=QListWidget();layout.addWidget(self.recent,1)
        for path in d.recent:
            p=Path(path)
            if p.exists() and p.resolve().is_relative_to(d.disk.root.resolve()):item=QListWidgetItem(p.name);item.setData(Qt.UserRole,str(p));item.setToolTip(str(p.relative_to(d.disk.root)));self.recent.addItem(item)
        self.recent.itemActivated.connect(lambda item:d.open_item(Path(item.data(Qt.UserRole))));show=QCheckBox('Show Welcome Center at startup');show.setChecked(d.state.get('startup_welcome',False));show.toggled.connect(lambda v:d.set_preference('startup_welcome',v));layout.addWidget(show);note=QLabel('F6 searches Classic · Ctrl+Alt+1…4 changes workspaces · Controls keeps the top bar quiet.');note.setWordWrap(True);layout.addWidget(note)
