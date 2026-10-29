"""Built-in desktop utilities. All widgets live in Macaque's window area."""
import time,json,zipfile
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QPoint,QUrl
from PySide6.QtGui import QColor,QPainter,QPen,QImage,QFont
from PySide6.QtWidgets import *

class Tasks(QWidget):
    app_name='Tasks'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Tasks · automatically saved'));self.items=QListWidget();layout.addWidget(self.items);row=QHBoxLayout();self.entry=QLineEdit();self.entry.setPlaceholderText('What needs doing?');row.addWidget(self.entry);add=QPushButton('Add');row.addWidget(add);layout.addLayout(row);remove=QPushButton('Delete selected');layout.addWidget(remove)
        for value in d.state.get('tasks',[]):self.add(value['text'],value.get('done',False),False)
        add.clicked.connect(lambda:self.add(self.entry.text()));self.entry.returnPressed.connect(lambda:self.add(self.entry.text()));remove.clicked.connect(self.remove);self.items.itemChanged.connect(self.save)
    def add(self,text,done=False,save=True):
        if not text.strip():return
        item=QListWidgetItem(text.strip());item.setFlags(item.flags()|Qt.ItemIsUserCheckable|Qt.ItemIsEditable);item.setCheckState(Qt.Checked if done else Qt.Unchecked);self.items.addItem(item);self.entry.clear()
        if save:self.save()
    def remove(self):self.items.takeItem(self.items.currentRow());self.save()
    def save(self,*args):self.d.state['tasks']=[{'text':self.items.item(i).text(),'done':self.items.item(i).checkState()==Qt.Checked} for i in range(self.items.count())];self.d.persist()

class Clockwork(QWidget):
    app_name='Clockwork'
    def __init__(self,d):
        super().__init__();self.d=d;self.started=None;self.elapsed=0;self.deadline=None;layout=QVBoxLayout(self);self.clock=QLabel('00:00.0');self.clock.setAlignment(Qt.AlignCenter);self.clock.setStyleSheet('font-family:DejaVu Sans Mono;font-size:42px;');layout.addWidget(self.clock);row=QHBoxLayout();layout.addLayout(row)
        for text,fn in [('Start / Pause',self.toggle),('Reset',self.reset),('Lap',self.lap)]:b=QPushButton(text);b.clicked.connect(fn);row.addWidget(b)
        self.laps=QListWidget();layout.addWidget(self.laps);row=QHBoxLayout();layout.addLayout(row);self.minutes=QSpinBox();self.minutes.setRange(1,1440);self.minutes.setSuffix(' minutes');row.addWidget(self.minutes);b=QPushButton('Start countdown');b.clicked.connect(self.countdown);row.addWidget(b);self.status=QLabel('Stopwatch and countdown run while this window stays open.');layout.addWidget(self.status);self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(100)
    def value(self):return self.elapsed+(time.monotonic()-self.started if self.started is not None else 0)
    def toggle(self):
        if self.started is None:self.started=time.monotonic()
        else:self.elapsed=self.value();self.started=None
    def reset(self):self.started=None;self.elapsed=0;self.laps.clear();self.tick()
    def lap(self):self.laps.addItem(self.clock.text())
    def countdown(self):self.deadline=time.monotonic()+self.minutes.value()*60
    def tick(self):
        value=self.value();self.clock.setText(f'{int(value//60):02}:{value%60:04.1f}')
        if self.deadline is not None:
            remaining=max(0,int(self.deadline-time.monotonic()));self.status.setText(f'Countdown: {remaining//60:02}:{remaining%60:02}')
            if not remaining:self.deadline=None;self.status.setText('Time is up!');self.d.play_sound('notification')

class Canvas(QWidget):
    def __init__(self):
        super().__init__();self.image=QImage(900,600,QImage.Format_RGB32);self.image.fill(Qt.white);self.setFixedSize(900,600);self.color=QColor('#1e5559');self.width=8;self.last=None;self.undo=[];self.dirty=False
    def paintEvent(self,e):p=QPainter(self);p.drawImage(0,0,self.image)
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            self.undo.append(self.image.copy());self.undo=self.undo[-15:];self.last=e.position().toPoint();self.stroke(self.last)
    def stroke(self,pos):
        p=QPainter(self.image);p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(self.color,self.width,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawPoint(pos) if self.last==pos else p.drawLine(self.last,pos);p.end();self.last=pos;self.dirty=True;self.update()
    def mouseMoveEvent(self,e):
        if self.last is not None and e.buttons()&Qt.LeftButton:self.stroke(e.position().toPoint())
    def mouseReleaseEvent(self,e):self.last=None
    def revert(self):
        if self.undo:self.image=self.undo.pop();self.dirty=True;self.update()

class Paint(QWidget):
    app_name='Macaque Paint'
    def __init__(self,d):
        super().__init__();self.d=d;self.canvas=Canvas();layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row)
        for color in ['#111111','#ffffff','#2e7d72','#386bb6','#c54e54','#e6b84c','#8a65a9']:
            b=QPushButton();b.setFixedSize(26,26);b.setStyleSheet('background:'+color);b.setToolTip('Brush '+color);b.clicked.connect(lambda checked=False,c=color:setattr(self.canvas,'color',QColor(c)));row.addWidget(b)
        size=QSpinBox();size.setRange(1,60);size.setValue(8);size.setPrefix('Brush ');size.valueChanged.connect(lambda n:setattr(self.canvas,'width',n));row.addWidget(size)
        for text,fn in [('Undo',self.canvas.revert),('Save PNG',self.save)]:b=QPushButton(text);b.clicked.connect(fn);row.addWidget(b)
        scroll=QScrollArea();scroll.setWidget(self.canvas);layout.addWidget(scroll)
    def save(self):
        path,_=QFileDialog.getSaveFileName(self,'Save Drawing',str(self.d.disk.root/'Documents'/'Drawing.png'),'PNG (*.png)')
        if not path:return False
        if not path.lower().endswith('.png'):path+='.png'
        if not self.canvas.image.save(path,'PNG'):self.d.error('Could not save the drawing.');return False
        self.canvas.dirty=False;self.d.disk_changed.emit();self.d.play_sound('save');return True
    def can_close(self):
        if not self.canvas.dirty:return True
        choice=QMessageBox.question(self,'Save drawing?','Save your drawing before closing?',QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel,QMessageBox.Save)
        return self.save() if choice==QMessageBox.Save else choice==QMessageBox.Discard

class ArchiveViewer(QWidget):
    app_name='Archive Viewer'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);b=QPushButton('Open ZIP…');b.clicked.connect(self.open);layout.addWidget(b);self.items=QTreeWidget();self.items.setHeaderLabels(['Name','Bytes','Compressed']);layout.addWidget(self.items);self.status=QLabel('Inspect ZIP contents without extracting files.');layout.addWidget(self.status)
    def open(self):
        path,_=QFileDialog.getOpenFileName(self,'Open ZIP',str(self.d.disk.root),'ZIP (*.zip)')
        if path:self.load(path)
    def load(self,path):
        try:
            with zipfile.ZipFile(path) as archive:
                entries=archive.infolist();self.items.clear()
                for entry in entries[:10000]:self.items.addTopLevelItem(QTreeWidgetItem([entry.filename,str(entry.file_size),str(entry.compress_size)]))
                self.status.setText(f'{len(entries)} entries · displaying up to 10,000 · nothing extracted')
        except (OSError,zipfile.BadZipFile) as ex:self.d.error(ex)

class Characters(QWidget):
    app_name='Character Map'
    def __init__(self,d):
        super().__init__();layout=QVBoxLayout(self);layout.addWidget(QLabel('Click a symbol to copy it.'));grid=QGridLayout();layout.addLayout(grid)
        for i,c in enumerate('©®™°±×÷∞≠≤≥πµΩαβγδ←↑→↓↔✓✗★☆♥♦♣♠♫♪☀☁☂☕✉⚙⌘⌥⇧⏎•…—–§¶€£¥¢'):
            b=QPushButton(c);b.setStyleSheet('font-family:DejaVu Sans;font-size:22px;');b.clicked.connect(lambda checked=False,c=c:QApplication.clipboard().setText(c));grid.addWidget(b,i//10,i%10)
        layout.addStretch()

class MediaPlayer(QWidget):
    app_name='Media Player'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self)
        try:
            from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
            from PySide6.QtMultimediaWidgets import QVideoWidget
            self.player=QMediaPlayer(self);self.audio=QAudioOutput(self);self.player.setAudioOutput(self.audio);video=QVideoWidget();self.player.setVideoOutput(video);layout.addWidget(video,1);row=QHBoxLayout();layout.addLayout(row)
            for text,fn in [('Open…',self.open),('Play',self.player.play),('Pause',self.player.pause),('Stop',self.player.stop)]:b=QPushButton(text);b.clicked.connect(fn);row.addWidget(b)
            self.position=QSlider(Qt.Horizontal);self.player.durationChanged.connect(lambda n:self.position.setRange(0,n));self.player.positionChanged.connect(self.position.setValue);self.position.sliderMoved.connect(self.player.setPosition);layout.addWidget(self.position);self.status=QLabel('Local audio and video · codec support depends on Qt.');layout.addWidget(self.status);self.player.errorOccurred.connect(lambda *a:self.status.setText(self.player.errorString()))
        except ImportError:layout.addWidget(QLabel('Qt Multimedia is unavailable. Reinstall requirements.txt.'))
    def open(self):
        path,_=QFileDialog.getOpenFileName(self,'Open Media',str(self.d.disk.root/'Documents'),'Media (*.wav *.mp3 *.ogg *.flac *.mp4 *.webm *.mkv);;All files (*)')
        if path:self.load(path)
    def load(self,path):
        if hasattr(self,'player'):self.player.setSource(QUrl.fromLocalFile(str(path)));self.player.play()
    def can_close(self):
        if hasattr(self,'player'):self.player.stop()
        return True
