"""Render original Macaque installer artwork from existing code-native assets."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(root/'desktop'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter,QImage,QColor,QFont,QPen
from PySide6.QtCore import Qt,QRect
from visuals import icon
from wallpapers import render
app=QApplication([]);dest=root/'iso/branding';dest.mkdir(exist_ok=True)
logo=icon('macaque',256).pixmap(256,256);logo.save(str(dest/'macaque-logo.png'))
def card(name,title,subtitle,kind,body):
 image=render('Lagoon').scaled(1200,720,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation);p=QPainter(image);p.fillRect(image.rect(),QColor(10,30,39,110));p.setRenderHint(QPainter.Antialiasing)
 p.drawPixmap(50,45,100,100,logo);p.setPen(QColor('#ffffff'));p.setFont(QFont('DejaVu Sans',32,QFont.Bold));p.drawText(QRect(170,55,950,55),Qt.AlignLeft|Qt.AlignVCenter,'Macaque Classic')
 p.setFont(QFont('DejaVu Sans',15));p.setPen(QColor('#bfe4df'));p.drawText(QRect(174,110,900,35),Qt.AlignLeft,subtitle)
 p.setPen(QPen(QColor('#73918f'),2));p.setBrush(QColor('#24343b'));p.drawRoundedRect(64,195,1070,450,9,9);p.fillRect(65,196,1068,43,QColor('#344a50'))
 for x,c in [(88,'#ed6c5d'),(114,'#efc24c'),(140,'#6bbd62')]:p.setPen(Qt.NoPen);p.setBrush(QColor(c));p.drawEllipse(x,210,14,14)
 p.drawPixmap(100,292,110,110,icon(kind,110).pixmap(110,110));p.setPen(QColor('#ffffff'));p.setFont(QFont('DejaVu Sans',25,QFont.Bold));p.drawText(QRect(250,280,820,70),Qt.AlignLeft|Qt.AlignVCenter,title)
 p.setFont(QFont('DejaVu Sans',17));p.setPen(QColor('#d6e5e4'));p.drawText(QRect(252,365,800,195),Qt.AlignLeft|Qt.TextWordWrap,body)
 p.setFont(QFont('DejaVu Sans',12));p.setPen(QColor('#a3c8c2'));p.drawText(85,680,'Macaque Classic 0.26 · Installer Preview');p.end();image.save(str(dest/name))
card('welcome.png','A classic desktop, ready to explore.','Welcome to your Macaque installation','macaque','Choose your language, keyboard, disk and account. Review the summary before applying changes. Built on Debian Linux, with an original Macaque desktop.')
card('slide-desktop.png','Make yourself at home.','Familiar details. Room to work.','folder','Traffic-light windows, a quiet menu bar and your Classic Control Strip. Arrange your files, switch workspaces, choose a wallpaper and make the desktop yours.')
card('slide-terminal.png','A shell with a familiar frame.','Terminal is part of the desktop.','terminal','Open Terminal from the Control Strip or desktop. Real Linux commands run inside a Macaque window, with the same controls as your other built-in apps.')
card('slide-linux.png','Classic character. Linux underneath.','Your installation is being prepared.','disk','The standard installation includes cached BIOS and UEFI bootloader packages. After restarting, sign in with the account you selected. Keep the USB connected until shutdown or restart completes.')
print('Rendered original installer logo, welcome art and three slides')
