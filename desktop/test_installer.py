import os,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from unittest.mock import patch,Mock
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtGui import QCloseEvent
from PySide6.QtTest import QTest
from desktop import Desktop
from installer_support import installer_available
app=QApplication([])
with tempfile.TemporaryDirectory() as data:
 d=Desktop(data);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True);d.show();QTest.qWait(20)
 assert not installer_available()
 with patch('installer_support.installer_available',return_value=False),patch('installer_support.subprocess.Popen') as spawn:
  d.launch_installer_wizard();spawn.assert_not_called()
 with patch('installer_support.installer_available',return_value=True),patch('installer_support.QMessageBox.question',return_value=QMessageBox.No),patch('installer_support.subprocess.Popen') as spawn:
  d.launch_installer_wizard();spawn.assert_not_called()
 process=Mock();process.poll.return_value=None
 with patch('installer_support.installer_available',return_value=True),patch('installer_support.QMessageBox.question',return_value=QMessageBox.Yes),patch('installer_support.subprocess.Popen',return_value=process) as spawn:
  d.launch_installer_wizard();assert spawn.call_args.args[0]==['/usr/bin/sudo','-n','--','/usr/bin/calamares'];assert d.installer_busy()
  event=QCloseEvent();d.closeEvent(event);assert not event.isAccepted()
 process.poll.return_value=0;assert not d.installer_busy();d.quitting=True;d.hide()
print('Installer launcher/exit-guard checks passed. No real installer process launched.')
