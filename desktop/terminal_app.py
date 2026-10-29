"""An interactive Linux PTY inside the ordinary Macaque window frame."""
import errno,fcntl,os,pty,signal,struct,subprocess,sys,termios
from pathlib import Path
import pyte
from PySide6.QtCore import Qt,QSocketNotifier,QTimer,QEvent
from PySide6.QtGui import QFont,QFontMetrics,QTextCursor,QColor,QKeySequence
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPlainTextEdit,QMessageBox,QMenu,QApplication,QTextEdit

class TerminalView(QPlainTextEdit):
    def __init__(self,owner):
        super().__init__();self.owner=owner;self.setReadOnly(True);self.setLineWrapMode(QPlainTextEdit.NoWrap);self.setFont(QFont('DejaVu Sans Mono',12));self.setStyleSheet('QPlainTextEdit {background:#172127;color:#f0f3f5;border:0;}');self.setContextMenuPolicy(Qt.CustomContextMenu);self.customContextMenuRequested.connect(self.menu)
    def menu(self,pos):
        m=QMenu(self);a=m.addAction('Copy',self.copy);a.setEnabled(self.textCursor().hasSelection());m.addAction('Paste',self.owner.paste);m.addAction('Select All',self.selectAll);m.exec(self.mapToGlobal(pos));m.deleteLater()
    def event(self,e):
        if e.type()==QEvent.ShortcutOverride and e.modifiers()&Qt.ControlModifier:e.accept();return True
        return super().event(e)
    def keyPressEvent(self,e):
        key=e.key();mods=e.modifiers()
        if mods&Qt.ControlModifier and mods&Qt.ShiftModifier:
            if key==Qt.Key_C:self.copy();return
            if key==Qt.Key_V:self.owner.paste();return
        if mods&Qt.ShiftModifier and key in (Qt.Key_PageUp,Qt.Key_PageDown):
            (self.owner.screen.prev_page if key==Qt.Key_PageUp else self.owner.screen.next_page)();self.owner.render();return
        special={Qt.Key_Return:b'\r',Qt.Key_Enter:b'\r',Qt.Key_Backspace:b'\x7f',Qt.Key_Tab:b'\t',Qt.Key_Escape:b'\x1b',Qt.Key_Up:b'\x1b[A',Qt.Key_Down:b'\x1b[B',Qt.Key_Right:b'\x1b[C',Qt.Key_Left:b'\x1b[D',Qt.Key_Home:b'\x1b[H',Qt.Key_End:b'\x1b[F',Qt.Key_Delete:b'\x1b[3~',Qt.Key_PageUp:b'\x1b[5~',Qt.Key_PageDown:b'\x1b[6~'}
        if mods&Qt.ControlModifier and Qt.Key_A<=key<=Qt.Key_Z:data=bytes([key-Qt.Key_A+1])
        else:data=special.get(key,e.text().encode())
        if mods&Qt.AltModifier and data:data=b'\x1b'+data
        if data:self.owner.send(data)
    def resizeEvent(self,e):super().resizeEvent(e);self.owner.resize_pty()
    def wheelEvent(self,e):
        if e.angleDelta().y()>0:self.owner.screen.prev_page()
        else:self.owner.screen.next_page()
        self.owner.render()

class Terminal(QWidget):
    app_name='Terminal'
    def __init__(self,d,command=None):
        super().__init__();self.d=d;self.fd=None;self.process=None;self.closed=False;self.screen=pyte.HistoryScreen(100,28,history=2000);self.stream=pyte.ByteStream(self.screen)
        self.screen.write_process_input=lambda text:self.send(text.encode())
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);self.view=TerminalView(self);layout.addWidget(self.view,1);self.status=QLabel('Linux shell · Ctrl+Shift+C / V copy and paste · Shift+PageUp / Down scroll');layout.addWidget(self.status)
        self.flush=QTimer(self);self.flush.setSingleShot(True);self.flush.timeout.connect(self.render)
        try:
            master,slave=pty.openpty();self.fd=master;os.set_blocking(master,False);self.resize_pty()
            env=dict(os.environ,TERM='xterm-256color')
            for key in ['QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','LD_LIBRARY_PATH','PYTHONPATH']:env.pop(key,None)
            try:self.process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('terminal_child.py')),*(command or [])],stdin=slave,stdout=slave,stderr=slave,env=env,cwd=str(Path.home()),start_new_session=True,close_fds=True)
            finally:os.close(slave)
            self.notifier=QSocketNotifier(master,QSocketNotifier.Read,self);self.notifier.activated.connect(self.read_ready)
            self.poll=QTimer(self);self.poll.timeout.connect(self.check_exit);self.poll.start(300);self.view.setFocus()
        except (OSError,subprocess.SubprocessError) as ex:self.status.setText('Terminal could not start: '+str(ex));self.cleanup()
    def resize_pty(self):
        if not hasattr(self,'view'):return
        fm=QFontMetrics(self.view.font());cols=max(20,self.view.viewport().width()//max(1,fm.horizontalAdvance('M')));rows=max(5,self.view.viewport().height()//max(1,fm.lineSpacing()))
        self.screen.resize(lines=rows,columns=cols)
        if self.fd is not None:
            try:fcntl.ioctl(self.fd,termios.TIOCSWINSZ,struct.pack('HHHH',rows,cols,0,0))
            except OSError:pass
        if hasattr(self,'flush'):self.flush.start(20)
    def send(self,data):
        if self.fd is not None:
            try:os.write(self.fd,data)
            except (BlockingIOError,OSError):self.status.setText('Terminal input unavailable; try again.')
    def paste(self):self.send(QApplication.clipboard().text().encode())
    def read_ready(self,*args):
        if self.fd is None:return
        try:
            # Bound each callback so a verbose process cannot monopolize the UI.
            for i in range(32):
                data=os.read(self.fd,8192)
                if not data:self.notifier.setEnabled(False);break
                self.stream.feed(data)
        except BlockingIOError:pass
        except OSError as ex:
            if ex.errno!=errno.EIO:self.status.setText('Terminal read failed: '+str(ex))
            self.notifier.setEnabled(False)
        if not self.flush.isActive():self.flush.start(25)
    def render(self):
        selected=self.view.textCursor();a,b=selected.selectionStart(),selected.selectionEnd();self.view.setPlainText('\n'.join(self.screen.display))
        if a!=b:
            c=self.view.textCursor();c.setPosition(min(a,self.view.document().characterCount()-1));c.setPosition(min(b,self.view.document().characterCount()-1),QTextCursor.KeepAnchor);self.view.setTextCursor(c)
        else:
            c=QTextCursor(self.view.document().findBlockByNumber(self.screen.cursor.y));c.movePosition(QTextCursor.Right,QTextCursor.MoveAnchor,self.screen.cursor.x);self.view.setTextCursor(c)
        self.screen.dirty.clear()
    def check_exit(self):
        if self.process is not None and self.process.poll() is not None:self.poll.stop();self.status.setText(f'Shell exited ({self.process.returncode}). Close this window when finished.')
    def cleanup(self):
        if self.closed:return
        self.closed=True
        if hasattr(self,'notifier'):self.notifier.setEnabled(False)
        if hasattr(self,'poll'):self.poll.stop()
        if hasattr(self,'flush'):self.flush.stop()
        if self.fd is not None:os.close(self.fd);self.fd=None
        if self.process is not None and self.process.poll() is None:
            try:os.killpg(self.process.pid,signal.SIGHUP)
            except ProcessLookupError:pass
    def can_close(self):
        if self.process is not None and self.process.poll() is None:
            if QMessageBox.question(self,'Close Terminal','End this shell and its running programs?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return False
        self.cleanup();return True
