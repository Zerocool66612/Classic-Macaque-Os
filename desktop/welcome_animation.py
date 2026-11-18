"""Original Qt-rendered first-run welcome, no Apple footage or sampled audio."""
import math
from PySide6.QtCore import Qt,QTimer,QElapsedTimer,QRectF
from PySide6.QtGui import QPainter,QColor,QFont,QLinearGradient
from PySide6.QtWidgets import QDialog
from visuals import icon
DURATION=15.0

class WelcomeAnimation(QDialog):
    def __init__(self,d,replay=False):
        super().__init__(d);self.d=d;self.replay=replay;self.setWindowTitle('Welcome to Macaque Classic');self.setWindowFlags(Qt.Dialog|Qt.FramelessWindowHint);self.setModal(True);self.resize(1280,720);self.t=0.;self.completed=False;self.logo=icon('macaque');self.clock=QElapsedTimer()
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.tick);self.finished.connect(self.cleanup)
    def showEvent(self,e):
        super().showEvent(e);self.clock.start();self.timer.start();QTimer.singleShot(400,self.chime)
    def chime(self):
        if self.isVisible():
            self.d.sound_theme.suspended=False;self.d.play_sound('welcome')
    def tick(self):
        self.t=self.clock.elapsed()/1000;self.update()
        if self.t>=DURATION:self.completed=True;super().accept()
    def cleanup(self,*_):self.timer.stop();self.d.sound_theme.stop()
    def accept(self):
        if self.completed:super().accept()
    def reject(self):
        if self.completed:super().reject()
    def done(self,result):
        if self.completed:super().done(result)
    def closeEvent(self,e):
        if self.completed or getattr(self.d,'quitting',False):e.accept()
        else:e.ignore()
    def keyPressEvent(self,e):e.accept()
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);self.paint_frame(p,self.width(),self.height(),11.0 if self.d.state.get('reduce_motion',False) else self.t);p.end()
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
