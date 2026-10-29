"""Software 3D teapot demo: lathed body/lid, swept spout and curved handle.
Original procedural mesh, inspired by the classic graphics demo (not Utah mesh).
"""
import math,time
from PySide6.QtCore import Qt,QTimer,QPointF
from PySide6.QtGui import QColor,QPainter,QPolygonF,QPen
from PySide6.QtWidgets import *

def mesh():
    faces=[];n=24
    def surface(rings):
        for a,b in zip(rings,rings[1:]):
            for j in range(n):faces.append([a[j],a[(j+1)%n],b[(j+1)%n],b[j]])
    profile=[(.20,-.80),(.65,-.80),(.9,-.63),(1.07,-.25),(1.1,.12),(.98,.5),(.72,.70),(.60,.72)]
    surface([[(r*math.cos(j*2*math.pi/n),y,r*math.sin(j*2*math.pi/n)) for j in range(n)] for r,y in profile])
    lid=[(.68,.71),(.73,.76),(.5,.9),(.19,.94),(.15,1.08),(.23,1.15),(.13,1.27),(.01,1.29)]
    surface([[(r*math.cos(j*2*math.pi/n),y,r*math.sin(j*2*math.pi/n)) for j in range(n)] for r,y in lid])
    # Spout extends right; cross-section perpendicular enough for the demo.
    surface([[ (x,y+r*math.cos(j*2*math.pi/n),r*math.sin(j*2*math.pi/n)) for j in range(n)] for x,y,r in [( .8,-.3,.36),(1.2,-.15,.31),(1.5,.18,.23),(1.72,.56,.18),(1.95,.8,.19),(2.08,.85,.24)]])
    rings=[]
    for k in range(19):
        angle=math.pi/2+k*math.pi/18;cx=-.95+.72*math.cos(angle);cy=.0+.7*math.sin(angle)
        rings.append([(cx+.13*math.cos(j*2*math.pi/n)*math.cos(angle),cy+.13*math.cos(j*2*math.pi/n)*math.sin(angle),.13*math.sin(j*2*math.pi/n)) for j in range(n)])
    surface(rings);return faces

class TeapotView(QWidget):
    def __init__(self):
        super().__init__();self.faces=mesh();self.angle=.5;self.tilt=-.25;self.zoom=1.;self.running=True;self.wire=False;self.color=QColor('#b9b6dc');self.last=None;self.setMinimumSize(320,250);self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(33)
    def tick(self):
        if self.running and self.isVisible():self.angle+=.022;self.update()
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:self.last=e.position();self.running=False
    def mouseMoveEvent(self,e):
        if self.last is not None:
            delta=e.position()-self.last;self.angle+=delta.x()*.012;self.tilt=max(-1.2,min(1.2,self.tilt+delta.y()*.012));self.last=e.position();self.update()
    def mouseReleaseEvent(self,e):self.last=None
    def wheelEvent(self,e):self.zoom=max(.4,min(2.3,self.zoom+e.angleDelta().y()/1200));self.update();e.accept()
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor('#17232f'));scale=min(self.width()/5.6,self.height()/3.8)*self.zoom
        p.setPen(Qt.NoPen);p.setBrush(QColor('#101920'));p.drawEllipse(QPointF(self.width()/2,self.height()*.79),scale*1.8,scale*.24)
        def transform(v):
            x,y,z=v;ca,sa=math.cos(self.angle),math.sin(self.angle);x,z=x*ca+z*sa,-x*sa+z*ca;ct,st=math.cos(self.tilt),math.sin(self.tilt);return x,y*ct-z*st,y*st+z*ct
        polygons=[]
        for face in self.faces:
            pts=[transform(v) for v in face];a,b,c=pts[:3];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)];normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);length=math.sqrt(sum(t*t for t in normal)) or 1;light=.28+.72*abs(sum(n*l for n,l in zip(normal,(-.4,.7,-.6)))/length);color=QColor.fromRgbF(min(1,self.color.redF()*light),min(1,self.color.greenF()*light),min(1,self.color.blueF()*light));poly=QPolygonF([QPointF(self.width()/2+x*scale,self.height()*.55-y*scale) for x,y,z in pts]);polygons.append((sum(t[2] for t in pts)/4,poly,color))
        for z,poly,color in sorted(polygons,key=lambda f:f[0],reverse=True):p.setBrush(Qt.NoBrush if self.wire else color);p.setPen(QPen(QColor('#86b6bb'),.6) if self.wire else QPen(color,.5));p.drawPolygon(poly)
        p.setPen(QColor('#cad9e1'));p.drawText(16,25,'TEAPOT STUDIO / SOFTWARE 3D');p.drawText(16,self.height()-15,'Drag to orbit · scroll to zoom · no GPU required')

class Teapot(QWidget):
    app_name='Teapot Studio'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);self.view=TeapotView();layout.addWidget(self.view,1);row=QHBoxLayout();layout.addLayout(row)
        b=QPushButton('Play / Pause');b.clicked.connect(lambda:setattr(self.view,'running',not self.view.running));row.addWidget(b);wire=QCheckBox('Wireframe');wire.toggled.connect(lambda v:(setattr(self.view,'wire',v),self.view.update()));row.addWidget(wire)
        colors=QComboBox();colors.addItems(['Platinum','Copper','Jade','Cobalt']);colors.currentIndexChanged.connect(lambda i:(setattr(self.view,'color',QColor(['#b9b6dc','#e1a072','#73c3ad','#709ad9'][i])),self.view.update()));row.addWidget(colors);b=QPushButton('Save frame…');b.clicked.connect(self.save);row.addWidget(b)
    def save(self):
        path,_=QFileDialog.getSaveFileName(self,'Save Teapot Render',str(self.d.disk.root/'Documents'/'Teapot.png'),'PNG (*.png)')
        if path:
            if not path.lower().endswith('.png'):path+='.png'
            if not self.view.grab().save(path,'PNG'):self.d.error('Could not save the render.')
            else:self.d.disk_changed.emit()
    def can_close(self):self.view.timer.stop();return True
