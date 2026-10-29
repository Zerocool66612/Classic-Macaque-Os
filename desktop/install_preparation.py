"""Visible disk/swap inventory before opening the installation wizard."""
import json
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import *
HELPER='/usr/local/libexec/macaque-swap-helper.py'
class InstallPreparation(QWidget):
    app_name='Install Preparation'
    def __init__(self,d):
        super().__init__();self.d=d;self.data=None;self.busy=False;layout=QVBoxLayout(self)
        label=QLabel('Select the intended installation disk to inspect or release its active swap. This does not erase or format the disk. Calamares asks you to choose the installation disk again.');label.setWordWrap(True);layout.addWidget(label)
        self.disks=QComboBox();layout.addWidget(self.disks);self.details=QPlainTextEdit();self.details.setReadOnly(True);layout.addWidget(self.details,1)
        row=QHBoxLayout();layout.addLayout(row);self.refresh_button=QPushButton('Refresh Disks');self.refresh_button.clicked.connect(self.refresh);row.addWidget(self.refresh_button);self.release_button=QPushButton('Release Selected Disk’s Swap');self.release_button.clicked.connect(self.release_swap);row.addWidget(self.release_button)
        launch=QPushButton('Continue to Installer…');launch.clicked.connect(self.continue_install);layout.addWidget(launch);self.launch_button=launch
        terminal=QPushButton('Open Terminal');terminal.clicked.connect(d.launch_terminal);layout.addWidget(terminal);self.process=QProcess(self);self.process.finished.connect(self.finished);self.process.errorOccurred.connect(self.failed);self.buffer='';self.kind='';self.refresh()
    def run(self,kind,program,args):
        self.kind=kind;self.buffer='';self.busy=True
        for w in [self.refresh_button,self.release_button,self.launch_button,self.disks]:w.setEnabled(False)
        self.process.setProcessChannelMode(QProcess.MergedChannels);self.process.readyReadStandardOutput.connect(self.read) if not getattr(self,'connected',False) else None;self.connected=True;self.process.start(program,args)
    def read(self):self.buffer+=bytes(self.process.readAllStandardOutput()).decode(errors='replace')
    def failed(self,error):
        if self.process.state()==QProcess.NotRunning:self.complete();self.details.setPlainText(self.process.errorString())
    def complete(self):
        self.busy=False
        for w in [self.refresh_button,self.release_button,self.launch_button,self.disks]:w.setEnabled(True)
    def refresh(self):self.run('list','/usr/bin/python3',[HELPER])
    def finished(self,code,status):
        self.read();self.complete()
        if code:self.details.setPlainText(self.buffer or 'Operation failed. No automatic retry was attempted.');return
        if self.kind=='list':
            try:self.data=json.loads(self.buffer)
            except ValueError:self.details.setPlainText('Could not read disk inventory.');return
            self.disks.clear()
            for disk in self.data['disks']:
                if disk.get('type')=='disk':self.disks.addItem(f"{disk['name']} · {disk.get('model','')} · {int(disk['size'])/2**30:.1f} GiB",disk)
            self.details.setPlainText('Live boot source: '+self.data['live_source']+'\n\nActive swap:\n'+json.dumps(self.data['swaps'],indent=2)+'\n\nIf no swap is active, releasing swap cannot fix a partition-creation error. The new installer defaults to no swap partition.')
        else:self.details.setPlainText(self.buffer+'\n\nUse Refresh Disks to verify before opening the installer.')
    def release_swap(self):
        disk=self.disks.currentData()
        if not disk:return
        if QMessageBox.question(self,'Release Active Swap',f"Release active swap partitions on {disk['name']} ({disk.get('model','')})?\n\nOther disks are excluded. Swap files and encrypted mappings are not changed. If RAM is insufficient, the operation may fail.",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        self.run('release','/usr/bin/sudo',['-n','--','/usr/bin/python3',HELPER,'--release','--disk',disk['name'],'--expected-id',disk['maj:min']])
    def continue_install(self):
        if not self.busy:self.d.launch_installer_wizard()
    def can_close(self):return not self.busy
