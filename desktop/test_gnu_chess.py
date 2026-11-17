"""Real engine moves, UI responsiveness and cancellation; no network games."""
import os,time
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import chess
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from gnu_chess import GNUChess,engine_path
from chess_app import Chess
app=QApplication([])
binary=os.environ.get('MACAQUE_TEST_GNUCHESS') or engine_path()
if not binary:raise RuntimeError('Install GNU Chess to run this integration check')
engine=GNUChess(binary=binary);moves=[];errors=[];beats=[]
engine.move_ready.connect(lambda f,m:moves.append((f,m)));engine.failed.connect(errors.append)
heartbeat=QTimer();heartbeat.timeout.connect(lambda:beats.append(1));heartbeat.start(10)
board=chess.Board();board.push_uci('e2e4');engine.request(board.fen(),250)
deadline=time.monotonic()+12
while not moves and not errors and time.monotonic()<deadline:QTest.qWait(20)
assert not errors,errors
assert len(moves)==1 and moves[0][0]==board.fen() and chess.Move.from_uci(moves[0][1]) in board.legal_moves,moves
assert len(beats)>3,'GUI event loop was blocked'
engine.request(board.fen(),2500);engine.cancel();QTest.qWait(100);assert not engine.busy and len(moves)==1
class Desktop:
 state={}
 def persist(self):pass
widget=Chess(Desktop());widget.engine.binary=binary;widget.engine_choice.setCurrentText('GNU Chess')
widget.board.push_uci('e2e4');widget.computer();assert widget.engine.busy
widget.undo();QTest.qWait(400);assert widget.board.fen()==chess.STARTING_FEN and not widget.engine.busy
widget.board.push_uci('d2d4');widget.computer();widget.set_mode(1);QTest.qWait(400)
assert len(widget.board.move_stack)==1 and not widget.engine.busy
widget.engine_move(chess.STARTING_FEN,'e2e4');assert len(widget.board.move_stack)==1
widget.can_close();widget.deleteLater();QTest.qWait(100)
missing=GNUChess(binary='/no/such/gnuchess');missing.failed.connect(errors.append);missing.request(board.fen(),100);QTest.qWait(100);assert errors and not missing.busy
print('PASS: real GNU Chess legal response, responsive Qt loop, undo/mode-change cancellation, stale-result rejection and missing-engine feedback.')
