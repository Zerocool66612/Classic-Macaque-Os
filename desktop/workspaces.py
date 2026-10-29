"""Four Macaque-internal workspaces. Native session windows remain external."""
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import *

class WorkspaceOverview(QWidget):
    app_name='Workspaces'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Workspaces · organize built-in Macaque windows'));self.columns=QHBoxLayout();layout.addLayout(self.columns,1);self.lists=[];self.chosen=None
        for i in range(4):
            panel=QWidget();box=QVBoxLayout(panel);self.columns.addWidget(panel);button=QPushButton();button.clicked.connect(lambda checked=False,index=i:d.switch_workspace(index));box.addWidget(button);items=QListWidget();items.itemActivated.connect(lambda item:d.activate_window(item.data(Qt.UserRole)));items.itemClicked.connect(lambda item:setattr(self,'chosen',item.data(Qt.UserRole)));box.addWidget(items);row=QHBoxLayout();box.addLayout(row);rename=QPushButton('Rename');rename.clicked.connect(lambda checked=False,index=i:self.rename(index));row.addWidget(rename);move=QPushButton('Move selected here');move.clicked.connect(lambda checked=False,index=i:self.move_selected(index));row.addWidget(move);self.lists.append((button,items))
        layout.addWidget(QLabel('Ctrl+Alt+1…4 switches workspaces while Macaque has focus. External Flatpak/emulator windows are not managed here.'));self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(800);self.refresh()
    def refresh(self):
        names=self.d.workspace_names()
        for i,(button,items) in enumerate(self.lists):
            button.setText(('● ' if i==self.d.workspace else '')+names[i]);selected=items.currentItem().data(Qt.UserRole) if items.currentItem() else None;items.clear()
            for window in self.d.area.subWindowList():
                if window.property('workspace')==i and window.content is not self:
                    item=QListWidgetItem(window.windowTitle()+(' · minimized' if window.isMinimized() else ''));item.setData(Qt.UserRole,window);items.addItem(item)
                    if selected is window:items.setCurrentItem(item)
    def rename(self,index):
        name,ok=QInputDialog.getText(self,'Rename workspace','Name:',text=self.d.workspace_names()[index])
        if ok and name.strip():self.d.state.setdefault('workspace_names',self.d.workspace_names())[index]=name.strip()[:32];self.d.persist();self.refresh()
    def move_selected(self,index):
        from shiboken6 import isValid
        if self.chosen is not None and isValid(self.chosen):self.d.move_to_workspace(self.chosen,index);self.refresh()
    def can_close(self):self.timer.stop();return True

class WorkspaceFeatures:
    def workspace_names(self):
        names=self.state.get('workspace_names',['Desktop','Work','Creative','Games']);return (list(names)+['Desktop','Work','Creative','Games'])[:4]
    def switch_workspace(self,index):
        if index not in range(4):return
        self.workspace=index;self.state['workspace']=index
        for window in self.area.subWindowList():window.setVisible(window.property('workspace')==index)
        self.persist();self.top_bar.refresh_status()
    def activate_window(self,window):
        from shiboken6 import isValid
        if not isValid(window):return
        index=window.property('workspace')
        if index is not None and index!=self.workspace:self.switch_workspace(index)
        window.showNormal();window.raise_();self.area.setActiveSubWindow(window)
    def move_to_workspace(self,window,index):
        if index not in range(4):return
        window.setProperty('workspace',index);window.setVisible(index==self.workspace);self.top_bar.refresh_status()
    def workspace_menu(self,menu):
        menu.clear()
        for i,name in enumerate(self.workspace_names()):
            action=menu.addAction(f'{i+1} · {name}',lambda checked=False,index=i:self.switch_workspace(index));action.setCheckable(True);action.setChecked(i==self.workspace)
        menu.addSeparator();menu.addAction('Workspace Overview…',lambda:self.launch('Workspaces'))
        window=self.area.activeSubWindow()
        if window:
            move=menu.addMenu('Move Active Window')
            for i,name in enumerate(self.workspace_names()):move.addAction(name,lambda checked=False,w=window,index=i:self.move_to_workspace(w,index))
