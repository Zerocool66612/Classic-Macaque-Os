"""Original monochrome macaque profile for the system menu."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap,QPainter,QColor,QIcon,QPainterPath,QPen

def white_monkey():
    image=QPixmap(64,64);image.fill(Qt.transparent)
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);p.setPen(Qt.NoPen);p.setBrush(QColor('white'))
    # A right-facing profile: rounded crown, short brow, projecting muzzle,
    # compact jaw and broad nape. No grin or front-facing cartoon features.
    head=QPainterPath();head.moveTo(17,55)
    head.cubicTo(19,48,14,44,11,38);head.cubicTo(6,27,10,16,19,11)
    head.cubicTo(27,6,39,7,44,13);head.cubicTo(48,17,48,22,47,26)
    head.lineTo(51,29);head.lineTo(49,32);head.cubicTo(51,34,55,34,56,38)
    head.cubicTo(58,42,55,46,51,47);head.lineTo(44,48)
    head.cubicTo(42,51,40,53,36,53);head.lineTo(35,57);head.lineTo(17,57);head.closeSubpath();p.drawPath(head)
    # Transparent ear, eye and muzzle crease preserve a single-color mark.
    p.setCompositionMode(QPainter.CompositionMode_Clear);p.setBrush(Qt.black)
    p.drawEllipse(17,25,12,15)
    p.setPen(QPen(Qt.black,2.2,Qt.SolidLine,Qt.RoundCap));p.setBrush(Qt.NoBrush)
    ear=QPainterPath();ear.moveTo(22,29);ear.cubicTo(25,28,26,32,23,35);p.drawPath(ear)
    p.setPen(Qt.NoPen);p.setBrush(Qt.black);p.drawEllipse(40,26,4,3)
    p.setPen(QPen(Qt.black,2.2,Qt.SolidLine,Qt.RoundCap));p.drawLine(47,41,55,41);p.end()
    result=QIcon()
    for mode in (QIcon.Normal,QIcon.Active,QIcon.Selected,QIcon.Disabled):result.addPixmap(image,mode)
    return result
