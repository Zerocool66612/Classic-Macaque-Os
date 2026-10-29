import os,tempfile,time
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from terminal_app import Terminal
app=QApplication([])
def until(test,seconds=4):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  QTest.qWait(30)
  if test():return
 raise AssertionError('Timed out waiting for PTY output: '+t.view.toPlainText())
with tempfile.TemporaryDirectory() as tmp:
 t=Terminal(None);t.resize(900,500);t.show();assert t.process is not None
 t.send(b"export PS1='PROMPT> '; printf '\\nPTY_READY\\n'\r");until(lambda:'PTY_READY' in t.view.toPlainText())
 # Verify real execution, rather than just terminal echo of the typed command.
 output=os.path.join(tmp,'result')
 t.send(("printf '%s' $((17*19)) > "+output+'\r').encode());until(lambda:os.path.exists(output));assert open(output).read()=='323'
 t.send(b"printf '\\033[2J\\033[HANSI_OK\\n'\r");until(lambda:'ANSI_OK' in t.view.toPlainText())
 t.send(b'sleep 30\r');QTest.qWait(100);QTest.keyClick(t.view,Qt.Key_C,Qt.ControlModifier);t.send(b"printf '\\nINTERRUPT_OK\\n'\r");until(lambda:'INTERRUPT_OK' in t.view.toPlainText())
 t.resize(700,400);QTest.qWait(50);assert t.screen.columns>=20
 with patch.object(QMessageBox,'question',return_value=QMessageBox.No):assert not t.can_close()
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):assert t.can_close()
 until(lambda:t.process.poll() is not None);assert t.fd is None
print('Real PTY execution, ANSI screen, Ctrl+C, resize, close cancellation and shell cleanup passed')
