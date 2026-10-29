import os,tempfile
from pathlib import Path
from unittest.mock import patch,Mock
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject,Signal,QUrl,QTimer
from PySide6.QtNetwork import QNetworkReply,QNetworkRequest
from downloads import DownloadFile,download_url,download_name,Downloads
from desktop import Desktop
class Reply(QObject):
 readyRead=Signal();downloadProgress=Signal(int,int);finished=Signal()
 def __init__(self,data,status=200,error=QNetworkReply.NoError):super().__init__();self.data=data;self.code=status;self.err=error
 def readAll(self):data=self.data;self.data=b'';return data
 def attribute(self,key):return self.code
 def error(self):return self.err
 def errorString(self):return 'Simulated network failure'
 def abort(self):self.err=QNetworkReply.OperationCanceledError;self.finished.emit()
app=QApplication([])
for bad in ['http://example.com/file','file:///etc/passwd','https://user:secret@example.com/file','not a link']:
 try:download_url(bad)
 except ValueError:pass
 else:raise AssertionError('Unsafe URL accepted')
assert download_name(QUrl('https://example.com/path/a.flatpakref'))=='a.flatpakref'
with tempfile.TemporaryDirectory() as temp:
 directory=Path(temp)/'Downloads';sink=DownloadFile(directory,'safe.txt');sink.write(b'hello');assert sink.finish().read_bytes()==b'hello';other=DownloadFile(directory,'safe.txt');assert other.target.name!='safe.txt';other.cancel();assert not list(directory.glob('.download-*'))
 sink=DownloadFile(directory,'failed.txt')
 with patch('downloads.LIMIT',3):
  try:sink.write(b'too long')
  except ValueError:pass
  else:raise AssertionError('Size limit not enforced')
 sink.cancel();assert not (directory/'failed.txt').exists()
 d=Desktop(Path(temp)/'data');d.show();app.processEvents();w=d.launch('Downloads');view=w.content;assert d.launch('Downloads') is w
 view.url.setText('https://example.com/org.example.App.flatpakref');reply=Reply(b'[Flatpak Ref]\nName=org.example.App\n')
 with patch.object(view.network,'get',return_value=reply):view.start()
 reply.readyRead.emit();reply.finished.emit();assert view.completed and view.completed.read_bytes().startswith(b'[Flatpak Ref]');assert view.install_button.isEnabled()
 fake=Mock()
 with patch.object(d,'launch',return_value=fake) as launch:view.install();launch.assert_called_once_with('Flatpak Apps');fake.content.install_path.assert_called_once_with(str(view.completed))
 view.url.setText('https://example.com/failure.txt');reply=Reply(b'not found',404)
 with patch.object(view.network,'get',return_value=reply):view.start()
 reply.finished.emit();assert view.completed is None and 'Not saved' in view.status.text();assert not (d.disk.root/'Downloads/failure.txt').exists()
 view.url.setText('https://example.com/cancel.txt');reply=Reply(b'partial')
 with patch.object(view.network,'get',return_value=reply):view.start()
 reply.readyRead.emit();view.cancel();assert not (d.disk.root/'Downloads/cancel.txt').exists();assert not list((d.disk.root/'Downloads').glob('.download-*'))
 d.quitting=True;d.close()
print('PASS: URL and filename handling; no overwrite; size limit; cancellation cleanup; actual download-widget success/failure callbacks with simulated replies; Flatpak installation handoff. External HTTPS download not verified.')
