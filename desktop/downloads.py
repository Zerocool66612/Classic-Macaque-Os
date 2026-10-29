"""An internal HTTPS file downloader; downloaded content is never executed."""
import os,re,tempfile,shutil
from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QTimer
from PySide6.QtNetwork import QNetworkAccessManager,QNetworkRequest,QNetworkReply
from PySide6.QtWidgets import *
LIMIT=512*1024*1024
GIMP='https://flathub.org/repo/appstream/org.gimp.GIMP.flatpakref'

def download_url(text):
    url=QUrl(text.strip())
    if not url.isValid() or url.scheme().lower()!='https' or not url.host() or url.userInfo():raise ValueError('Enter an HTTPS file link without embedded login details.')
    url.setFragment('');return url

def download_name(url):
    value=url.fileName() or 'Download';value=re.sub(r'[\x00-\x1f<>:"/\\|?*]','_',value).strip('. ')
    return value[:160] or 'Download'

class DownloadFile:
    def __init__(self,directory,name):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True);self.target=self.directory/name;self.size=0
        from model import Disk
        self.target=Disk.unused(self.target);fd,path=tempfile.mkstemp(prefix='.download-',dir=self.directory);self.temp=Path(path);self.stream=os.fdopen(fd,'wb')
    def write(self,data):
        if self.size+len(data)>LIMIT:raise ValueError('Download exceeds the 512 MB limit.')
        self.stream.write(data);self.size+=len(data)
    def finish(self):
        self.stream.close()
        try:
            fd=os.open(self.target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            try:
                with os.fdopen(fd,'wb') as out,self.temp.open('rb') as source:shutil.copyfileobj(source,out)
            except Exception:self.target.unlink(missing_ok=True);raise
            return self.target
        finally:self.temp.unlink(missing_ok=True)
    def cancel(self):
        if not self.stream.closed:self.stream.close()
        self.temp.unlink(missing_ok=True)

class Downloads(QWidget):
    app_name='Downloads'
    def __init__(self,d):
        super().__init__();self.d=d;self.reply=None;self.file=None;self.completed=None;self.failure=None;self.network=QNetworkAccessManager(self);layout=QVBoxLayout(self);heading=QLabel('Classic Downloads');heading.setStyleSheet('font-size:21px;font-weight:bold');layout.addWidget(heading);label=QLabel('Paste a direct HTTPS file link. Files are saved in Macaque HD/Downloads.');label.setWordWrap(True);layout.addWidget(label);self.url=QLineEdit();self.url.setPlaceholderText('https://…/installer.flatpakref');layout.addWidget(self.url);row=QHBoxLayout();layout.addLayout(row);self.get=QPushButton('Download');self.get.clicked.connect(self.start);row.addWidget(self.get);self.cancel_button=QPushButton('Cancel');self.cancel_button.clicked.connect(self.cancel);self.cancel_button.setEnabled(False);row.addWidget(self.cancel_button);example=QPushButton('Use GIMP installer link');example.clicked.connect(lambda:self.url.setText(GIMP));row.addWidget(example);self.progress=QProgressBar();self.progress.setRange(0,100);layout.addWidget(self.progress);self.status=QLabel('Ready. This is a file downloader, not a web browser.');self.status.setWordWrap(True);layout.addWidget(self.status);row=QHBoxLayout();layout.addLayout(row);folder=QPushButton('Open Downloads');folder.clicked.connect(self.open_folder);row.addWidget(folder);self.open_button=QPushButton('Open downloaded file');self.open_button.setEnabled(False);self.open_button.clicked.connect(self.open_file);row.addWidget(self.open_button);self.install_button=QPushButton('Install downloaded Flatpak');self.install_button.setEnabled(False);self.install_button.clicked.connect(self.install);row.addWidget(self.install_button);layout.addWidget(QLabel('Maximum 512 MB per file. Cancel or failed downloads leave no final file.'));layout.addStretch();self.timeout=QTimer(self);self.timeout.setSingleShot(True);self.timeout.timeout.connect(self.timed_out)
    def start(self):
        if self.reply:return
        try:url=download_url(self.url.text());self.file=DownloadFile(self.d.disk.root/'Downloads',download_name(url))
        except (OSError,ValueError) as ex:self.status.setText(str(ex));return
        self.completed=None;self.failure=None;self.open_button.setEnabled(False);self.install_button.setEnabled(False);self.get.setEnabled(False);self.url.setEnabled(False);self.cancel_button.setEnabled(True);self.progress.setRange(0,0);self.status.setText('Connecting to '+url.host()+'…');request=QNetworkRequest(url);request.setAttribute(QNetworkRequest.RedirectPolicyAttribute,QNetworkRequest.NoLessSafeRedirectPolicy);request.setMaximumRedirectsAllowed(5);request.setTransferTimeout(30000);self.reply=self.network.get(request);self.reply.readyRead.connect(self.read);self.reply.downloadProgress.connect(self.update_progress);self.reply.finished.connect(self.finished);self.timeout.start(5*60*1000)
    def read(self):
        if not self.reply or self.failure:return
        try:self.file.write(bytes(self.reply.readAll()))
        except (OSError,ValueError) as ex:self.failure=str(ex);self.reply.abort()
    def update_progress(self,received,total):
        if total>LIMIT:self.failure='Download exceeds the 512 MB limit.';self.reply.abort();return
        if total>0:self.progress.setRange(0,100);self.progress.setValue(int(received*100/total))
        self.status.setText(f'Downloading · {received//1024:,} KB received')
    def finished(self):
        reply=self.reply
        if not reply:return
        self.timeout.stop();self.read();status=reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        try:
            if self.failure:raise ValueError(self.failure)
            if reply.error()!=QNetworkReply.NoError:raise ValueError(reply.errorString())
            if status is None or not 200<=int(status)<300:raise ValueError('The server did not return a successful download.')
            self.completed=self.file.finish();self.status.setText('Saved: Downloads / '+self.completed.name);self.open_button.setEnabled(True);self.install_button.setEnabled(self.completed.suffix.lower() in ('.flatpakref','.flatpak'));self.progress.setRange(0,100);self.progress.setValue(100);self.d.disk_changed.emit();self.d.play_sound('save')
        except (OSError,ValueError) as ex:self.file.cancel();self.status.setText('Not saved: '+str(ex));self.progress.setRange(0,100);self.progress.setValue(0)
        finally:self.reply=None;reply.deleteLater();self.file=None;self.get.setEnabled(True);self.url.setEnabled(True);self.cancel_button.setEnabled(False)
    def cancel(self):
        if self.reply:self.failure='Cancelled.';self.reply.abort()
    def timed_out(self):
        if self.reply:self.failure='Download timed out.';self.reply.abort()
    def open_folder(self):path=self.d.disk.root/'Downloads';path.mkdir(exist_ok=True);self.d.open_finder(path)
    def open_file(self):
        if self.completed:
            if self.completed.suffix.lower() in ('.flatpakref','.flatpak'):self.install()
            else:self.d.open_item(self.completed)
    def install(self):
        if self.completed and self.completed.suffix.lower() in ('.flatpakref','.flatpak'):self.d.launch('Flatpak Apps').content.install_path(str(self.completed))
    def can_close(self):
        if self.reply:self.cancel()
        if self.file:self.file.cancel()
        return True
