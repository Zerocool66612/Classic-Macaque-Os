from pathlib import Path
import os,shutil
from PySide6.QtCore import Qt,QTimer,QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *
from visuals import icon,app_kind
from model import APP_NAMES

class AppHub(QWidget):
    app_name='Applications'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Macaque Applications · creative apps: use run-creative.sh; switch with Alt+Tab.'));self.search=QLineEdit();self.search.setPlaceholderText('Find an application…');layout.addWidget(self.search);self.apps=QListWidget();self.apps.setViewMode(QListWidget.IconMode);self.apps.setIconSize(QSize(42,42));self.apps.setGridSize(QSize(155,88));self.apps.setResizeMode(QListWidget.Adjust);layout.addWidget(self.apps,1);self.search.textChanged.connect(self.refresh);self.apps.itemDoubleClicked.connect(lambda item:d.launch(item.text()));self.refresh()
    def refresh(self):
        self.apps.clear()
        for name in APP_NAMES:
            if self.search.text().casefold() in name.casefold():self.apps.addItem(QListWidgetItem(icon(app_kind(name)),name))

class Sound(QWidget):
    app_name='Sound'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Sound output volume'));self.status=QLabel();layout.addWidget(self.status);self.slider=QSlider(Qt.Horizontal);self.slider.setRange(0,100);layout.addWidget(self.slider);self.value=QLabel();layout.addWidget(self.value);refresh=QPushButton('Refresh');refresh.clicked.connect(self.refresh);layout.addWidget(refresh);self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(lambda:d.native_strip.write_volume(self.slider.value()) if d.native_strip else None);self.slider.valueChanged.connect(self.changed);layout.addStretch();self.refresh()
    def refresh(self):
        value=self.d.native_strip.read_volume() if self.d.native_strip and self.d.native_strip.has_audio_backend() else None
        self.slider.blockSignals(True);self.slider.setEnabled(value is not None)
        if value is not None:self.slider.setValue(value);self.value.setText(f'Volume: {value}%');self.status.setText('Audio backend connected')
        else:self.value.setText('No volume available');self.status.setText('No audio service is available.')
        self.slider.blockSignals(False)
    def changed(self,value):self.value.setText(f'Volume: {value}%');self.timer.start(150)

from network_panel import Network

class Storage(QWidget):
    app_name='Storage'
    def __init__(self,d):
        super().__init__();layout=QVBoxLayout(self);layout.addWidget(QLabel('Filesystem information · no partition changes'));self.tree=QTreeWidget();self.tree.setHeaderLabels(['Filesystem','Total','Available']);self.tree.setRootIsDecorated(False);layout.addWidget(self.tree,1)
        from PySide6.QtCore import QStorageInfo
        for disk in QStorageInfo.mountedVolumes():
            if disk.isValid() and disk.isReady():self.tree.addTopLevelItem(QTreeWidgetItem([disk.rootPath(),d.format_bytes(disk.bytesTotal()),d.format_bytes(disk.bytesAvailable())]))
        self.tree.resizeColumnToContents(0);button=QPushButton('Open Macaque HD');button.clicked.connect(lambda:d.open_finder(d.disk.root));layout.addWidget(button)

class Monitor(QWidget):
    app_name='System Monitor'
    def __init__(self,d):
        super().__init__();layout=QVBoxLayout(self);self.output=QTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output);self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(2000);self.refresh()
    def refresh(self):
        text=['System Monitor · host information','']
        try:text+=['Load averages: '+', '.join(f'{v:.2f}' for v in os.getloadavg()),'']
        except OSError:pass
        try:text += [line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))]
        except OSError:text+=['Memory information unavailable.']
        self.output.setPlainText('\n'.join(text))

class Display(QWidget):
    app_name='Display'
    def __init__(self,d):
        super().__init__();layout=QVBoxLayout(self);layout.addWidget(QLabel('Macaque display preferences'));screen=d.screen();layout.addWidget(QLabel(f'Host display: {screen.size().width()} × {screen.size().height()}\nScale: {screen.devicePixelRatio()}'))
        button=QPushButton('Toggle Macaque Fullscreen');button.clicked.connect(d.fullscreen);layout.addWidget(button);layout.addWidget(QLabel('These options affect the Macaque application. Host monitor resolution and brightness are unchanged.'));appearance=QPushButton('Appearance');appearance.clicked.connect(d.appearance);layout.addWidget(appearance);layout.addStretch()

class ImageViewer(QWidget):
    app_name='Image Viewer'
    def __init__(self,d,path):
        super().__init__();self.path=Path(path);layout=QVBoxLayout(self);layout.addWidget(QLabel(self.path.name));self.label=QLabel();self.label.setAlignment(Qt.AlignCenter);self.original=QPixmap(str(path))
        if self.original.isNull():raise ValueError('This image format could not be opened.')
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.label);layout.addWidget(scroll,1);self.label.setPixmap(self.original.scaled(850,600,Qt.KeepAspectRatio,Qt.SmoothTransformation));layout.addWidget(QLabel(f'{self.original.width()} × {self.original.height()} pixels'))

class EmbeddedDialog(QWidget):
    app_name='Control Strip'
    def __init__(self,dialog):
        super().__init__();self.dialog=dialog;self.completed=False;self.layout=QVBoxLayout(self);self.layout.setContentsMargins(0,0,0,0);dialog.setWindowFlags(Qt.Widget);dialog.setModal(False);self.layout.addWidget(dialog);dialog.show()
    def can_close(self):
        if not self.completed:self.dialog.reject()
        return True
    def finish(self):
        self.completed=True;self.dialog.hide() # The C++ stack owns destruction; never transfer ownership to Python.
