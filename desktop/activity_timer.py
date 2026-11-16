"""Timers for optional UI work; hidden/minimized windows do not keep ticking."""
from PySide6.QtCore import QTimer,QEvent
from shiboken6 import isValid

class ActivityTimer(QTimer):
    def __init__(self,owner,interval,callback,enabled=lambda:True):
        super().__init__(owner);self.owner=owner;self.enabled=enabled;self.watched=[]
        self.setInterval(interval);self.timeout.connect(callback);self.recheck()
    def recheck(self):
        if not isValid(self) or not isValid(self.owner):return
        widget=self.owner;visible=widget.isVisible()
        while widget is not None:
            if widget not in self.watched:widget.installEventFilter(self);self.watched.append(widget)
            if widget.isMinimized():visible=False
            widget=widget.parentWidget()
        active=visible and self.enabled()
        if active and not self.isActive():self.start()
        elif not active and self.isActive():self.stop()
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.Show,QEvent.Hide,QEvent.WindowStateChange,QEvent.ParentChange):
            QTimer.singleShot(0,self.recheck)
        return False
