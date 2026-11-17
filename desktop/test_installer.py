import os,tempfile
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['MACAQUE_SILENT']='1'
from unittest.mock import patch,Mock
from PySide6.QtWidgets import QApplication,QMessageBox,QPushButton
from PySide6.QtGui import QCloseEvent
from PySide6.QtTest import QTest
from PySide6.QtCore import QTimer,Qt
from desktop import Desktop
from installer_support import installer_available
app=QApplication([]);app.setQuitOnLastWindowClosed(False);app.setDesktopFileName('org.macaque.Classic')
with tempfile.TemporaryDirectory() as data:
 d=Desktop(data);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True);d.show();QTest.qWait(20)
 assert not installer_available()
 with patch('installer_support.installer_available',return_value=False),patch('installer_support.subprocess.Popen') as spawn:
  d.launch_installer_wizard();spawn.assert_not_called()
 with patch('installer_support.installer_available',return_value=True),patch('installer_support.QMessageBox.question',return_value=QMessageBox.No),patch('installer_support.subprocess.Popen') as spawn:
  d.launch_installer_wizard();spawn.assert_not_called()
 process=Mock();process.poll.return_value=None
 with patch('installer_support.installer_available',return_value=True),patch('installer_support.QMessageBox.question',return_value=QMessageBox.Yes),patch('installer_support.subprocess.Popen',return_value=process) as spawn:
  d.launch_installer_wizard();assert spawn.call_args.args[0]==['/usr/bin/sudo','-n','--','/usr/local/libexec/macaque-wayland-installer',os.environ.get('WAYLAND_DISPLAY','')];assert d.installer_busy()
  event=QCloseEvent();d.closeEvent(event);assert not event.isAccepted()
 process.poll.return_value=0;assert not d.installer_busy();d.quitting=True;d.hide()
 process.poll.return_value=None;d.installer_process=None
 with patch.dict(os.environ,{'MACAQUE_WAYLAND_SESSION':'1','WAYLAND_DISPLAY':'wayland-7'}),patch('installer_support.installer_available',return_value=True),patch('installer_support.QMessageBox.question',return_value=QMessageBox.Yes),patch('installer_support.subprocess.Popen',return_value=process) as spawn:
  d.launch_installer_wizard();assert spawn.call_args.args[0]==['/usr/bin/sudo','-n','--','/usr/local/libexec/macaque-wayland-installer','wayland-7']
 process.poll.return_value=0
# Exercise the actual first Install click without inventory, disk or sudo calls.
with tempfile.TemporaryDirectory() as data:
 with patch('desktop.installer_available',return_value=True),patch('installer_support.installer_available',return_value=True),patch('install_preparation.InstallPreparation.refresh'),patch('installer_support.subprocess.Popen') as spawn:
  d=Desktop(data);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True,single_click=False);d.setGeometry(d.screen().availableGeometry());d.show();QTest.qWait(50)
  icon=next(b for b in d.icons if b.property('iconKey')=='Install Macaque Classic')
  QTest.mouseDClick(icon,Qt.LeftButton);QTest.qWait(100)
  screen=d.installer_screen
  assert screen.isFullScreen() and screen.geometry()==screen.screen().geometry()
  assert screen not in d.area.subWindowList()
  assert d.launch_installer() is screen
  screen.content.busy=True;event=QCloseEvent();screen.closeEvent(event);assert not event.isAccepted() and d.installer_busy()
  QTest.keyClick(screen,Qt.Key_Escape);assert screen.isVisible()
  screen.content.busy=False
  problems=[]
  def dismiss_confirmation():
   box=QApplication.activeModalWidget()
   try:
    assert isinstance(box,QMessageBox)
    assert box.parentWidget() is screen
    assert not box.isFullScreen() and not box.isMaximized()
    assert box.width()<screen.width() and box.height()<screen.height()
   except AssertionError:problems.append('Confirmation did not stay normal-sized')
   finally:
    if box is not None:box.done(QMessageBox.No)
  QTimer.singleShot(30,dismiss_confirmation);d.launch_installer_wizard()
  assert not problems and screen.isVisible();spawn.assert_not_called()
  with patch.object(d,'launch_terminal') as terminal:
   screen.content.open_terminal();assert not screen.isVisible();terminal.assert_called_once()
  d.launch_installer();QTest.qWait(20);assert screen.isFullScreen() and screen.isVisible()
  child=Mock();child.poll.return_value=None;spawn.return_value=child
  with patch('installer_support.QMessageBox.question',return_value=QMessageBox.Yes):d.launch_installer_wizard()
  assert spawn.call_count==1 and not screen.isVisible()
  child.poll.return_value=0;d.installer_watch.stop()
  other=d.launch('Calculator');QTest.qWait(20);assert not other.isFullScreen() and not other.isMaximized()
  back=next(b for b in screen.findChildren(QPushButton) if b.text()=='Back to Desktop')
  QTest.mouseClick(back,Qt.LeftButton);QTest.qWait(20);assert not screen.isVisible()
  assert d.launch_installer() is screen;QTest.qWait(20);QTest.keyClick(screen,Qt.Key_Escape);QTest.qWait(20);assert not screen.isVisible()
  d.quitting=True;d.close();QTest.qWait(20)
print('PASS: actual Install click fills the screen, reuses one preparation view, keeps confirmations normal-sized, preserves busy/cancel guards, and hands off to the wizard; no real disk/sudo processes launched.')
