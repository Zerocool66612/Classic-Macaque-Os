import json,os
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,QPlainTextEdit
from system_tasks import Task
class Updates(QWidget):
    app_name='Software Update'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;v=QVBoxLayout(self)
        from desktop import VERSION
        v.addWidget(QLabel('Macaque Classic '+VERSION+' · Software Update'));self.status=QLabel('Desktop updates are installed as packages. Your files and preferences stay in your user folder.');self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status)
        self.releases=QListWidget();v.addWidget(self.releases);row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('Check Desktop Releases',self.check),('Download Selected',self.download),('Install Desktop Package…',self.choose)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        self.packages=QPlainTextEdit();self.packages.setReadOnly(True);self.packages.setPlaceholderText('Debian updates shown here use the current local package index.');v.addWidget(self.packages)
        row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('List Debian Updates',self.list_updates),('Update Debian…',self.system_update)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        note=QLabel('Desktop downloads use HTTPS and a release checksum, not a signed Macaque update feed. Install only desktop packages you trust. Debian updates use APT signature verification and ask before changes.');note.setWordWrap(True);v.addWidget(note)
    def run(self,payload,callback):
        if self.job:return
        self.status.setText('Checking…');self.job=Task(self,Task.helper('update_backend.py'),payload,180000)
        def done(ok,text):
            self.job=None
            if not ok:self.status.setText(text);return
            try:data=json.loads(text)
            except ValueError:self.status.setText('Invalid updater response.');return
            callback(data)
        self.job.done.connect(done)
    def check(self):self.run({'action':'check'},self.checked)
    def checked(self,data):
        self.releases.clear()
        for release in data['releases']:
            item=QListWidgetItem(release['version']+(' · Preview' if release['prerelease'] else '')+' · '+release['tag']);item.setData(Qt.UserRole,release);self.releases.addItem(item)
        if self.releases.count():self.releases.setCurrentRow(0)
        self.status.setText('Choose a release to download. Check the version before installing.' if self.releases.count() else 'No desktop .deb + checksum release assets are published yet. ISO-only releases cannot update the desktop. You can install a local desktop package below.')
    def download(self):
        item=self.releases.currentItem()
        if item:self.run({'action':'download','release':item.data(Qt.UserRole),'folder':str(self.d.disk.root/'Downloads')},self.offer_install)
    def choose(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose a Macaque desktop update',str(self.d.disk.root/'Downloads'),'Debian package (*.deb)')
        if path:self.run({'action':'inspect','path':path},self.offer_install)
    def native_installed(self):
        from maintenance import installed_target
        return os.environ.get('MACAQUE_NATIVE_SESSION')=='1' and installed_target()
    def offer_install(self,data):
        self.status.setText('Package ready: Macaque Classic '+data['version'])
        if not self.native_installed():self.status.setText('Package ready. Install updates from an installed Macaque login session, not live media or the standalone prototype.');return
        if QMessageBox.question(self,'Install desktop update','Install Macaque Classic '+data['version']+' from this package?\n\nAdministrator authentication and APT confirmation follow in Terminal. Save work and log out/in after installation.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.terminal('Desktop Update',['sudo','--','/usr/bin/python3',str(Path(__file__).with_name('maintenance.py')),'install-desktop',data['path'],data['sha256']])
    def terminal(self,title,args):
        from terminal_app import Terminal
        panel=Terminal(self.d,command=args);self.d.window(title,panel,(960,620));panel.view.setFocus()
    def list_updates(self):
        if not self.native_installed():self.status.setText('Use an installed Macaque login session to list system updates.');return
        if self.job:return
        self.job=Task(self,['apt','list','--upgradable'],timeout=30000)
        def done(ok,text):self.job=None;self.packages.setPlainText(text);self.status.setText('Using the local Debian package index. Update Debian refreshes the index first.' if ok else 'Could not list Debian updates.')
        self.job.done.connect(done)
    def system_update(self):
        if not self.native_installed():self.status.setText('Use an installed Macaque login session before applying system updates.');return
        self.terminal('Debian Updates',['sudo','--','/usr/bin/python3',str(Path(__file__).with_name('maintenance.py')),'system-update'])
    def can_close(self):
        if self.job:self.status.setText('Wait for the update request to finish.');return False
        return True
