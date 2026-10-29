import os,tempfile,json
from pathlib import Path
from unittest.mock import patch,Mock
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication
from desktop import Desktop
from app_support import parse_flatpaks,flatpak_command,emulator_preferences,FlatpakApps,ClassicMacApps
app=QApplication([])
with tempfile.TemporaryDirectory() as temp:
 t=Path(temp);d=Desktop(t/'data');d.show();app.processEvents();d.error=lambda ex:(_ for _ in ()).throw(AssertionError(str(ex)))
 parsed=parse_flatpaks('org.gimp.GIMP\tGIMP\norg.foo.App\tMy App\n--bad\tBad\norg.foo.App\tMy App\nmalformed\n');assert len(parsed)==2 and dict(parsed)['org.gimp.GIMP']=='GIMP'
 env={'MACAQUE_NATIVE_SESSION':'1','DISPLAY':':125','XAUTHORITY':'private'};args=flatpak_command('org.gimp.GIMP',d.disk.root,env);assert '--socket=x11' in args and '--nosocket=wayland' in args and args[-1]=='org.gimp.GIMP';assert any(str(d.disk.root) in a for a in args);assert not any('XAUTHORITY=' in a for a in args)
 for invalid in ('--command=sh','org.foo.App; rm -rf x','org.foo.App\n'):
  try:flatpak_command(invalid,d.disk.root,env)
  except ValueError:pass
  else:raise AssertionError('Invalid Flatpak ID accepted')
 try:flatpak_command('org.foo.App',d.disk.root,{})
 except ValueError:pass
 else:raise AssertionError('Flatpak launch allowed on host display')
 rom=t/'User ROM';rom.write_bytes(b'ROM placeholder');disk=t/'Guest disk.img';disk.write_bytes(b'not a real boot disk');shared=t/'shared';shared.mkdir()
 for kind in ('BasiliskII','SheepShaver'):
  prefs=emulator_preferences(kind,rom,disk,shared,64);assert 'rom '+str(rom) in prefs and 'ramsize 67108864' in prefs and 'nogui true' in prefs
 try:emulator_preferences('Other',rom,disk,shared,64)
 except ValueError:pass
 else:raise AssertionError('Unknown emulator accepted')
 try:emulator_preferences('BasiliskII',rom,t/'missing',shared,64)
 except ValueError:pass
 else:raise AssertionError('Missing disk accepted')
 manager=d.app_support;manager.installed={'org.gimp.GIMP':'GIMP'}
 with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'0'}),patch('app_support.subprocess.Popen') as launch:
  manager.launch_flatpak('org.gimp.GIMP');manager.launch_classic({});launch.assert_not_called()
 with patch.dict(os.environ,env),patch('app_support.subprocess.run',return_value=Mock(returncode=0,stdout='',stderr='')),patch.object(manager,'spawn') as spawn:
  manager.launch_flatpak('org.gimp.GIMP');assert spawn.call_args.args[1][0:2]==['flatpak','run'];assert spawn.call_args.args[2]['DISPLAY']==':125'
  executable=t/'BasiliskII';executable.write_text('#!/bin/sh\nexit 0\n');executable.chmod(0o755)
  config={'kind':'BasiliskII','binary':str(executable),'rom':str(rom),'disk':str(disk),'ram':64};manager.launch_classic(config);assert spawn.call_args.args[1][1]=='--config';assert Path(spawn.call_args.args[1][2]).is_file();assert spawn.call_args.args[2]['DISPLAY']==':125'
 with patch.dict(os.environ,env),patch('app_support.subprocess.run',return_value=Mock(returncode=0,stdout='org.gimp.GIMP\n',stderr='')),patch.object(manager,'spawn') as spawn:
  manager.launch_flatpak('org.gimp.GIMP');spawn.assert_not_called()
 with patch('app_support.shutil.which',return_value=None):
  w=d.launch('Flatpak Apps');assert isinstance(w.content,FlatpakApps);assert 'not installed' in w.content.status.text();w.close()
 w=d.launch('Classic Mac Apps');assert isinstance(w.content,ClassicMacApps);w.content.fields['rom'].setText(str(rom));w.content.fields['disk'].setText(str(disk));w.content.save();assert d.state['classic_mac']['rom']==str(rom);w.close()
 d.quitting=True;d.close()
print('PASS: Flatpak parsing, strict IDs, session gating, X11 permissions, nested environment and existing-instance refusal; emulator prefs/files/arguments; setup UI persistence and missing-dependency state. Emulator boot and real Flatpak launch NOT tested.')
