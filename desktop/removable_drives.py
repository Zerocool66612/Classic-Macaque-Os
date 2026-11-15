"""Classic removable-drive controls and user-session desktop discovery."""
import json
from PySide6.QtCore import QObject,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTreeWidget,QTreeWidgetItem,QLabel,QPushButton,QMessageBox,QFileDialog
from system_tasks import Task
class RemovableMonitor(QObject):
    def __init__(self,d):
        super().__init__(d);self.d=d;self.disks=[];self.job=None;self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(10000);QTimer.singleShot(1500,self.refresh)
    def refresh(self):
        if self.job:return
        self.job=Task(self,Task.helper('removable_backend.py'),{'action':'list'})
        def finish(ok,text):
            self.job=None
            if not ok:return
            try:disks=json.loads(text)['disks']
            except (ValueError,KeyError):return
            if disks!=self.disks:
                previous={v['device']:v['name'] for disk in self.disks for v in disk['volumes']}
                current={v['device'] for disk in disks for v in disk['volumes']}
                for device,name in previous.items():
                    if device not in current:self.d.notify('Drive removed',name+' is no longer connected.',sound=False)
                self.disks=disks;self.d.refresh_desktop()
                for w in self.d.area.subWindowList():
                    if isinstance(w.content,RemovableDrives):w.content.populate(disks)
        self.job.done.connect(finish)
class RemovableDrives(QWidget):
    app_name='USB Drives'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;v=QVBoxLayout(self);self.status=QLabel('USB sticks and removable non-system disks');self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status)
        self.tree=QTreeWidget();self.tree.setHeaderLabels(['Volume','Drive','Size','Mounted at']);self.tree.setRootIsDecorated(False);v.addWidget(self.tree)
        for buttons in [[('Refresh',self.refresh),('Mount',lambda:self.act('mount')),('Open',self.open),('Unmount',lambda:self.act('unmount')),('Safely Eject',self.eject)],[('Import File to Macaque HD…',lambda:self.copy('import')),('Export File to USB…',lambda:self.copy('export'))]]:
            row=QHBoxLayout();v.addLayout(row)
            for title,fn in buttons:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        note=QLabel('Open browses the volume read only. Import/export copies individual files without overwriting existing ones. Close files before ejecting; busy drives stay attached.');note.setWordWrap(True);v.addWidget(note);self.refresh()
    def run(self,payload):
        if self.job:return
        self.status.setText('Working…');self.job=Task(self,Task.helper('removable_backend.py'),payload,3600000 if payload.get('action') in ('import','export') else 180000)
        def done(ok,text):
            self.job=None
            if not ok:self.pending_eject=None;self.status.setText(text);return
            try:data=json.loads(text)
            except ValueError:self.status.setText('Could not read drive information.');return
            self.populate(data['disks']);self.status.setText(data.get('message','Select a volume.'));self.d.removable.refresh()
            if payload['action']=='import':self.d.disk_changed.emit()
            pending=getattr(self,'pending_eject',None);self.pending_eject=None
            if pending:self.eject_volume(pending)
        self.job.done.connect(done)
    def refresh(self):self.run({'action':'list'})
    def populate(self,disks):
        self.tree.clear()
        for disk in disks:
            for volume in disk['volumes']:
                item=QTreeWidgetItem([volume['name'],disk['model'],self.d.format_bytes(volume['size']),' · '.join(volume['mounts']) or 'Not mounted']);item.setData(0,Qt.UserRole,volume);self.tree.addTopLevelItem(item)
        self.tree.resizeColumnToContents(0)
    def selected(self):
        item=self.tree.currentItem()
        if not item:self.status.setText('Select a removable volume first.');return None
        return item.data(0,Qt.UserRole)
    def act(self,action):
        volume=self.selected()
        if volume:self.run({**volume,'action':action})
    def open(self):
        volume=self.selected()
        if volume and volume['mounts']:self.d.open_finder(volume['mounts'][0])
        elif volume:self.status.setText('Mount this volume first, then click Open.')
    def eject_volume(self,volume):
        if self.job:self.pending_eject=volume;self.status.setText('Refreshing before safe eject…');return
        for i in range(self.tree.topLevelItemCount()):
            item=self.tree.topLevelItem(i);current=item.data(0,Qt.UserRole)
            if all(current.get(k)==volume.get(k) for k in ('device','identity','uuid')):
                self.tree.setCurrentItem(item);self.eject();return
        self.status.setText('This volume changed or was removed. Refresh the drive list.')
    def eject(self):
        volume=self.selected()
        if volume and QMessageBox.question(self,'Safely Eject','Unmount all volumes on this USB drive and power it off?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.run({**volume,'action':'eject'})
    def copy(self,action):
        volume=self.selected()
        if not volume:return
        if not volume['mounts']:self.status.setText('Mount the volume first.');return
        folder=volume['mounts'][0] if action=='import' else str(self.d.disk.root)
        source,_=QFileDialog.getOpenFileName(self,'Select a file to '+action,folder)
        if source:self.run({**volume,'action':action,'source':source,'local_root':str(self.d.disk.root)})
    def can_close(self):
        if self.job:self.status.setText('Wait for the drive operation to finish before closing.');return False
        return True
