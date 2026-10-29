"""Original procedural wallpapers, rendered locally at desktop resolution."""
import math,random
from pathlib import Path
from PySide6.QtCore import Qt,QPointF,QRectF,QSize
from PySide6.QtGui import QPainter,QImage,QColor,QLinearGradient,QPainterPath,QPen,QPixmap,QIcon
from PySide6.QtWidgets import *
NAMES=['Lagoon','Afterglow','Lunar Peaks','Midnight Orbit','Platinum Weave','Macaque Grove']
def render(name,width=1920,height=1080):
    image=QImage(width,height,QImage.Format_RGB32);p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);p.scale(width/1920,height/1080);rng=random.Random(22)
    palettes={'Lagoon':('#0a344a','#308c92'),'Afterglow':('#332d63','#d98789'),'Lunar Peaks':('#151e3c','#4e6c96'),'Midnight Orbit':('#08101e','#263856'),'Platinum Weave':('#697588','#b4bdca'),'Macaque Grove':('#143934','#65917a')};top,bottom=palettes.get(name,palettes['Lagoon']);g=QLinearGradient(0,0,1920,1080);g.setColorAt(0,QColor(top));g.setColorAt(1,QColor(bottom));p.fillRect(QRectF(0,0,1920,1080),g);p.setPen(Qt.NoPen)
    if name in ('Lagoon','Afterglow','Macaque Grove'):
        for i in range(9):
            y=480+i*93;path=QPainterPath(QPointF(-100,y));path.cubicTo(550,y-360,1000,y+200,2020,y-230);path.lineTo(2020,1200);path.lineTo(-100,1200);path.closeSubpath();p.setBrush(QColor(120+i*8,210-i*7,190 if name!='Afterglow' else 150,20+i*3));p.drawPath(path)
        if name=='Macaque Grove':
            for i in range(18):
                x=i*130+rng.randrange(-60,60);p.setPen(QPen(QColor('#133c35'),12));p.drawLine(x,1100,x+100,350+rng.randrange(300));p.setPen(Qt.NoPen);p.setBrush(QColor(10,45,38,90));p.drawEllipse(QPointF(x+70,450),130,230)
    elif name=='Lunar Peaks':
        p.setBrush(QColor('#eee4ce'));p.drawEllipse(QPointF(1390,245),115,115)
        for layer in range(4):
            path=QPainterPath(QPointF(-100,1100));path.lineTo(-100,700+layer*60)
            for x in range(0,2200,160):path.lineTo(x,440+layer*120+rng.randrange(-150,130))
            path.lineTo(2100,1100);path.closeSubpath();p.setBrush(QColor(35-layer*5,54-layer*7,81-layer*9));p.drawPath(path)
    elif name=='Midnight Orbit':
        for i in range(210):
            p.setBrush(QColor(220,233,255,rng.randrange(50,200)));r=rng.choice([1,1,2]);p.drawEllipse(QPointF(rng.randrange(1920),rng.randrange(1080)),r,r)
        p.setBrush(QColor('#425879'));p.drawEllipse(QPointF(1270,550),240,240);p.setBrush(Qt.NoBrush)
        for offset in range(0,35,4):p.setPen(QPen(QColor(160,183,209,80),2));p.drawEllipse(QRectF(820-offset,430-offset/3,900+offset*2,240+offset*2/3))
    else:
        for y in range(0,1080,12):
            for x in range(0,1920,12):p.fillRect(x,y,6,6,QColor(255,255,255,17));p.fillRect(x+6,y+6,6,6,QColor(0,0,0,12))
    p.end();return image

class Wallpapers(QWidget):
    app_name='Wallpapers'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Original Macaque wallpapers · double-click to apply'));self.list=QListWidget();self.list.setViewMode(QListWidget.IconMode);self.list.setIconSize(QSize(192,108));self.list.setGridSize(QSize(215,150));self.list.setResizeMode(QListWidget.Adjust);layout.addWidget(self.list)
        for name in NAMES:self.list.addItem(QListWidgetItem(QIcon(QPixmap.fromImage(render(name,384,216))),name))
        self.list.itemDoubleClicked.connect(lambda item:self.apply(item.text()));row=QHBoxLayout();layout.addLayout(row);b=QPushButton('Apply selected');b.clicked.connect(lambda:self.apply(self.list.currentItem().text()) if self.list.currentItem() else None);row.addWidget(b);b=QPushButton('Export selected PNG…');b.clicked.connect(self.export);row.addWidget(b)
    def apply(self,name):self.d.change_appearance('wallpaper',name)
    def export(self):
        item=self.list.currentItem()
        if not item:return
        path,_=QFileDialog.getSaveFileName(self,'Export Wallpaper',str(self.d.disk.root/'Documents'/(item.text()+'.png')),'PNG (*.png)')
        if path:
            if not path.lower().endswith('.png'):path+='.png'
            if not render(item.text()).save(path,'PNG'):self.d.error('Could not save wallpaper.')
            else:self.d.disk_changed.emit()
