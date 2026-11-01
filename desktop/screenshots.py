"""Classic screenshot app: internal windows or the native Wayland display."""
import json,os,tempfile,time
from pathlib import Path
from shiboken6 import isValid
from PySide6.QtCore import Qt,QTimer,QBuffer,QIODevice
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QComboBox,QSpinBox,QCheckBox,QPushButton,QApplication
from system_tasks import Task

def save_pixmap(pixmap,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    buffer=QBuffer();buffer.open(QIODevice.WriteOnly)
    if pixmap.isNull() or not pixmap.save(buffer,'PNG'):raise ValueError('Could not create the screenshot.')
    fd,name=tempfile.mkstemp(prefix='Screenshot '+time.strftime('%Y-%m-%d %H-%M-%S')+' ',suffix='.png',dir=directory)
    try:
        with os.fdopen(fd,'wb') as f:f.write(bytes(buffer.data()))
    except BaseException:Path(name).unlink(missing_ok=True);raise
    return Path(name)
class Screenshots(QWidget):
    app_name='Screenshot'
    def __init__(self,d,target=None):
        super().__init__();self.d=d;self.target=target;self.job=None;self.busy=False;self.image=None;self.path=None;v=QVBoxLayout(self);form=QFormLayout();v.addLayout(form);self.mode=QComboBox();self.mode.addItems(['Classic desktop','Classic window','Full screen','Select region']);form.addRow('Capture',self.mode);self.delay=QSpinBox();self.delay.setRange(0,10);self.delay.setSuffix(' seconds');form.addRow('Delay',self.delay);self.cursor=QCheckBox('Include pointer (full screen / region)');v.addWidget(self.cursor)
        row=QHBoxLayout();v.addLayout(row);self.button=QPushButton('Take screenshot');self.button.clicked.connect(self.capture);row.addWidget(self.button);self.copy=QPushButton('Copy image');self.copy.setEnabled(False);self.copy.clicked.connect(lambda:QApplication.clipboard().setPixmap(self.image));row.addWidget(self.copy);b=QPushButton('Open Pictures');b.clicked.connect(lambda:d.open_finder(d.disk.root/'Pictures'));row.addWidget(b)
        self.status=QLabel('Saved automatically to Macaque HD / Pictures. Print opens this tool; Shift+Print selects a region; Ctrl+Print captures the full display. Esc cancels region selection.');self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status);self.preview=QLabel('Screenshot preview');self.preview.setMinimumHeight(190);self.preview.setAlignment(Qt.AlignCenter);v.addWidget(self.preview,1)
    def frame(self):return next((w for w in self.d.area.subWindowList() if w.content is self),None)
    def capture(self):
        if self.busy:return
        mode=self.mode.currentText()
        if mode=='Classic window' and (self.target is None or not isValid(self.target)):self.status.setText('Open a Classic window, then reopen Screenshot to capture it.');return
        self.busy=True;self.button.setEnabled(False);frame=self.frame()
        if frame:frame.hide()
        self.status.setText('Waiting to capture…');QTimer.singleShot(self.delay.value()*1000+220,lambda:self.take(mode))
    def take(self,mode):
        directory=self.d.disk.root/'Pictures'
        if mode in ('Full screen','Select region'):
            self.job=Task(self,Task.helper('screenshot_backend.py'),{'directory':str(directory),'region':mode=='Select region','cursor':self.cursor.isChecked()},timeout=160000)
            def done(ok,text):
                self.job=None
                if not ok:self.finished(error=text);return
                try:
                    data=json.loads(text)
                    if data.get('cancelled'):self.finished(error='Selection cancelled.');return
                    self.finished(Path(data['path']))
                except (ValueError,KeyError) as ex:self.finished(error=str(ex))
            self.job.done.connect(done);return
        try:
            source=self.target if mode=='Classic window' else self.d
            if source is None or not isValid(source):raise ValueError('That window has closed.')
            self.finished(save_pixmap(source.grab(),directory))
        except (OSError,ValueError,RuntimeError) as ex:self.finished(error=str(ex))
    def finished(self,path=None,error=None):
        self.busy=False;self.button.setEnabled(True);frame=self.frame()
        if frame:frame.show();self.d.activate_window(frame)
        if error:self.status.setText(error);return
        self.path=path;self.image=QPixmap(str(path))
        if self.image.isNull():self.status.setText('Could not preview the captured file.');return
        self.copy.setEnabled(True);self.preview.setPixmap(self.image.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation));self.status.setText('Saved to Pictures / '+path.name);self.d.disk_changed.emit();self.d.play_sound('save')
    def can_close(self):
        if self.busy:self.status.setText('Finish capture or press Esc to cancel region selection.');return False
        return True
