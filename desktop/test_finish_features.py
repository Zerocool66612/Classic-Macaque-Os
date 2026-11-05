import os,tempfile,json,zipfile,subprocess
from pathlib import Path
from unittest.mock import patch,Mock
os.environ['QT_QPA_PLATFORM']='offscreen'
import desktop_services as services
from backup import create_backup,recover_backup,validated_preferences
# Lock failure must never lead to suspend, and previews cannot mutate the host.
with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}):
 with patch.object(services,'run',side_effect=RuntimeError('lock failed')) as run:
  try:services.action({'action':'suspend'})
  except RuntimeError:pass
  assert run.call_count==1 and run.call_args.args[0]==['/usr/local/bin/macaque-lock']
 with patch.object(services,'run',return_value='') as run:
  services.action({'action':'suspend'});assert run.call_args_list[1].args[0]==['systemctl','suspend']
 with patch.object(services,'run',return_value='America/Denver\nUTC\n') as run:
  services.action({'action':'timezone','zone':'UTC'});assert run.call_args.args[0]==['timedatectl','set-timezone','UTC']
  try:services.action({'action':'timezone','zone':'--help'});raise AssertionError()
  except ValueError:pass
 with patch.object(services,'run',return_value='org.example.App\tExample\tDescription\tflathub\n') as run:
  rows=services.action({'action':'flatpak-search','query':'painting'})['rows'];assert rows and '--user' in run.call_args.args[0]
  for bad in ('--delete','org.app;echo','../../a'):
   try:services.action({'action':'flatpak-install','id':bad});raise AssertionError()
   except ValueError:pass
with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'1'}),patch.object(services,'run') as run:
 for op in ('suspend','flatpak-install','timezone'):
  try:services.action({'action':op});raise AssertionError()
  except ValueError:pass
 run.assert_not_called()
with tempfile.TemporaryDirectory() as t:
 t=Path(t);root=t/'Documents';root.mkdir();(root/'visible.txt').write_text('hello');(root/'.secret').write_text('omit');(root/'link').symlink_to(root/'.secret');archive=t/'backup.zip'
 create_backup(root,{},archive,True)
 with zipfile.ZipFile(archive) as z:assert not any('.secret' in n or n.endswith('/link') for n in z.namelist())
 dest=Path(recover_backup(archive,t/'Recovered'));assert (dest/'Macaque HD/visible.txt').read_text()=='hello'
 prefs=t/'preferences.json';prefs.write_text(json.dumps({'mode':'dark','text_size':20,'high_contrast':True,'startup_apps':['dangerous'],'classic_mac':{'binary':'unsafe'}}));values=validated_preferences(prefs);assert values=={'high_contrast':True,'mode':'dark','text_size':20}
 prefs.write_text('{"text_size": true}')
 try:validated_preferences(prefs);raise AssertionError()
 except ValueError:pass
from PySide6.QtWidgets import QApplication,QCheckBox,QPushButton
from PySide6.QtTest import QTest
from desktop import Desktop
app=QApplication([])
with tempfile.TemporaryDirectory() as t:
 d=Desktop(Path(t));d.show();QTest.qWait(50)
 for name in ('Setup Assistant','Accessibility','Software Center','Lock & Sleep'):
  a=d.launch(name);assert d.launch(name) is a
 panel=d.launch('Accessibility').content;panel.size.setValue(20);panel.contrast.setChecked(True);panel.motion.setChecked(True);panel.apply();assert d.state['reduce_motion'] and d.state['high_contrast'] and d.top_bar.height()>=27
 setup=d.launch('Setup Assistant').content;setup.advance();setup.advance();setup.advance();assert d.state['setup_completed']
 software=d.launch('Software Center').content
 with patch.object(software,'confirm',return_value=False),patch.object(software,'request') as request:software.update();software.enable();request.assert_not_called()
 d.quitting=True;d.close()
print('Lock-before-suspend, preview guard, validated timezone/Flatpak argv, backup round-trip/exclusions, safe preference whitelist, four singleton panels, accessibility, setup completion and cancelled software actions passed.')
