"""Hardware mutations are mocked; only temporary files are written."""
import json,os,sys,tempfile,types,unittest,zipfile
from pathlib import Path
from unittest.mock import patch,Mock
import input_settings as inputs,display_settings as displays,reliability_backend as hardware,diagnostics_backend as diagnostics
FIXTURE='''eDP-1 "Laptop panel"
  Enabled: yes
  Modes:
    1920x1080 px, 60.000000 Hz (preferred, current)
    1280x720 px, 60.000000 Hz
  Position: 0,0
  Transform: normal
  Scale: 1.000000
HDMI-A-1 "External monitor"
  Enabled: no
  Modes:
    2560x1440 px, 59.950001 Hz (preferred)
'''
VALUE={'name':'eDP-1','mode':'1280x720@60.000000Hz','scale':1.25,'x':0,'y':0,'transform':'normal'}
class Checks(unittest.TestCase):
 def test_touchpad_config_preserves_keys_and_rejects_bad_values(self):
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'XDG_CONFIG_HOME':temp}):
   source=Path(__file__).with_name('labwc-rc.xml');inputs.atomic(inputs.folder()/'touchpad.json',json.dumps(dict(inputs.DEFAULT,tap=False,pointerSpeed=.3)));dest=inputs.render(source)
   import xml.etree.ElementTree as ET
   root=ET.parse(dest/'rc.xml');self.assertEqual(root.find('.//libinput/device/tap').text,'no');self.assertEqual(root.find('.//libinput/device/pointerSpeed').text,'0.3');self.assertTrue(root.findall('.//keybind'))
   for bad in ({'tap':'yes'},{'pointerSpeed':2},[],{'pointerSpeed':float('nan')}):
    with self.assertRaises(ValueError):inputs.validate(bad)
   inputs.atomic(inputs.folder()/'touchpad.json','[]');self.assertEqual(inputs.values(),inputs.DEFAULT)
 def test_display_preview_keep_and_independent_rollback(self):
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':temp,'XDG_CONFIG_HOME':temp}),patch.object(displays,'status',return_value=displays.outputs(FIXTURE)),patch.object(displays,'run',return_value='') as run,patch.object(displays.subprocess,'Popen') as spawn:
   preview=displays.preview(VALUE);self.assertTrue(displays.load()['pending']);spawn.assert_called_once();self.assertIn('--dryrun',run.call_args_list[0].args[0]);self.assertNotIn('--dryrun',run.call_args_list[1].args[0])
   with self.assertRaises(ValueError):displays.preview(VALUE)
   displays.finish(preview['token'],True);self.assertFalse(displays.load()['pending']);self.assertTrue((inputs.folder()/'displays.json').is_file())
   preview=displays.preview(VALUE)
   with patch.object(displays.time,'sleep'):displays.guard(preview['token'])
   self.assertIn('1920x1080@60.000000Hz',run.call_args.args[0]);self.assertFalse(displays.load()['pending'])
   with self.assertRaises(ValueError):displays.finish(preview['token'],True)
 def test_bad_display_command_and_apply_failure_leaves_guard_armed(self):
  available=displays.outputs(FIXTURE)
  for bad in (dict(VALUE,name='other'),dict(VALUE,mode='garbage'),dict(VALUE,scale=9),dict(VALUE,x=True)):
   with self.assertRaises(ValueError):displays.command(bad,available)
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':temp}),patch.object(displays,'status',return_value=available),patch.object(displays,'run',side_effect=['',RuntimeError('apply failed')]),patch.object(displays.subprocess,'Popen'):
   with self.assertRaises(RuntimeError):displays.preview(VALUE)
   self.assertTrue(displays.load()['pending'])
 def test_native_guard_and_supported_profiles(self):
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'1'}),patch.object(hardware,'run') as run:
   for op in ('profile-set','touchpad-apply','bluetooth-connect','audio-output','audio-test','display-preview'):
    with self.assertRaises(ValueError):hardware.action({'action':op})
   run.assert_not_called()
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch.object(hardware,'run',side_effect=['* balanced:\n power-saver:\n','balanced\n']) as run:
   with self.assertRaises(ValueError):hardware.action({'action':'profile-set','profile':'performance'})
   self.assertEqual(run.call_count,2)
 def test_audio_device_validation_and_microphone_level(self):
  state={'outputs':[{'name':'speakers'}],'inputs':[{'name':'microphone'}]}
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch.object(hardware,'audio_status',return_value=state),patch.object(hardware,'run',return_value='') as run:
   hardware.action({'action':'audio-input-volume','name':'microphone','percent':35});run.assert_called_once_with(['pactl','set-source-volume','microphone','35%'])
   for bad in ({'action':'audio-output','name':'invented'},{'action':'audio-input-volume','name':'microphone','percent':101}):
    with self.assertRaises(ValueError):hardware.action(bad)
 def test_bluetooth_adapter_and_pairing_boundary(self):
  objects={'/org/bluez/hci0':{'org.bluez.Adapter1':{'Powered':True}},'/org/bluez/hci0/dev_1':{'org.bluez.Device1':{'Name':'Fixture headset','Paired':False}}};api=Mock();manager=Mock();manager.GetManagedObjects.return_value=objects
  module=types.SimpleNamespace(SystemBus=lambda:Mock(get_object=lambda *a:Mock()),Interface=lambda obj,iface:manager if iface=='org.freedesktop.DBus.ObjectManager' else api,ObjectPath=str,Boolean=bool)
  with patch.dict(sys.modules,{'dbus':module}):
   self.assertEqual(hardware.bluetooth({'action':'bluetooth-status'})['devices'][0]['name'],'Fixture headset')
   with self.assertRaisesRegex(ValueError,'Pair this device'):hardware.bluetooth({'action':'bluetooth-connect','device':'/org/bluez/hci0/dev_1'})
   api.Connect.assert_not_called()
 def test_diagnostics_local_bundle_redaction_and_no_overwrite(self):
  secret='password=private\npsk: hidden\n12:34:56:78:9a:bc 192.168.4.2'
  clean=diagnostics.redact(secret);self.assertNotIn('private',clean);self.assertNotIn('hidden',clean);self.assertNotIn('192.168.4.2',clean)
  with tempfile.TemporaryDirectory() as temp,patch.object(diagnostics,'collect',return_value={'summary.txt':'fixture','session.log':clean}):
   a=diagnostics.action({'action':'diagnostics-export','directory':temp});b=diagnostics.action({'action':'diagnostics-export','directory':temp});self.assertNotEqual(a['path'],b['path'])
   with zipfile.ZipFile(a['path']) as z:self.assertEqual(z.namelist(),['summary.txt','session.log']);self.assertNotIn(b'private',z.read('session.log'))
if __name__=='__main__':unittest.main()
