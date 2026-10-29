"""Original classic-inspired UI earcons. No sampled Apple audio."""
import math,wave,struct,time
from pathlib import Path
from PySide6.QtCore import QObject,QUrl,Qt
from PySide6.QtWidgets import *
SOUNDS={'startup':'Startup chime','open':'Open window','close':'Close window','save':'Save document','move':'Move or copy files','trash':'Move to Trash','empty':'Empty Trash','error':'Alert','notification':'Notification'}
# Frequency, duration, onset: gently filtered harmonics with attack/release.
SCORES={
 'startup':[(261.63,.72,0),(329.63,.72,.09),(392,.8,.18),(523.25,.85,.28)],
 'open':[(660,.055,0),(880,.09,.045)],
 'close':[(520,.06,0),(350,.085,.045)],
 'save':[(523.25,.09,0),(783.99,.15,.09)],
 'move':[(440,.055,0),(587.33,.08,.06)],
 'trash':[(190,.055,0),(145,.07,.06),(110,.09,.12)],
 'empty':[(310,.04,0),(235,.045,.05),(160,.06,.10),(95,.12,.16)],
 'error':[(370,.13,0),(311.13,.18,.16)],
 'notification':[(880,.10,0),(1174.66,.20,.10)]}
def samples(key,rate=22050):
    score=SCORES[key];length=int((max(start+dur for freq,dur,start in score)+.03)*rate);out=[]
    for i in range(length):
        t=i/rate;value=0
        for freq,dur,start in score:
            phase=t-start
            if 0<=phase<dur:
                envelope=min(1,phase/.007)*min(1,(dur-phase)/.045)*math.exp(-phase*2.4/dur)
                value+=envelope*(math.sin(2*math.pi*freq*phase)+.13*math.sin(4*math.pi*freq*phase))
        out.append(value)
    peak=max(abs(v) for v in out) or 1
    return [int(v/peak*16000) for v in out]
def generate(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    for key in SOUNDS:
        with wave.open(str(directory/(key+'.wav')),'wb') as wav:wav.setparams((1,2,22050,0,'NONE','not compressed'));data=samples(key);wav.writeframes(struct.pack('<'+'h'*len(data),*data))
class SoundTheme(QObject):
    def __init__(self,d,effect_factory=None):
        super().__init__(d);self.d=d;self.effects={};self.last=0;self.suspended=True;self.available=False;self.reason=''
        try:
            if effect_factory is None:
                from PySide6.QtMultimedia import QSoundEffect,QMediaDevices
                if QMediaDevices.defaultAudioOutput().isNull():raise OSError('No output device detected. Select a Linux audio output and restart Macaque.')
                effect_factory=QSoundEffect
            for key in SOUNDS:
                path=Path(__file__).parent/'sounds'/(key+'.wav')
                if not path.exists():raise OSError('Sound files are missing; extract the full ZIP.')
                effect=effect_factory(self);effect.setSource(QUrl.fromLocalFile(str(path)));self.effects[key]=effect
            self.available=True
        except (ImportError,OSError) as ex:self.reason=str(ex)
    def play(self,key,preview=False):
        if key not in self.effects or not self.available:return False
        if not preview:
            if self.suspended or not self.d.state.get('sounds_enabled',True) or self.d.state.get('do_not_disturb',False) or not self.d.state.get('sound_events',{}).get(key,True):return False
            now=time.monotonic()
            if now-self.last<.14:return False
            self.last=now
        # Keep feedback brief; multiple operations cannot stack a wall of audio.
        for effect in self.effects.values():effect.stop()
        effect=self.effects[key];effect.setVolume(max(0,min(1,self.d.state.get('sound_volume',30)/100)));effect.play();return True
    def stop(self):
        for effect in self.effects.values():effect.stop()

class SoundPreferences(QWidget):
    app_name='Classic Sounds'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);layout.addWidget(QLabel('Macaque Classic Sounds'));label=QLabel('Original synthesized chimes and clicks inspired by classic desktops.');label.setWordWrap(True);layout.addWidget(label);enabled=QCheckBox('Enable desktop sounds');enabled.setChecked(d.state.get('sounds_enabled',True));enabled.toggled.connect(lambda v:(d.set_preference('sounds_enabled',v),d.sound_theme.stop() if not v else None));layout.addWidget(enabled)
        row=QHBoxLayout();layout.addLayout(row);row.addWidget(QLabel('Effects volume'));volume=QSlider(Qt.Horizontal);volume.setRange(0,100);volume.setValue(d.state.get('sound_volume',30));row.addWidget(volume);self.level=QLabel(str(volume.value())+'%');row.addWidget(self.level);volume.valueChanged.connect(lambda v:(d.set_preference('sound_volume',v),self.level.setText(str(v)+'%')))
        grid=QGridLayout();layout.addLayout(grid)
        for i,(key,title) in enumerate(SOUNDS.items()):
            check=QCheckBox(title);check.setChecked(d.state.get('sound_events',{}).get(key,True));check.toggled.connect(lambda v,k=key:self.toggle(k,v));grid.addWidget(check,i,0);test=QPushButton('Preview');test.clicked.connect(lambda checked=False,k=key:d.sound_theme.play(k,preview=True));grid.addWidget(test,i,1)
        info=QLabel('Do Not Disturb silences automatic desktop sounds. Preview plays the selected effect at the chosen volume. This slider changes Macaque effects only.');info.setWordWrap(True);layout.addWidget(info)
        status=QLabel('Qt audio backend loaded. If silent, check your Linux output device.' if d.sound_theme.available else 'Audio unavailable: '+d.sound_theme.reason);status.setWordWrap(True);layout.addWidget(status);layout.addStretch()
    def toggle(self,key,value):self.d.state.setdefault('sound_events',{})[key]=value;self.d.persist()
