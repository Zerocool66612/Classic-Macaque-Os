"""Asynchronous GNU Chess UCI client; no X11 frontend or UI-thread search."""
import shutil
from pathlib import Path
import chess
from PySide6.QtCore import QObject,QProcess,QTimer,Signal

def engine_path():
    return shutil.which('gnuchess') or next((str(p) for p in [Path('/usr/games/gnuchess'),Path('/usr/bin/gnuchess')] if p.is_file()),None)

class GNUChess(QObject):
    move_ready=Signal(str,str)
    failed=Signal(str)
    def __init__(self,parent=None,binary=None):
        super().__init__(parent);self.binary=binary;self.process=None;self.timeout=QTimer(self);self.timeout.setSingleShot(True);self.timeout.timeout.connect(lambda:self.fail('GNU Chess timed out. Try again or choose Practice.'))
    @property
    def busy(self):return self.process is not None
    def cancel(self):
        self.timeout.stop();p=self.process;self.process=None
        if p is not None:
            if p.state()!=QProcess.NotRunning:p.kill()
            else:p.deleteLater()
    def fail(self,message):self.cancel();self.failed.emit(message)
    def request(self,fen,milliseconds=1000):
        self.cancel();chess.Board(fen)
        binary=self.binary or engine_path()
        if not binary:self.failed.emit('GNU Chess is not installed. Install the desktop update or choose Practice.');return
        self.fen=fen;self.milliseconds=max(100,min(5000,int(milliseconds)));self.buffer=''
        p=QProcess(self);self.process=p
        p.setProgram(binary);p.setArguments(['--uci'])
        p.started.connect(lambda:self.send(p,'uci'))
        p.readyReadStandardOutput.connect(lambda:self.read(p))
        p.finished.connect(lambda *_:self.exited(p));p.finished.connect(p.deleteLater)
        p.errorOccurred.connect(lambda _:self.fail('Could not run GNU Chess: '+p.errorString()) if self.process is p else None)
        self.timeout.start(self.milliseconds+10000);p.start()
    def send(self,p,text):
        if self.process is p:p.write((text+'\n').encode())
    def read(self,p):
        if self.process is not p:return
        self.buffer+=bytes(p.readAllStandardOutput()).decode('utf-8','replace')
        while '\n' in self.buffer:
            line,self.buffer=self.buffer.split('\n',1);parts=line.strip().split()
            if not parts:continue
            if parts[0]=='uciok':self.send(p,'isready')
            elif parts[0]=='readyok':
                self.send(p,'position fen '+self.fen);self.send(p,'go movetime '+str(self.milliseconds))
            elif parts[0]=='bestmove':
                try:
                    move=chess.Move.from_uci(parts[1]);board=chess.Board(self.fen)
                    if move not in board.legal_moves:raise ValueError('illegal engine move')
                except (IndexError,ValueError):self.fail('GNU Chess returned an invalid move.');return
                fen=self.fen;self.timeout.stop();self.process=None
                p.write(b'quit\n');cleanup=QTimer(p);cleanup.setSingleShot(True);cleanup.timeout.connect(p.kill);cleanup.start(500)
                self.move_ready.emit(fen,move.uci());return
    def exited(self,p):
        if self.process is p:self.fail('GNU Chess stopped before choosing a move.')
