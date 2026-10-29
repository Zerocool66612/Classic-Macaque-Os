import os,tempfile,wave,struct
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication,QCheckBox
from desktop import Desktop
from sound_theme import SoundTheme,SOUNDS
class FakeEffect:
 def __init__(self,parent):self.played=0;self.volume=0
 def setSource(self,url):self.path=url.toLocalFile()
 def setVolume(self,v):self.volume=v
 def play(self):self.played+=1
 def stop(self):pass
app=QApplication([])
with tempfile.TemporaryDirectory() as t:
 d=Desktop(t);d.show();app.processEvents();engine=SoundTheme(d,FakeEffect);engine.suspended=False
 assert engine.play('save');assert engine.effects['save'].played==1 and engine.effects['save'].volume==.3
 assert not engine.play('open') # Rate limit prevents rapid overlapping events.
 d.state['sounds_enabled']=False;engine.last=0;assert not engine.play('open');assert engine.play('save',preview=True)
 d.state['sounds_enabled']=True;d.state['do_not_disturb']=True;engine.last=0;assert not engine.play('open')
 d.state['do_not_disturb']=False;d.state['sound_events']={'open':False};assert not engine.play('open')
 d.state['sound_volume']=250;assert engine.play('save',preview=True);assert engine.effects['save'].volume==1
 for key in SOUNDS:
  with wave.open(str(Path(__file__).parent/'sounds'/(key+'.wav')),'rb') as wav:
   assert wav.getnchannels()==1 and wav.getsampwidth()==2
   frames=wav.readframes(wav.getnframes());data=struct.unpack('<'+'h'*(len(frames)//2),frames);assert 0.05<len(data)/wav.getframerate()<2;assert 1000<max(abs(n) for n in data)<=16000;assert abs(data[0])<30 and abs(data[-1])<30
 # Actual application callbacks request the appropriate event sound.
 events=[];d.play_sound=events.append
 w=d.launch('Calculator');assert events[-1]=='open';w.close();assert events[-1]=='close'
 path=d.disk.root/'Documents'/'sound-test.txt';path.write_text('test');d.transfer_paths([path],d.disk.root/'Desktop');assert events[-1]=='move'
 d.trash_paths([d.disk.root/'Desktop'/'sound-test.txt']);assert events[-1]=='trash'
 d.operation(d.disk.empty_trash,'empty');assert events[-1]=='empty'
 text=d.launch('Macaque Text').content;text.path=d.disk.root/'Documents'/'saved.txt';text.editor.setPlainText('saved');assert text.save();assert events[-1]=='save'
 with patch('desktop.QMessageBox.warning'):d.error('test alert')
 assert events[-1]=='error'
 d.notify('Test','Notification');assert events[-1]=='notification'
 w=d.launch('Classic Sounds');checks={c.text():c for c in w.content.findChildren(QCheckBox)};checks['Enable desktop sounds'].setChecked(False);assert not d.state['sounds_enabled'];w.close();d.quitting=True;d.close()
print('PASS: nine bundled WAV effects, valid envelopes/levels; volume/mute/DND/per-event settings; audio rate limiting; real window/save/file/trash/error/notification callbacks; sound controls')
