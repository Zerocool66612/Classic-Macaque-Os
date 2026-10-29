from PySide6.QtCore import Qt,QRect,QPoint
from PySide6.QtGui import QPainter,QPixmap,QIcon,QColor,QPen,QPolygon

STYLE='''
QWidget { font-family:"DejaVu Sans"; font-size:13px; color:#202020; }
QPushButton { background:#d5d4d0; border-top:2px solid #fff; border-left:2px solid #fff; border-right:2px solid #555; border-bottom:2px solid #555; padding:5px 10px; }
QPushButton:pressed { background:#b5b4b0; border:2px inset #777; }
QPushButton:disabled { color:#888; }
QLineEdit,QTextEdit,QPlainTextEdit,QListWidget,QTreeWidget { background:#fffefb; color:#171717; border:1px solid #777; selection-background-color:#333399; selection-color:white; }
QMenu { background:#deddd9; color:#171717; border:1px solid #444; padding:3px; }
QMenu::item { padding:5px 25px 5px 13px; } QMenu::item:selected { background:#333399; color:white; }
QMenu::item:disabled { color:#888; } QMenu::separator { height:1px; background:#999; margin:3px; }
QTabWidget::pane { border:1px solid #777; background:#d5d4d0; } QTabBar::tab { background:#c5c4c0; border:1px solid #888; padding:6px 12px; } QTabBar::tab:selected { background:#e0dfda; }
QToolTip { background:#ffffce; color:#111; border:1px solid #444; }
QScrollBar { background:#c9c8c3; } QCalendarWidget QWidget { color:#171717; } QStatusBar { background:#d5d4d0; }
'''

def icon(kind='folder',size=56):
    pm=QPixmap(size,size);pm.fill(Qt.transparent);p=QPainter(pm);p.scale(size/56,size/56);p.setPen(QPen(QColor('#30354a'),1))
    if kind in ('folder','apps','system','documents'):
        p.setBrush(QColor('#aebfef'));p.drawRect(5,13,23,10);p.setBrush(QColor('#8ba6df'));p.drawRect(4,21,48,27);p.setPen(QColor('#e2eaff'));p.drawLine(6,23,50,23)
        p.setPen(QColor('#34476d'))
        if kind=='apps':
            p.setPen(QPen(QColor('#9f5039'),3));p.drawLine(18,42,29,25);p.drawLine(29,25,41,42);p.drawLine(20,36,38,36)
        elif kind=='system':
            p.drawLine(20,41,20,28);p.drawLine(20,28,28,36);p.drawLine(28,36,36,28);p.drawLine(36,28,36,41)
        elif kind=='documents':
            p.setBrush(QColor('#fffbe8'));p.drawRect(23,26,15,18);p.drawLine(26,31,35,31);p.drawLine(26,35,35,35)
    elif kind=='disk':
        p.setBrush(QColor('#c5c4be'));p.drawRect(6,17,44,27);p.setBrush(QColor('#eeeae0'));p.drawRect(8,12,40,25);p.drawLine(10,33,45,33);p.setPen(QColor('#333'));p.drawLine(11,40,35,40);p.setPen(QColor('#47a85a'));p.drawLine(41,40,45,40)
    elif kind=='trash':
        p.setBrush(QColor('#c3c4c6'));p.drawRect(17,16,25,31);p.setBrush(QColor('#e6e5e0'));p.drawEllipse(14,9,31,8)
        for x in range(21,40,5):p.drawLine(x,20,x,43)
    elif kind=='sticky':
        p.setBrush(QColor('#f8e883'));p.drawRect(8,8,40,38);p.drawLine(14,18,41,18);p.drawLine(14,25,38,25);p.drawLine(14,32,33,32)
    elif kind=='calculator':
        p.setBrush(QColor('#bbbbc3'));p.drawRect(13,5,32,46);p.setBrush(QColor('#d4e7c4'));p.drawRect(17,10,24,9)
        for y in (25,33,41):
            for x in (18,27,36):p.setBrush(QColor('#ecebe4'));p.drawRect(x,y,5,5)
    elif kind=='search':
        p.setBrush(QColor('#b1dce5'));p.drawEllipse(9,6,27,27);p.setPen(QPen(QColor('#53463a'),7));p.drawLine(33,32,46,47)
    elif kind=='puzzle':
        for i in range(9):p.setBrush(QColor(['#648cae','#dfbb6b','#bb6f64'][i%3]));p.drawRect(7+i%3*14,7+i//3*14,13,13)
    elif kind=='appearance':
        p.setBrush(QColor('#f0dfb2'));p.drawEllipse(5,9,45,35)
        for x,y,c in [(15,17,'#d44'),(30,15,'#45b'),(37,26,'#4a5'),(20,32,'#774')]:p.setBrush(QColor(c));p.drawEllipse(x,y,7,7)
    elif kind=='chess':
        p.setBrush(QColor('#e9e1c8'));p.drawRect(6,6,44,44)
        for y in range(4):
            for x in range(4):
                if (x+y)%2:p.fillRect(7+x*11,7+y*11,10,10,QColor('#548179'))
        p.setBrush(QColor('#f8f1dc'));p.drawRect(19,35,22,8);p.drawEllipse(24,16,12,12);p.drawRect(26,27,8,9);p.drawLine(30,8,30,16);p.drawLine(26,12,34,12)
    elif kind=='teapot':
        p.setBrush(QColor('#b8b5dc'));p.drawEllipse(11,18,32,25);p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor('#9f9bc3'),4));p.drawEllipse(4,20,12,16);p.setBrush(QColor('#b8b5dc'));p.drawPolygon(QPolygon([QPoint(38,25),QPoint(50,16),QPoint(45,34),QPoint(38,37)]));p.drawEllipse(17,15,22,7);p.drawEllipse(26,10,6,6)
    elif kind=='media':
        p.setBrush(QColor('#465d79'));p.drawRect(7,7,42,42);p.setBrush(QColor('#dce8dd'));p.drawPolygon(QPolygon([QPoint(22,17),QPoint(22,40),QPoint(40,28)]))
    elif kind=='tasks':
        p.setBrush(QColor('#f2ebd6'));p.drawRect(10,5,37,46);p.setPen(QPen(QColor('#367b6c'),2))
        for y in (16,28,40):p.drawRect(15,y-4,7,7);p.drawLine(27,y,41,y)
    elif kind=='mouse':
        p.setBrush(QColor('#d4d5d8'));p.drawRoundedRect(15,7,28,43,13,13);p.drawLine(16,26,42,26);p.drawLine(29,7,29,25);p.setBrush(QColor('#507f79'));p.drawRoundedRect(27,12,4,10,2,2)
    elif kind in ('bell','quiet'):
        p.setBrush(QColor('#dfc582'));p.drawEllipse(17,9,23,27);p.drawRect(17,24,23,15);p.drawRect(12,38,33,5);p.drawEllipse(24,44,10,6)
        if kind=='quiet':p.setPen(QPen(QColor('#ba5659'),4));p.drawLine(9,10,47,47)
    elif kind=='capture':
        p.setBrush(QColor('#b8c8c6'));p.drawRect(5,15,46,32);p.drawRect(12,10,14,5);p.setBrush(QColor('#4e747d'));p.drawEllipse(20,21,22,22);p.setBrush(QColor('#cde8e3'));p.drawEllipse(25,26,12,12)
    elif kind=='gear':
        p.translate(28,28);p.setPen(QPen(QColor('#a9bab9'),8))
        for i in range(8):p.drawLine(0,-15,0,-22);p.rotate(45)
        p.setPen(QPen(QColor('#334750'),1));p.setBrush(QColor('#a9bab9'));p.drawEllipse(-17,-17,34,34);p.setBrush(QColor('#3d5e68'));p.drawEllipse(-7,-7,14,14)
    elif kind=='power':
        p.setBrush(Qt.NoBrush);p.setPen(QPen(QColor('#7cae98'),6));p.drawArc(9,9,38,38,130*16,280*16);p.drawLine(28,5,28,28)
    elif kind=='clock':
        p.setBrush(QColor('#faf9ee'));p.drawEllipse(6,6,44,44);p.setPen(QPen(QColor('#333'),2));p.drawLine(28,28,28,13);p.drawLine(28,28,40,33)
    elif kind=='network':
        p.setBrush(QColor('#76b5c4'));p.drawEllipse(6,6,44,44);p.setBrush(QColor('#6eaa7c'));p.drawPolygon(QPolygon([QPoint(13,13),QPoint(27,11),QPoint(32,22),QPoint(22,31),QPoint(14,25)]));p.drawPolygon(QPolygon([QPoint(31,32),QPoint(42,29),QPoint(39,43),QPoint(32,46)]))
    elif kind=='sound':
        p.setBrush(QColor('#a8beb4'));p.drawRect(7,22,13,14);p.drawPolygon(QPolygon([QPoint(20,22),QPoint(33,12),QPoint(33,46),QPoint(20,36)]));p.setBrush(Qt.NoBrush);p.drawArc(29,12,21,33,-70*16,140*16)
    elif kind in ('display','monitor'):
        p.setBrush(QColor('#aebeb6'));p.drawRect(5,7,46,34);p.setBrush(QColor('#426b79'));p.drawRect(9,11,38,25);p.drawLine(26,42,26,48);p.drawLine(17,49,38,49)
        if kind=='monitor':
            p.setPen(QPen(QColor('#8be6b3'),2));p.drawPolyline(QPolygon([QPoint(11,29),QPoint(18,29),QPoint(23,17),QPoint(28,32),QPoint(33,23),QPoint(44,23)]))
    elif kind=='terminal':
        p.setBrush(QColor('#172127'));p.drawRect(5,9,46,36);p.setPen(QPen(QColor('#ffffff'),3));p.drawLine(13,18,21,25);p.drawLine(21,25,13,32);p.drawLine(28,33,41,33)
    elif kind in ('computer','macaque'):
        p.setPen(QPen(QColor('#123e38'),1));p.setBrush(QColor('#308f80'));p.drawEllipse(4,16,15,18);p.drawEllipse(37,16,15,18);p.drawEllipse(11,5,34,44)
        p.setBrush(QColor('#c9dfc4'));p.drawEllipse(15,19,26,25);p.setBrush(QColor('#203b34'));p.drawEllipse(19,21,4,5);p.drawEllipse(33,21,4,5);p.setBrush(QColor('#91b6a5'));p.drawEllipse(22,30,12,8);p.drawLine(25,35,31,35)
    else:
        p.setBrush(QColor('#fffbdf'));p.drawPolygon(QPolygon([QPoint(13,5),QPoint(35,5),QPoint(45,15),QPoint(45,50),QPoint(13,50)]));p.drawLine(35,5,35,15);p.drawLine(35,15,45,15)
        for y in range(23,44,6):p.drawLine(19,y,38,y)
    p.end();return QIcon(pm)

def app_kind(name):return {'Terminal':'terminal','Welcome Center':'macaque','Macaque Web':'network','Workspaces':'display','Downloads':'network','Classic Mac Apps':'computer','Flatpak Apps':'apps','Backup & Recovery':'disk','Classic Sounds':'sound','Settings':'system','Notifications':'tasks','Chess':'chess','Teapot Studio':'teapot','Macaque Paint':'appearance','Tasks':'tasks','Clockwork':'clock','Media Player':'media','Character Map':'note','Archive Viewer':'documents','Wallpapers':'display','Mouse':'mouse','GIMP':'appearance','Audacity':'sound','OBS Studio':'media','Macaque Files':'folder','Network':'network','Sound':'sound','Display':'display','Storage':'disk','System Monitor':'monitor','Macaque Text':'note','Macaque Notes':'sticky','Calculator':'calculator','Macaque Search':'search','Macaque Tiles':'puzzle','Macaque Clips':'documents','Appearance':'appearance','Date & Time':'clock','Help Center':'computer'}.get(name,'apps')
