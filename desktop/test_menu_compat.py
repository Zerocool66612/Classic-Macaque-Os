import os,gc
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication,QEvent
from shiboken6 import isValid
from menu_compat import Menu
app=QApplication([]);root=Menu();hits=[]
for i in range(30):
 child=root.addMenu('Apps');child.addAction('Launch',lambda:hits.append(1));del child
 gc.collect();child=next(a.menu() for a in root.actions() if a.text()=='Apps');assert isValid(child);child.actions()[0].trigger()
 nested=child.addMenu('More');nested.addAction('Nested');del nested;gc.collect();nested=next(a.menu() for a in child.actions() if a.text()=='More');assert isValid(nested)
 root.clear();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);assert not isValid(child) and not isValid(nested)
assert len(hits)==30
external=Menu('External');root.addMenu(external);root.clear();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);assert isValid(external)
print('Submenu ownership and rebuild cleanup passed')
