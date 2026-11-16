"""Web download UI and request lifecycle, with deterministic request signals."""
import os,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
from unittest.mock import Mock,patch
from PySide6.QtCore import QObject,Signal,QUrl
from PySide6.QtWidgets import QApplication,QFileDialog,QMessageBox
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest as R
from browser_app import Browser
class Request(QObject):
 receivedBytesChanged=Signal();totalBytesChanged=Signal();isFinishedChanged=Signal()
 def __init__(self,name='installer.flatpakref'):super().__init__();self.name=name;self.current=R.DownloadRequested;self.saved=None;self.directory=None;self.accepted=False
 def url(self):return QUrl('https://example.org/api/download?id=1')
 def suggestedFileName(self):return self.name
 def setDownloadDirectory(self,value):self.directory=value
 def setDownloadFileName(self,value):self.saved=value
 def receivedBytes(self):return 10
 def totalBytes(self):return 100
 def state(self):return self.current
 def accept(self):self.accepted=True;self.current=R.DownloadInProgress
 def cancel(self):self.current=R.DownloadCancelled;self.isFinishedChanged.emit()
 def interruptReasonString(self):return 'Network disconnected'
app=QApplication([])
with tempfile.TemporaryDirectory() as temp:
 d=Mock();d.disk.root=Path(temp)
 with patch('browser_app.os.geteuid',return_value=0):b=Browser(d)
 # Server filename wins over opaque URL; existing downloads get a unique suggestion.
 folder=Path(temp)/'Downloads';folder.mkdir();(folder/'installer.flatpakref').write_text('old')
 r=Request()
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(folder/'new.flatpakref'),'')) as save:b.request_download(r)
 assert r.accepted and r.saved=='new.flatpakref' and r.directory==str(folder)
 assert Path(save.call_args.args[2]).name!='installer.flatpakref'
 assert r in b.downloads
 r.current=R.DownloadCompleted;r.isFinishedChanged.emit()
 assert not b.downloads and 'Saved:' in b.status.text();d.disk_changed.emit.assert_called_once()
 # Cancellation does not report success or emit filesystem refresh.
 d.disk_changed.emit.reset_mock();r=Request()
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(folder/'cancel.iso'),'')):b.request_download(r)
 with patch.object(QMessageBox,'question',return_value=QMessageBox.No):assert b.can_close() is False
 r.cancel();assert not b.downloads and b.status.text()=='Cancelled';d.disk_changed.emit.assert_not_called()
 r=Request()
 with patch.object(QFileDialog,'getSaveFileName',return_value=('','')):b.request_download(r)
 assert not r.accepted and not b.downloads
 r=Request()
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(folder/'fail.iso'),'')):b.request_download(r)
 r.current=R.DownloadInterrupted;r.isFinishedChanged.emit();assert 'Network disconnected' in b.status.text()
 # Only deliberately clicked links can open another tab, always inside Macaque.
 req=Mock();req.isUserInitiated.return_value=False
 b.new_window_requested(req);req.openIn.assert_not_called()
 req.isUserInitiated.return_value=True;req.requestedUrl.return_value=QUrl('https://example.org/file')
 view=Mock()
 with patch.object(b,'new_tab',return_value=view):b.new_window_requested(req)
 req.openIn.assert_called_once_with(view.page())
 b.deleteLater();app.processEvents()
print('PASS: browser download filenames, progress lifecycle, success, failure, cancellation, close guard and user-initiated tabs.')
