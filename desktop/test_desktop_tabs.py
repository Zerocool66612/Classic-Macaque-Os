import os,tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtCore import Qt,QPoint,QEvent
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtTest import QTest
from unittest.mock import patch
from desktop import Desktop
app=QApplication([])
with tempfile.TemporaryDirectory() as t:
 d=Desktop(Path(t));d.state['reduce_motion']=True;d.show();QTest.qWait(80);tabs=d.desktop_tabs
 w=d.launch('Macaque Text');editor=w.content.editor;editor.setPlainText('Keep my unsaved work');original=w.geometry();tabs.attach(w);assert not w.isVisible() and tabs.bar.isVisible() and tabs.bar.count()==1
 QTest.mouseClick(tabs.bar,Qt.LeftButton,pos=tabs.bar.tabRect(0).center());assert w.isVisible() and editor.toPlainText()=='Keep my unsaved work';assert w.geometry().bottom()<=tabs.bar.y()
 QTest.mouseClick(tabs.bar,Qt.LeftButton,pos=tabs.bar.tabRect(0).center());assert not w.isVisible()
 d.activate_window(w);assert w.isVisible();w.rename('My Draft');assert tabs.bar.tabText(0)=='My Draft'
 other=d.launch('Calculator');tabs.attach(other);tabs.open(other);assert not w.isVisible() and other.isVisible();tabs.open(w);assert not other.isVisible()
 d.resize(900,650);QTest.qWait(60);tabs.layout();assert w.geometry().bottom()<=tabs.bar.y() and tabs.bar.geometry().right()<d.area.viewport().width()
 d.switch_workspace(1);assert not w.isVisible() and not tabs.bar.isVisible();d.switch_workspace(0);assert w.isVisible() and tabs.bar.isVisible()
 d.move_to_workspace(w,2);assert not w.isVisible();d.activate_window(w);assert d.workspace==2 and w.isVisible()
 tabs.detach(w);assert not w.property('desktop_tabbed') and w.geometry()==original and editor.toPlainText()=='Keep my unsaved work'
 tabs.attach(w)
 with patch.object(w.content,'can_close',return_value=False):w.close();assert w in tabs.records
 with patch.object(w.content,'can_close',return_value=True):w.close();QTest.qWait(20);assert w not in tabs.records
 d.switch_workspace(0);tabs.detach(other);assert tabs.bar.count()==0 and not tabs.bar.isVisible()
 # Drag a live title bar to the lower edge; dragging back out detaches.
 test=d.launch('Calculator');test.move(50,50);press=test.bar.rect().center();target=d.area.viewport().mapToGlobal(QPoint(300,d.area.viewport().height()-5));end=test.bar.mapFromGlobal(target)
 QTest.mousePress(test.bar,Qt.LeftButton,pos=press);QTest.mouseMove(test.bar,end,20);QTest.mouseRelease(test.bar,Qt.LeftButton,pos=end);assert test in tabs.records
 tabs.open(test);QTest.mousePress(test.bar,Qt.LeftButton,pos=test.bar.rect().center());QTest.mouseMove(test.bar,QPoint(100,-80),20);QTest.mouseRelease(test.bar,Qt.LeftButton,pos=QPoint(100,-80));assert test not in tabs.records
 for _ in range(3):tabs.attach(d.launch('Calculator'))
 d.quitting=True;d.close();assert tabs.bar.count()==0 and not tabs.timer.isActive()
print('Desktop drawer tabs: click open/collapse, preserved edits, rename, detach geometry, close cancellation, workspace move/activation, resize, drag-to-edge and drag-off passed.')
