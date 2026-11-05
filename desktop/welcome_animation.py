"""Original Qt-rendered first-run welcome, no Apple footage or sampled audio."""
import math
from PySide6.QtCore import Qt,QTimer,QElapsedTimer,QRectF
from PySide6.QtGui import QPainter,QColor,QFont,QLinearGradient
from PySide6.QtWidgets import QDialog,QPushButton
from window_motion_icon import rainbow_monkey
DURATION=15.0

class WelcomeAnimation(QDialog):
    def __init__(self,d,replay=False):
        super().__init__(d);self.d=d;self.replay=replay;self.setWindowTitle('Welcome to Macaque Classic');self.setWindowFlags(Qt.Dialog|Qt.FramelessWindowHint);self.setModal(True);self.resize(1280,720);self.t=0.;self.muted=False;self.logo=rainbow_monkey();self.clock=QElapsedTimer()
        self.skip=QPushButton('Skip',self);self.skip.setAccessibleName('Skip welcome animation');self.skip.clicked.connect(self.accept)
        self.mute=QPushButton('Mute',self);self.mute.setCheckable(True);self.mute.setAccessibleName('Mute welcome chime');self.mute.toggled.connect(self.set_muted)
        for b in (self.skip,self.mute):b.setStyleSheet('QPushButton {color:white;background:#ffffff18;border:1px solid #ffffff60;border-radius:5px;padding:7px 18px;} QPushButton:hover {background:#ffffff30;}')
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.tick);self.finished.connect(self.cleanup)
    def resizeEvent(self,e):
        super().resizeEvent(e);self.skip.setGeometry(self.width()-112,self.height()-58,88,34);self.mute.setGeometry(24,self.height()-58,100,34)
    def showEvent(self,e):
        super().showEvent(e);self.clock.start();self.timer.start();QTimer.singleShot(400,self.chime)
    def chime(self):
        if self.isVisible() and not self.muted:
            self.d.sound_theme.suspended=False;self.d.play_sound('startup')
    def set_muted(self,value):
        self.muted=value;self.mute.setText('Muted' if value else 'Mute')
        if value:self.d.sound_theme.stop()
    def tick(self):
        self.t=self.clock.elapsed()/1000;self.update()
        if self.t>=DURATION:self.accept()
    def cleanup(self,*_):self.timer.stop();self.d.sound_theme.stop()
    def keyPressEvent(self,e):
        if e.key()==Qt.Key_Escape:self.accept()
        else:super().keyPressEvent(e)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);self.paint_frame(p,self.width(),self.height(),self.t);p.end()
    def paint_frame(self,p,w,h,t):
        gradient=QLinearGradient(0,0,w,h);gradient.setColorAt(0,QColor('#092d42'));gradient.setColorAt(1,QColor('#41979d'));p.fillRect(0,0,w,h,gradient)
        p.setPen(Qt.NoPen)
        for i in range(5):
            p.setBrush(QColor(170,235,235,12+i*3));offset=math.sin(t*.15+i)*w*.04;p.drawEllipse(QRectF(-w*.3+offset,h*.38+i*h*.12,w*1.7,h*.85))
        if t<7.2:
            words=['Hello','Bonjour','Hola','Hello'];index=min(3,int(t/1.8));phase=(t%1.8)/1.8;opacity=min(1,phase*4,(1-phase)*4)
            p.setOpacity(max(0,opacity));font=QFont('DejaVu Serif',max(28,int(h*.11)));font.setItalic(True);p.setFont(font);p.setPen(QColor('white'));p.drawText(QRectF(20,h*.31,w-40,h*.25),Qt.AlignCenter,words[index])
        else:
            opacity=min(1,(t-7.2)/1.1);p.setOpacity(opacity);size=int(h*.19);self.logo.paint(p,int((w-size)/2),int(h*.20),size,size)
            p.setPen(QColor('white'));p.setFont(QFont('DejaVu Sans',max(18,int(h*.043)),QFont.Bold));p.drawText(QRectF(20,h*.45,w-40,h*.11),Qt.AlignCenter,'Welcome to Macaque Classic')
            p.setFont(QFont('DejaVu Sans',max(12,int(h*.025))));p.drawText(QRectF(20,h*.58,w-40,h*.07),Qt.AlignCenter,'Made by Drew')
            p.setOpacity(opacity*min(1,max(0,(t-10)/1.2)));p.drawText(QRectF(20,h*.69,w-40,h*.07),Qt.AlignCenter,'A familiar beginning. A new adventure.')
        p.setOpacity(1)
