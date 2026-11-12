"""Bottom-edge drawer tabs for live built-in windows; documents stay in memory."""
from PySide6.QtCore import Qt,QObject,QEvent,QRect,QTimer
from PySide6.QtWidgets import QTabBar,QMenu
from shiboken6 import isValid

class DesktopTabs(QObject):
    def __init__(self,d):
        super().__init__(d);self.d=d;self.records={};self.bar=QTabBar(d.area.viewport());self.bar.setObjectName('desktopDrawerTabs');self.bar.setExpanding(False);self.bar.setMovable(True);self.bar.setUsesScrollButtons(True);self.bar.setElideMode(Qt.ElideRight);self.bar.setDrawBase(False);self.bar.setShape(QTabBar.RoundedNorth);self.bar.hide();self.bar.tabBarClicked.connect(self.toggle_index);self.bar.tabMoved.connect(lambda *_:self.layout());self.bar.setContextMenuPolicy(Qt.CustomContextMenu);self.bar.customContextMenuRequested.connect(self.context);d.area.viewport().installEventFilter(self)
        self.timer=QTimer(self);self.timer.setInterval(250);self.timer.timeout.connect(self.layout);self.timer.start()
    def eventFilter(self,obj,event):
        if event.type() in (QEvent.Resize,QEvent.Show):QTimer.singleShot(0,self.layout)
        return False
    def index(self,w):return next((i for i in range(self.bar.count()) if self.bar.tabData(i) is w),-1)
    def attach(self,w,geometry=None):
        if not isValid(w) or w in self.records:return
        if w.isMaximized() or w.isMinimized():w.showNormal()
        if w.shaded:w.shade()
        self.records[w]={'geometry':QRect(geometry or w.geometry()),'drawer_size':w.size(),'open':False};w.setProperty('desktop_tabbed',True)
        i=self.bar.addTab(w.windowTitle());self.bar.setTabData(i,w);self.bar.setTabToolTip(i,w.windowTitle()+' · click to open/collapse · right-click for options')
        w.windowTitleChanged.connect(lambda *_:self.titles());w.destroyed.connect(lambda *_ ,key=w:self.remove_deleted(key));w.hide();self.layout()
    def titles(self):
        for w in self.records:
            if isValid(w):
                i=self.index(w)
                if i>=0:self.bar.setTabText(i,w.windowTitle());self.bar.setTabToolTip(i,w.windowTitle()+' · click to open/collapse · right-click for options')
    def remove_deleted(self,w):
        self.records.pop(w,None)
        if not isValid(self.bar):return
        i=self.index(w)
        if i>=0:self.bar.removeTab(i)
        self.layout()
    def toggle_index(self,index):
        w=self.bar.tabData(index)
        if w not in self.records:return
        if self.records[w]['open']:self.collapse(w)
        else:self.open(w)
    def collapse(self,w):
        if w not in self.records:return
        self.records[w]['open']=False;w.hide();self.layout()
    def open(self,w):
        if w not in self.records or not isValid(w):return
        space=w.property('workspace')
        if space!=self.d.workspace:self.d.switch_workspace(space)
        for other,record in self.records.items():
            if other is not w and isValid(other) and other.property('workspace')==space:record['open']=False;other.hide()
        self.records[w]['open']=True;self.bar.setCurrentIndex(self.index(w));w.showNormal();self.layout();w.raise_();self.bar.raise_();self.d.area.setActiveSubWindow(w);w.content.setFocus()
    def detach(self,w,keep_geometry=False):
        record=self.records.pop(w,None)
        if not record:return
        i=self.index(w)
        if i>=0:self.bar.removeTab(i)
        if isValid(w):
            w.setProperty('desktop_tabbed',False)
            if not keep_geometry:w.setGeometry(record['geometry'])
            if w.property('workspace')==self.d.workspace:w.showNormal();w.raise_();self.d.area.setActiveSubWindow(w)
        self.layout()
    def layout(self):
        if not isValid(self.d.area) or not isValid(self.bar):return
        viewport=self.d.area.viewport();visible=[]
        for w,record in list(self.records.items()):
            if not isValid(w):continue
            if w.isMinimized():record['open']=False
            active=w.property('workspace')==self.d.workspace;i=self.index(w)
            if i>=0:self.bar.setTabVisible(i,active)
            if active:visible.append(w)
            w.setVisible(active and record['open'])
        if not visible:self.bar.hide();return
        c=self.d.colors();self.bar.setStyleSheet('QTabBar::tab {background:'+c['title']+';color:'+c['text']+';border:1px solid '+c['stripe']+';border-top-left-radius:5px;border-top-right-radius:5px;padding:4px 12px;min-width:65px;max-width:180px;} QTabBar::tab:selected {font-weight:bold;}')
        height=max(26,self.d.state.get('text_size',13)+12);left=4;y=viewport.height()-height
        strip=getattr(self.d,'strip',None)
        if strip and isValid(strip) and strip.isVisible() and strip.geometry().bottom()>=y-5:
            if viewport.width()-strip.geometry().right()>250:left=max(4,strip.geometry().right()+8)
            else:y=max(0,strip.geometry().top()-height-3)
        self.bar.setGeometry(left,max(0,y),max(50,viewport.width()-left-4),height);self.bar.show()
        for w in visible:
            record=self.records[w]
            if not record['open']:continue
            if 'last_size' in record and w.size()!=record['last_size']:record['drawer_size']=w.size()
            size=record['drawer_size'];width=max(280,min(size.width(),viewport.width()));height_w=max(200,min(size.height(),max(200,y)))
            i=self.index(w);tab=self.bar.tabRect(i);x=max(0,min(left+tab.left(),viewport.width()-width));w.setGeometry(x,max(0,y-height_w),width,height_w);record['last_size']=w.size()
        self.bar.raise_()
    def shutdown(self):
        self.timer.stop();self.bar.blockSignals(True)
        while self.bar.count():self.bar.removeTab(0)
        self.records.clear();self.bar.hide()
    def context(self,pos):
        index=self.bar.tabAt(pos)
        if index<0:return
        w=self.bar.tabData(index);menu=QMenu(self.bar)
        menu.addAction('Collapse' if self.records[w]['open'] else 'Open',lambda:self.toggle_index(self.index(w)))
        menu.addAction('Detach as Normal Window',lambda:self.detach(w));menu.addSeparator();menu.addAction('Close Window',w.close);menu.exec(self.bar.mapToGlobal(pos))
