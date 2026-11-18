"""Headless check: animated beachball appears only during wait operations."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from mouse_tools import BeachballAnimator,mouse_cursor
app=QApplication([])
assert mouse_cursor('Mac OS X Beachball (Busy)').shape()==Qt.ArrowCursor
anim=BeachballAnimator(app)
anim.timer.stop()
anim.tick();assert not anim.active
app.setOverrideCursor(Qt.WaitCursor)
anim.tick();assert anim.active
first=app.overrideCursor().pixmap().cacheKey()
anim.tick();assert app.overrideCursor().pixmap().cacheKey()!=first
app.restoreOverrideCursor()
anim.tick();assert not anim.active
app.setOverrideCursor(Qt.PointingHandCursor)
anim.tick();assert not anim.active and app.overrideCursor().shape()==Qt.PointingHandCursor
app.restoreOverrideCursor()
print('PASS: normal arrow, animated wait beachball, restored cursor')
