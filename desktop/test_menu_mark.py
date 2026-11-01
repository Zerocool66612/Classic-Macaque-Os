"""Check the actual system-menu button's idle and hover rendering."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from unittest.mock import Mock
from PySide6.QtCore import QPoint,Qt,QEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from chrome import TopBar
from window_motion_icon import white_monkey
app=QApplication([])
image=white_monkey().pixmap(64,64).toImage()
pixels=[image.pixelColor(x,y) for x in range(64) for y in range(64) if image.pixelColor(x,y).alpha()]
assert pixels and all(c.red()==c.green()==c.blue()==255 for c in pixels)
for mode in ('light','dark'):
 d=Mock(state={'mode':mode,'compact_bar':True});bar=TopBar(d);bar.resize(900,32);bar.show();QTest.qWait(30);button=bar.buttons[0]
 def green_count():
  image=button.grab().toImage();return sum(1 for x in range(image.width()) for y in range(image.height()) if (lambda c:c.green()>c.red()+20 and c.green()>c.blue())(image.pixelColor(x,y)))
 button.setAttribute(Qt.WA_UnderMouse,False);app.sendEvent(button,QEvent(QEvent.Leave));button.update();QTest.qWait(30);assert green_count()==0,mode+' idle background is green'
 button.setAttribute(Qt.WA_UnderMouse,True);app.sendEvent(button,QEvent(QEvent.Enter));button.update();QTest.qWait(30);assert green_count()>20,mode+' hover highlight missing'
 button.setAttribute(Qt.WA_UnderMouse,False);app.sendEvent(button,QEvent(QEvent.Leave));button.update();QTest.qWait(30);assert green_count()==0,mode+' hover highlight remains after leaving'
 bar.battery_timer.stop();bar.hide();bar.deleteLater();app.processEvents()
print('White profile icon and actual light/dark button idle -> hover -> idle rendering passed.')
