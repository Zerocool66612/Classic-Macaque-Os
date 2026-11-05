"""Portable volume backups; recovery writes to a fresh folder, never overwrites."""
import json,os,stat,time,zipfile,shutil,tempfile
from pathlib import Path,PurePosixPath
from PySide6.QtCore import QThread,Signal
from PySide6.QtWidgets import *
LIMIT=250*1024*1024
COUNT=10000

def create_backup(root,state,destination,exclude_hidden=False):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('A file already exists there. Choose a new backup filename.')
    if destination.is_relative_to(root):raise ValueError('Save the backup outside Macaque HD so it cannot include itself.')
    entries=[];total=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[n for n in dirs if not (Path(parent)/n).is_symlink() and (not exclude_hidden or not n.startswith('.'))]
        for name in files:
            p=Path(parent)/name
            if p.is_symlink() or (exclude_hidden and name.startswith('.')):continue
            if not p.resolve().is_relative_to(root):raise ValueError('A file moved outside the volume during backup.')
            size=p.stat().st_size;total+=size;entries.append(p)
            if total>LIMIT or len(entries)>COUNT:raise ValueError('This backup tool supports up to 250 MB and 10,000 files.')
    fd,temp=tempfile.mkstemp(prefix='.macaque-backup-',dir=destination.parent);os.close(fd)
    try:
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('backup-info.json',json.dumps({'format':'macaque-classic-backup','version':1,'time':time.time()}));z.writestr('desktop-state.json',json.dumps(state,indent=2))
            # Store directories too, including empty user folders and app aliases.
            for parent,dirs,files in os.walk(root,followlinks=False):
                dirs[:]=[n for n in dirs if not (Path(parent)/n).is_symlink() and (not exclude_hidden or not n.startswith('.'))]
                for name in dirs:
                    p=Path(parent)/name;z.writestr('Macaque HD/'+p.relative_to(root).as_posix()+'/',b'')
            for p in entries:z.write(p,'Macaque HD/'+p.relative_to(root).as_posix())
        with zipfile.ZipFile(temp) as check:
            if len(check.infolist())>COUNT+2000 or sum(e.file_size for e in check.infolist())>LIMIT:raise ValueError('Backup exceeds the supported size/entry limit.')
        # Exclusive creation preserves old backups on Linux and removable drives.
        fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,'wb') as output,open(temp,'rb') as source:shutil.copyfileobj(source,output)
        except Exception:destination.unlink(missing_ok=True);raise
    finally:Path(temp).unlink(missing_ok=True)
    return str(destination)

def recover_backup(archive,parent):
    parent=Path(parent).resolve();parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist();total=0;seen=set()
        if len(entries)>COUNT+2000:raise ValueError('Too many backup entries.')
        for entry in entries:
            name=entry.filename;parts=PurePosixPath(name).parts
            if name.startswith('/') or '\\' in name or any(p in ('.','..') for p in parts) or ':' in name:raise ValueError('Unsafe backup path.')
            if not (name in ('backup-info.json','desktop-state.json') or parts and parts[0]=='Macaque HD'):raise ValueError('Unexpected backup entry.')
            if name in seen or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Duplicate or symbolic-link backup entry.')
            seen.add(name);total+=entry.file_size
            if total>LIMIT:raise ValueError('Backup expands beyond the 250 MB recovery limit.')
        if z.getinfo('backup-info.json').file_size>65536:raise ValueError('Backup metadata is too large.')
        info=json.loads(z.read('backup-info.json'))
        if info.get('format')!='macaque-classic-backup' or info.get('version')!=1:raise ValueError('This is not a supported Macaque backup.')
        destination=Path(tempfile.mkdtemp(prefix='Recovered-',dir=parent))
        try:
            for entry in entries:
                target=destination/entry.filename
                if not target.resolve().is_relative_to(destination):raise ValueError('Unsafe recovery destination.')
                if entry.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(entry) as source,target.open('xb') as output:
                    written=0
                    while True:
                        block=source.read(1024*1024)
                        if not block:break
                        written+=len(block)
                        if written>entry.file_size or written>LIMIT:raise ValueError('Invalid expanded file size.')
                        output.write(block)
        except Exception:shutil.rmtree(destination);raise
    return str(destination)

class BackupWorker(QThread):
    done=Signal(str);failed=Signal(str)
    def __init__(self,fn,args,parent):super().__init__(parent);self.fn=fn;self.args=args
    def run(self):
        try:self.done.emit(self.fn(*self.args))
        except Exception as ex:self.failed.emit(str(ex))
class Backups(QWidget):
    app_name='Backup & Recovery'
    def __init__(self,d):
        super().__init__();self.d=d;self.worker=None;layout=QVBoxLayout(self);heading=QLabel('Backup & Recovery');heading.setStyleSheet('font-size:21px;font-weight:bold');layout.addWidget(heading);text=QLabel('Back up Macaque HD and a snapshot of your notes, tasks and preferences. Recovery puts files in a new Recovered Backups folder; it never replaces your current desktop.');text.setWordWrap(True);layout.addWidget(text)
        self.save=QPushButton('Create backup ZIP…');self.save.clicked.connect(self.backup);layout.addWidget(self.save);self.restore=QPushButton('Recover from a backup…');self.restore.clicked.connect(self.recover);layout.addWidget(self.restore);personal=QPushButton('Back up a personal folder…');personal.clicked.connect(self.personal);layout.addWidget(personal);prefs=QPushButton('Restore appearance and accessibility…');prefs.clicked.connect(self.restore_preferences);layout.addWidget(prefs);self.status=QLabel('Save documents and drawings first. Limit: 250 MB / 10,000 files. Symlinks and Trash are excluded. Preferences are recovered as JSON, not applied automatically.');self.status.setWordWrap(True);layout.addWidget(self.status);layout.addStretch()
    def personal(self):
        import os
        if os.environ.get('MACAQUE_NATIVE_SESSION')!='1' or os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':self.status.setText('Personal-folder backup is available in the native Macaque session.');return
        folder=QFileDialog.getExistingDirectory(self,'Choose personal folder',str(Path.home()/'Documents'))
        if not folder:return
        root=Path(folder).resolve();home=Path.home().resolve()
        if not root.is_relative_to(home) or root==home or any(p.startswith('.') for p in root.relative_to(home).parts):self.status.setText('Choose a visible personal subfolder inside your home folder.');return
        path,_=QFileDialog.getSaveFileName(self,'Save personal-folder backup',str(home/'Downloads'/('Personal-'+time.strftime('%Y%m%d-%H%M%S')+'.zip')),'ZIP (*.zip)')
        if path:self.start(create_backup,(root,{},path if path.endswith('.zip') else path+'.zip',True))
    def restore_preferences(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose recovered desktop-state.json',str(self.d.disk.root/'Recovered Backups'),'JSON (*.json)')
        if not path:return
        try:values=validated_preferences(Path(path))
        except (OSError,ValueError) as e:self.status.setText(str(e));return
        if QMessageBox.question(self,'Restore preferences','Apply recovered appearance, accessibility and clock settings? Current settings will be saved first. Files and app startup commands are not changed.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        backup=self.d.base/('preferences-before-restore-'+time.strftime('%Y%m%d-%H%M%S')+'.json')
        try:
            fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as f:json.dump(self.d.state,f,indent=2)
            self.d.state.update(values);self.d.persist();self.d.apply_appearance();self.d.apply_ui_theme();self.d.top_bar.update_layout();self.status.setText('Preferences restored. Previous settings: '+str(backup))
        except (OSError,ValueError) as e:self.status.setText(str(e))
    def backup(self):
        from applications import Sticky
        for window in self.d.area.subWindowList():
            if isinstance(window.content,Sticky):window.content.persist()
        self.d.persist();path,_=QFileDialog.getSaveFileName(self,'Save Classic Backup',str(Path.home()/'Downloads'/('Classic Backup '+time.strftime('%Y-%m-%d')+'.zip')),'ZIP (*.zip)')
        if path:
            if not path.lower().endswith('.zip'):path+='.zip'
            self.start(create_backup,(self.d.disk.root,json.loads(json.dumps(self.d.state)),path))
    def recover(self):
        path,_=QFileDialog.getOpenFileName(self,'Recover Classic Backup',str(Path.home()/'Downloads'),'ZIP (*.zip)')
        if path:self.start(recover_backup,(path,self.d.disk.root/'Recovered Backups'))
    def start(self,fn,args):
        if self.worker and self.worker.isRunning():return
        self.save.setEnabled(False);self.restore.setEnabled(False);self.status.setText('Working… Keep this window open.');self.worker=BackupWorker(fn,args,self);self.worker.done.connect(self.complete);self.worker.failed.connect(self.failed);self.worker.finished.connect(self.ready);self.worker.start()
    def complete(self,path):self.status.setText('Completed: '+path);self.d.disk_changed.emit();self.d.notify('Backup & Recovery','Completed: '+Path(path).name)
    def failed(self,message):self.status.setText('Could not finish: '+message);self.d.play_sound('error')
    def ready(self):self.save.setEnabled(True);self.restore.setEnabled(True)
    def can_close(self):
        if self.worker and self.worker.isRunning():QMessageBox.information(self,'Backup in progress','Wait for the backup or recovery to finish before closing.');return False
        return True


def validated_preferences(path):
    import re
    path=Path(path)
    if path.stat().st_size>65536:raise ValueError('Preference file exceeds 64 KB.')
    data=json.loads(path.read_text())
    if not isinstance(data,dict):raise ValueError('Expected a preference object.')
    out={}
    for key in ('high_contrast','reduce_motion','clock_24','clock_seconds','clock_date','compact_bar','sounds_enabled'):
        if key in data:
            if type(data[key]) is not bool:raise ValueError('Invalid '+key)
            out[key]=data[key]
    for key,choices in [('mode',('light','dark')),('ui_density',('Compact','Comfortable')),('open_effect',('Soft Zoom','Fade','Slide','None')),('close_effect',('Soft Zoom','Fade','Slide','None'))]:
        if key in data:
            if data[key] not in choices:raise ValueError('Invalid '+key)
            out[key]=data[key]
    if 'text_size' in data:
        if type(data['text_size']) is not int or not 11<=data['text_size']<=24:raise ValueError('Invalid text size.')
        out['text_size']=data['text_size']
    if 'accent' in data:
        if not isinstance(data['accent'],str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',data['accent']):raise ValueError('Invalid accent color.')
        out['accent']=data['accent']
    if not out:raise ValueError('No supported preferences were found.')
    return out
