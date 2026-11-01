"""Laptop panel plus bounded media-key requests and a Classic desktop indicator."""
import json
from collections import deque
from PySide6.QtCore import QObject,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QSlider,QPushButton,QLabel,QHBoxLayout
from system_tasks import Task
from laptop_support import battery_summary
class HardwareKeys(QObject):
    def __init__(self,d):
        super().__init__(d);self.d=d;self.job=None;self.pending=deque();self.label=QLabel(d);self.label.setTextFormat(Qt.PlainText);self.label.setAlignment(Qt.AlignCenter);self.label.setAttribute(Qt.WA_TransparentForMouseEvents);self.label.setStyleSheet('padding:14px;background:#263238;color:white;border:1px solid #c5d3d4;border-radius:5px;font-size:17px;');self.label.hide();self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.label.hide)
    def run(self,action):
        if len(self.pending)<16:self.pending.append(action)
        self.next()
    def next(self):
        if self.job or not self.pending:return
        op=self.pending.popleft();self.job=Task(self,Task.helper('laptop_keys_backend.py'),{'action':op},timeout=20000)
        def done(ok,text):
            self.job=None
            if ok:
                try:
                    v=json.loads(text);message=v['kind']+(': muted' if v['muted'] else ': '+str(v['percent'])+'%')
                except (ValueError,KeyError):message='Could not read laptop control status.'
            else:message=text
            self.label.setText(message[:180]);self.label.setMaximumWidth(max(280,self.d.width()-60));self.label.adjustSize();self.label.move((self.d.width()-self.label.width())//2,max(20,self.d.height()-self.label.height()-65));self.label.show();self.label.raise_();self.timer.start(1800);QTimer.singleShot(0,self.next)
        self.job.done.connect(done)
class LaptopControls(QWidget):
    app_name='Laptop Controls'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;v=QVBoxLayout(self);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status);self.battery=QLabel();v.addWidget(self.battery);form=QFormLayout();v.addLayout(form)
        self.volume=QSlider(Qt.Horizontal);self.volume.setRange(0,100);self.volume.setEnabled(False);self.volume.sliderReleased.connect(lambda:self.run({'action':'volume','percent':self.volume.value()}));form.addRow('Output volume',self.volume)
        self.brightness=QSlider(Qt.Horizontal);self.brightness.setRange(5,100);self.brightness.setEnabled(False);self.brightness.sliderReleased.connect(lambda:self.run({'action':'brightness','percent':self.brightness.value()}));form.addRow('Screen brightness',self.brightness)
        row=QHBoxLayout();v.addLayout(row)
        for text,op in [('Mute / unmute','mute'),('Microphone mute','mic-mute')]:b=QPushButton(text);b.clicked.connect(lambda checked=False,a=op:self.run({'action':a}));row.addWidget(b)
        b=QPushButton('Battery, lid and idle settings…');b.clicked.connect(lambda:d.launch('Battery & Power'));v.addWidget(b)
        b=QPushButton('Refresh');b.clicked.connect(self.refresh);v.addWidget(b)
        note=QLabel('The brightness and speaker symbols on your laptop’s F-key row work across the Wayland session. Some keyboards require Fn or Fn Lock. Ordinary F1–F12 shortcuts remain available to apps. Brightness requires a backlight device; VM brightness is usually unavailable.');note.setWordWrap(True);v.addWidget(note);v.addStretch();self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(5000);self.refresh()
    def refresh(self):self.run({'action':'status'})
    def run(self,payload):
        if self.job:return
        self.job=Task(self,Task.helper('laptop_keys_backend.py'),payload)
        def done(ok,text):
            self.job=None
            if not ok:self.status.setText(text);return
            try:data=json.loads(text)
            except ValueError:self.status.setText('Could not read laptop controls.');return
            if payload['action']!='status':self.refresh();return
            sound=data['audio'];lights=data['backlights'];self.volume.setEnabled(bool(sound));self.brightness.setEnabled(bool(lights))
            if sound:self.volume.setValue(sound['percent'])
            if lights:self.brightness.setValue(lights[0]['percent'])
            self.battery.setText(battery_summary(data['batteries'])[1]);self.status.setText(('Output muted. ' if sound and sound['muted'] else '')+('Audio ready. ' if sound else data['audio_error']+' ')+('Backlight ready.' if lights else 'No laptop backlight detected.'))
        self.job.done.connect(done)
    def can_close(self):
        if self.job:self.status.setText('Wait for the current laptop request.');return False
        self.timer.stop();return True
