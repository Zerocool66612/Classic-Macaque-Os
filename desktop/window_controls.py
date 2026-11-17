"""Classic Platinum window boxes, with optional hello-style traffic lights."""
from PySide6.QtCore import Qt,QRect,Slot,QSignalBlocker
from PySide6.QtGui import QColor,QPainter,QPen
from PySide6.QtWidgets import QAbstractButton,QLabel,QComboBox

from decoration_settings import controls,STYLES,SIDES

def classic_controls(state):return controls(state)['window_buttons']=='Classic'

class ControlChoice(QComboBox):
    def __init__(self,desktop,key,label,choices):
        super().__init__();self.desktop=desktop;self.key=key
        self.setAccessibleName(label);self.setObjectName(key);self.addItems(choices);self.setCurrentText(controls(desktop.state)[key])
        self.currentTextChanged.connect(self.save);desktop.preferences_changed.connect(self.sync)
    @Slot(str)
    def save(self,value):self.desktop.set_preference(self.key,value)
    @Slot(str,object)
    def sync(self,key,value):
        if key==self.key:
            with QSignalBlocker(self):self.setCurrentText(controls({key:value})[key])

def add_control_preferences(layout,desktop):
    for key,label,choices in [('window_buttons','Button style',STYLES),('window_button_side','Button position',SIDES)]:
        layout.addWidget(QLabel(label));layout.addWidget(ControlChoice(desktop,key,label,choices))

class WindowButton(QAbstractButton):
    def __init__(self,desktop,kind,callback,parent):
        super().__init__(parent);self.desktop=desktop;self.kind=kind
        self.setToolTip(kind);self.setAccessibleName(kind);self.setFocusPolicy(Qt.StrongFocus)
        self.clicked.connect(callback);self.apply_theme()
    def apply_theme(self):self.setFixedSize(16,16) if classic_controls(self.desktop.state) else self.setFixedSize(14,14);self.update()
    def paintEvent(self,event):
        p=QPainter(self);r=self.rect().adjusted(1,1,-1,-1)
        if not classic_controls(self.desktop.state):
            p.setRenderHint(QPainter.Antialiasing);color={'Close':'#ed6c5d','Minimize':'#efc24c','Zoom':'#6bbd62'}[self.kind]
            p.setBrush(QColor(color).darker(120) if self.isDown() else QColor(color));p.setPen(QColor('#666666'));p.drawEllipse(r);return
        c=self.desktop.colors();p.fillRect(r,QColor(c['title'] if self.isDown() else c['panel']))
        p.setPen(QColor(c['border']));p.drawRect(r)
        light=QColor(c['edge']);dark=QColor(c['border'])
        if self.isDown():light,dark=dark,light
        p.setPen(light);p.drawLine(2,2,13,2);p.drawLine(2,2,2,13)
        p.setPen(dark);p.drawLine(3,13,13,13);p.drawLine(13,3,13,13)
        p.setPen(QColor(c['text']))
        if self.kind=='Close':p.drawRect(QRect(5,5,5,5))
        elif self.kind=='Minimize':p.drawLine(4,10,11,10);p.drawLine(4,11,11,11)
        else:p.drawRect(QRect(4,4,7,7));p.drawLine(4,6,11,6)
        if self.hasFocus():p.setPen(QPen(QColor(c['text']),1,Qt.DotLine));p.drawRect(self.rect().adjusted(0,0,-1,-1))
