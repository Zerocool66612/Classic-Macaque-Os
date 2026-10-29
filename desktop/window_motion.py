"""Short snapshot transitions; application widgets keep their original geometry."""
from PySide6.QtCore import Qt,QVariantAnimation,QEasingCurve,QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget,QGraphicsOpacityEffect
from shiboken6 import isValid

EFFECTS=['Soft Zoom','Fade','Slide','None']

def enabled(d,opening):
    return not d.state.get('reduce_motion',False) and d.state.get('open_effect' if opening else 'close_effect','Soft Zoom') in EFFECTS[:-1]

class Transition(QWidget):
    def __init__(self,w,opening):
        super().__init__(w.d.area.viewport());self.d=w.d;self.space=w.property('workspace');self.picture=w.grab();self.target=QRectF(w.geometry());self.opening=opening;self.progress=0.;self.window=w if opening else None
        self.effect=w.d.state.get('open_effect' if opening else 'close_effect','Soft Zoom');self.setAttribute(Qt.WA_TransparentForMouseEvents);self.setAttribute(Qt.WA_NoSystemBackground);self.setGeometry(self.parentWidget().rect())
        self.opacity=None
        if opening:
            self.opacity=QGraphicsOpacityEffect(w);self.opacity.setOpacity(0);w.setGraphicsEffect(self.opacity);w._opening_transition=self
        self.show();self.raise_();self.animation=QVariantAnimation(self);self.animation.setStartValue(0.);self.animation.setEndValue(1.)
        self.animation.setDuration({'Quick':160,'Normal':240,'Relaxed':360}.get(self.d.state.get('animation_speed','Normal'),240));self.animation.setEasingCurve(QEasingCurve.OutCubic if opening else QEasingCurve.InCubic);self.animation.valueChanged.connect(self.advance);self.animation.finished.connect(self.finish);self.animation.start()
    def advance(self,value):self.progress=float(value);self.update()
    def paintEvent(self,event):
        if self.d.workspace!=self.space:return
        t=self.progress if self.opening else 1-self.progress;r=QRectF(self.target)
        if self.effect=='Soft Zoom':
            scale=.86+.14*t;center=r.center();r.setSize(r.size()*scale);r.moveCenter(center)
        elif self.effect=='Slide':r.translate(0,24*(1-t))
        p=QPainter(self);p.setRenderHint(QPainter.SmoothPixmapTransform);p.setOpacity(t);p.drawPixmap(r,self.picture,QRectF(self.picture.rect()))
    def finish(self):
        self.animation.stop()
        if self.window is not None and isValid(self.window):
            self.window.setGraphicsEffect(None);self.window._opening_transition=None
        self.hide();self.deleteLater()

def animate(w,opening):
    previous=getattr(w,'_opening_transition',None)
    if previous is not None and isValid(previous):previous.finish()
    if enabled(w.d,opening) and w.isVisible() and not w.d.quitting:return Transition(w,opening)
