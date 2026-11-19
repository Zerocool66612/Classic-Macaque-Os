import json,os
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,QPlainTextEdit,QProgressBar
from system_tasks import Task
from classic_dialogs import question as classic_question, file_name as classic_file_name
class Updates(QWidget):
    app_name='Software Update'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;v=QVBoxLayout(self)
        from desktop import VERSION
        v.addWidget(QLabel('Macaque Classic '+VERSION+' · Software Update'));self.status=QLabel('Desktop updates are installed as packages. Your files and preferences stay in your user folder.');self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status)
        self.releases=QListWidget();v.addWidget(self.releases);row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('Check Desktop Releases',self.check),('Download Selected',self.download),('Install Desktop Package…',self.choose)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        self.notes=QPlainTextEdit();self.notes.setReadOnly(True);self.notes.setPlaceholderText('Release notes appear here when you select a release.');self.notes.setMaximumHeight(130);v.addWidget(self.notes)
        self.releases.currentItemChanged.connect(self.selection_changed)
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.hide();v.addWidget(self.progress)
        row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('Update History',self.history),('Roll Back Saved Desktop…',self.rollback),('Recovery & Diagnostics',lambda:d.launch('Recovery & Diagnostics'))]:
            b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        self.saved=[];self.rollback_list=QListWidget();self.rollback_list.setMaximumHeight(100);self.rollback_list.hide();v.addWidget(self.rollback_list)
        self.packages=QPlainTextEdit();self.packages.setReadOnly(True);self.packages.setPlaceholderText('Debian updates shown here use the current local package index.');v.addWidget(self.packages)
        row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('List Debian Updates',self.list_updates),('Update Debian…',self.system_update)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        note=QLabel('Desktop downloads use HTTPS and a release checksum, not a signed Macaque update feed. Install only desktop packages you trust. Debian updates use APT signature verification and ask before changes.');note.setWordWrap(True);v.addWidget(note)
    def run(self,payload,callback):
        if self.job:return
        self.status.setText('Working…');self.progress.show();self.job=Task(self,Task.helper('update_backend.py'),payload,180000)
        def done(ok,text):
            self.job=None;self.progress.hide()
            if not ok:self.status.setText('Update failed: '+text+'  Please retry or open Recovery & Diagnostics.');return
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
    def selection_changed(self,item,*_):
        release=item.data(Qt.UserRole) if item else {}
        self.notes.setPlainText(release.get('notes','No release notes supplied.'))
    def history(self):self.run({'action':'history'},self.history_loaded)
    def history_loaded(self,data):
        self.saved=data.get('packages',[]);self.rollback_list.clear();self.rollback_list.show()
        for item in self.saved:
            if item.get('rollback'):
                row=QListWidgetItem('Macaque Classic '+item['version']);row.setData(Qt.UserRole,item);self.rollback_list.addItem(row)
        if self.rollback_list.count():self.rollback_list.setCurrentRow(0)
        lines=['Installed desktop package: '+(data.get('installed_version') or 'not installed')]
        for item in reversed(data.get('history',[])):
            lines.append(item['time']+' · '+item['action']+' · '+item['version']+' · '+item['result'])
        self.packages.setPlainText('\n'.join(lines))
        self.status.setText('Choose a saved older desktop version to roll back.' if self.rollback_list.count() else 'No older desktop package is saved yet. Successful updates retain packages for future rollback; this does not undo Debian updates or user files.')
    def rollback(self):
        if not self.native_installed():self.status.setText('Rollback requires an installed Macaque login session.');return
        item=self.rollback_list.currentItem()
        if not item:self.history();return
        data=item.data(Qt.UserRole)
        if classic_question(self.d,'Roll back desktop','Install saved Macaque Classic '+data['version']+'?\n\nSave your work first. This changes only the desktop package, not Debian updates, drivers or personal files. Administrator authentication and APT confirmation follow.',QMessageBox.No)==QMessageBox.Yes:
            self.terminal('Desktop Rollback',['sudo','--','/usr/bin/python3',str(Path(__file__).with_name('maintenance.py')),'rollback-desktop',data['path'],data['sha256']])
    def download(self):
        item=self.releases.currentItem()
        if not item:
            self.status.setText('Select a desktop release first. Click Check Desktop Releases to refresh the list.')
            return
        release=item.data(Qt.UserRole)
        if not release or not release.get('url'):
            self.status.setText('The selected release has no downloadable desktop package.')
            return
        self.status.setText('Downloading Macaque Classic '+release['version']+'…')
        self.run({'action':'download','release':release,'folder':str(self.d.disk.root/'Downloads')},self.offer_install)
    def choose(self):
        path,_=classic_file_name(self.d,'Choose a Macaque desktop update',str(self.d.disk.root/'Downloads'),'Debian package (*.deb)')
        if path:self.run({'action':'inspect','path':path},self.offer_install)
    def native_installed(self):
        from maintenance import installed_target
        return os.environ.get('MACAQUE_NATIVE_SESSION')=='1' and installed_target()
    def offer_install(self,data):
        from desktop import VERSION
        from update_store import older
        from update_store import installed_version
        installed=installed_version() or VERSION
        if data['version']==installed:self.status.setText('Macaque Classic '+installed+' is already installed.');return
        if older(data['version'],installed):self.status.setText('This is an older desktop version. Use Update History to select a saved rollback package.');return
        self.status.setText('Package ready: Macaque Classic '+data['version'])
        if not self.native_installed():self.status.setText('Package downloaded, but installation is only available from an installed Macaque login session.');return
        if classic_question(self.d,'Install desktop update','Install Macaque Classic '+data['version']+' from this package?\n\nAdministrator authentication and APT confirmation follow in Terminal. Save work and log out/in after installation.',QMessageBox.No)==QMessageBox.Yes:self.terminal('Desktop Update',['sudo','--','/usr/bin/python3',str(Path(__file__).with_name('maintenance.py')),'install-desktop',data['path'],data['sha256']])
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
