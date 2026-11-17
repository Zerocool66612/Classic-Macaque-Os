import random
import chess
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import *
from gnu_chess import GNUChess,engine_path
class Chess(QWidget):
    app_name='Chess'
    def __init__(self,d):
        super().__init__();self.d=d;self.board=chess.Board();self.selected=None;self.cpu=True;self.buttons=[];layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row);self.mode=QComboBox();self.mode.addItems(['Play computer · you are White','Two players']);self.mode.currentIndexChanged.connect(self.set_mode);row.addWidget(self.mode)
        for text,fn in [('New game',self.new),('Undo',self.undo)]:b=QPushButton(text);b.clicked.connect(fn);row.addWidget(b)
        self.engine=GNUChess(self);self.engine.move_ready.connect(self.engine_move);self.engine.failed.connect(self.engine_failed);self.engine_error=''
        engine_row=QHBoxLayout();layout.addLayout(engine_row);engine_row.addWidget(QLabel('Computer engine'))
        self.engine_choice=QComboBox();self.engine_choice.addItems(['GNU Chess','Practice']);self.engine_choice.setCurrentText(d.state.get('chess_engine','GNU Chess' if engine_path() else 'Practice'));self.engine_choice.currentTextChanged.connect(self.engine_changed);engine_row.addWidget(self.engine_choice)
        self.level=QComboBox();self.level.addItems(['Quick','Normal','Deep']);self.level.setCurrentText(d.state.get('chess_level','Normal'));self.level.currentTextChanged.connect(self.engine_changed);engine_row.addWidget(self.level)
        grid=QGridLayout();grid.setSpacing(0);layout.addLayout(grid,1)
        for rank in range(7,-1,-1):
            for file in range(8):
                square=chess.square(file,rank);b=QPushButton();b.setMinimumSize(44,44);b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding);b.setFont(QFont('DejaVu Sans',30));b.clicked.connect(lambda checked=False,s=square:self.click(s));grid.addWidget(b,7-rank,file);self.buttons.append((square,b))
        self.status=QLabel();layout.addWidget(self.status);help=QLabel('Click a piece, then its destination. Castling, en passant and check rules supported. Promotion chooses a queen. GNU Chess runs locally inside Macaque. Practice uses the original simple computer. Quick, Normal and Deep set thinking time.');help.setWordWrap(True);layout.addWidget(help)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.computer)
        try:
            for move in d.state.get('chess_moves',[]):self.board.push_uci(move)
        except (ValueError,AssertionError):self.board=chess.Board()
        self.refresh();self.schedule()
    def save(self):self.d.state['chess_moves']=[m.uci() for m in self.board.move_stack];self.d.persist()
    def refresh(self):
        legal={m.to_square for m in self.board.legal_moves if m.from_square==self.selected} if self.selected is not None else set()
        for square,b in self.buttons:
            piece=self.board.piece_at(square);b.setText(piece.unicode_symbol() if piece else ('·' if square in legal else ''));b.setToolTip(chess.square_name(square));color='#a9d7ff' if square==self.selected else '#a8ba86' if square in legal else '#e7dfcc' if (chess.square_file(square)+chess.square_rank(square))%2 else '#557e78';b.setStyleSheet(f'background:{color};color:#131e27;border:0;border-radius:0;padding:0;font-size:36px;font-family:DejaVu Sans;')
        outcome=self.board.outcome(claim_draw=True)
        if outcome:self.status.setText('Game over · '+self.board.result(claim_draw=True)+' · '+outcome.termination.name.replace('_',' ').title())
        else:self.status.setText(('White' if self.board.turn else 'Black')+' to move'+(' · Check!' if self.board.is_check() else '')+(' · GNU Chess thinking…' if self.engine.busy else '')+(' · '+self.engine_error if self.engine_error else ''))
    def schedule(self):
        if self.cpu and self.board.turn==chess.BLACK and not self.board.is_game_over(claim_draw=True):self.timer.start(300)
    def set_mode(self,index):self.cpu=index==0;self.timer.stop();self.engine.cancel();self.engine_error='';self.refresh();self.schedule()
    def click(self,square):
        if self.board.is_game_over(claim_draw=True) or self.cpu and self.board.turn==chess.BLACK:return
        if self.selected is not None:
            move=chess.Move(self.selected,square)
            if self.board.piece_type_at(self.selected)==chess.PAWN and chess.square_rank(square) in (0,7):move.promotion=chess.QUEEN
            if move in self.board.legal_moves:self.board.push(move);self.selected=None;self.save();self.refresh();self.schedule();return
        piece=self.board.piece_at(square);self.selected=square if piece and piece.color==self.board.turn else None;self.refresh()
    def computer(self):
        if not self.cpu or self.board.turn!=chess.BLACK or self.board.is_game_over(claim_draw=True):return
        if self.engine_choice.currentText()=='GNU Chess':
            self.engine_error='';self.engine.request(self.board.fen(),{'Quick':250,'Normal':1000,'Deep':2500}[self.level.currentText()]);self.refresh();return
        values={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3.2,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
        def score(move):
            self.board.push(move)
            if self.board.is_checkmate():value=10000
            else:
                value=sum(len(self.board.pieces(p,chess.BLACK))*v-len(self.board.pieces(p,chess.WHITE))*v for p,v in values.items());value+=.15 if self.board.is_check() else 0
                # Discourage hanging pieces against the immediate reply.
                danger=max((values.get(self.board.piece_type_at(reply.to_square),0) for reply in self.board.legal_moves if self.board.is_capture(reply)),default=0);value-=danger*.8
            self.board.pop();return value+random.random()*.08
        moves=list(self.board.legal_moves);move=max(moves,key=score);self.board.push(move);self.save();self.refresh()
    def engine_changed(self,*args):
        self.timer.stop();self.engine.cancel();self.engine_error=''
        self.d.state.update(chess_engine=self.engine_choice.currentText(),chess_level=self.level.currentText());self.d.persist();self.refresh();self.schedule()
    def engine_move(self,fen,uci):
        if not self.cpu or self.board.fen()!=fen or self.board.turn!=chess.BLACK:return
        move=chess.Move.from_uci(uci)
        if move not in self.board.legal_moves:return
        self.board.push(move);self.selected=None;self.save();self.refresh()
    def engine_failed(self,message):self.engine_error=message;self.refresh()
    def new(self):
        if self.board.move_stack and QMessageBox.question(self,'New chess game?','Replace the current saved game?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        self.timer.stop();self.engine.cancel();self.engine_error='';self.board.reset();self.selected=None;self.save();self.refresh()
    def undo(self):
        self.timer.stop();self.engine.cancel();self.engine_error=''
        if self.board.move_stack:self.board.pop()
        if self.cpu and self.board.turn==chess.BLACK and self.board.move_stack:self.board.pop()
        self.selected=None;self.save();self.refresh();self.schedule()
    def can_close(self):self.timer.stop();self.engine.cancel();self.save();return True
