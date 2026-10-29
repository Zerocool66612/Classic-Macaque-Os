import os,tempfile,json
from unittest.mock import patch,Mock
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
config=tempfile.TemporaryDirectory();os.environ['XDG_CONFIG_HOME']=config.name
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QPoint,QSettings
from PySide6.QtTest import QTest
from desktop import Desktop
from install_preparation import InstallPreparation
app=QApplication([]);settings=QSettings('MacaqueOS','ClassicControlStripDesktop');settings.setValue('embeddingInitialized',True)
for i in range(13):settings.setValue(f'module{i}Visible',i==12)
settings.sync()
with tempfile.TemporaryDirectory() as data:
 d=Desktop(data);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True);d.show();QTest.qWait(30)
 assert d.native_strip is not None,getattr(d,'strip_error','')
 with patch.object(d,'launch_terminal') as terminal:
  QTest.mouseClick(d.strip,Qt.LeftButton,pos=QPoint(35,15));QTest.qWait(220);assert terminal.call_count==1
  d.launch('Terminal');assert terminal.call_count==2
 assert any(b.property('iconKey')=='Terminal' for b in d.icons)
 from terminal_app import Terminal
 with patch('terminal_app.subprocess.Popen',side_effect=OSError('test: no shell launched')):
  frame=d.launch_terminal();assert isinstance(frame.content,Terminal) and frame.bar is not None;frame.content.cleanup();frame.hide()
 with patch.object(InstallPreparation,'refresh'):
  ui=InstallPreparation(d)
  ui.kind='list';ui.buffer=json.dumps({'disks':[{'name':'/dev/sdb','type':'disk','maj:min':'8:16','size':128*2**30,'model':'Test SSD'}],'swaps':[],'live_source':'/dev/sda1'});ui.finished(0,None);assert ui.disks.count()==1
  with patch.object(ui,'run') as run,patch('install_preparation.QMessageBox.question',return_value=QMessageBox.No):ui.release_swap();run.assert_not_called()
  with patch.object(ui,'run') as run,patch('install_preparation.QMessageBox.question',return_value=QMessageBox.Yes):
   ui.release_swap();assert run.call_args.args[1]=='/usr/bin/sudo';assert run.call_args.args[2][-4:]==['--disk','/dev/sdb','--expected-id','8:16']
  ui.busy=True;assert not ui.can_close();ui.busy=False;assert ui.can_close()
 d.quitting=True;d.hide()
print('Real Control Strip Terminal button, terminal launch and swap UI checks passed; privileged calls mocked.')
