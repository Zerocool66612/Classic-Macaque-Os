"""Monochrome menu mark, independent of full-color application artwork."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap,QPainter,QColor,QIcon
from visuals import icon

def white_monkey():
    image=QPixmap(64,64);image.fill(Qt.transparent);p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);p.setPen(Qt.NoPen);p.setBrush(QColor('white'))
    p.drawEllipse(4,22,15,20);p.drawEllipse(45,22,15,20);p.drawEllipse(13,8,38,48)
    p.setCompositionMode(QPainter.CompositionMode_Clear);p.setBrush(Qt.black);p.drawEllipse(23,26,5,6);p.drawEllipse(36,26,5,6);p.drawEllipse(29,37,6,4)
    from PySide6.QtGui import QPen
    p.setPen(QPen(Qt.black,2));p.drawArc(23,35,18,13,200*16,140*16);p.end()
    result=QIcon()
    for mode in (QIcon.Normal,QIcon.Active,QIcon.Selected,QIcon.Disabled):result.addPixmap(image,mode)
    return result
