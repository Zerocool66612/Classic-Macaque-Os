"""Hardware boundaries are mocked: no real mixer/backlight is changed."""
import os,types,json,unittest
from unittest.mock import patch
import laptop_keys_backend as b
class Checks(unittest.TestCase):
 def test_volume_limit_and_mute(self):
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch.object(b.shutil,'which',return_value='/bin/wpctl'),patch.object(b,'call',return_value='Volume: 0.65 [MUTED]') as run:
   result=b.action({'action':'volume-up'});self.assertEqual(result,{'kind':'Volume','percent':65,'muted':True});self.assertEqual(run.call_args_list[0].args[0],['wpctl','set-volume','--limit','1.0','@DEFAULT_AUDIO_SINK@','5%+'])
   run.reset_mock();b.action({'action':'mic-mute'});self.assertEqual(run.call_args_list[0].args[0],['wpctl','set-mute','@DEFAULT_AUDIO_SOURCE@','toggle'])
 def test_preview_and_invalid_volume(self):
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'1'}),patch.object(b,'call') as run:
   with self.assertRaises(ValueError):b.action({'action':'mute'})
   run.assert_not_called()
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch.object(b.shutil,'which',return_value='/bin/wpctl'),patch.object(b,'call') as run:
   for value in (-1,101,True,'50'):
    with self.assertRaises(ValueError):b.action({'action':'volume','percent':value})
   run.assert_not_called()
 def test_brightness_clamps_and_missing_device(self):
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch.object(b,'backlights',return_value=[{'name':'fixture','percent':5}]),patch.object(b,'power') as power:
   self.assertEqual(b.action({'action':'brightness-down'})['percent'],5);power.assert_called_once_with({'action':'brightness','device':'fixture','percent':5})
  with patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch.object(b,'backlights',return_value=[]):
   with self.assertRaisesRegex(ValueError,'No laptop backlight'):b.action({'action':'brightness-up'})
 def test_global_bindings(self):
  from pathlib import Path
  import xml.etree.ElementTree as ET
  from session_control import decode_action
  rc=ET.parse(Path(__file__).with_name('labwc-rc.xml'));bindings={x.attrib['key']:x.find('action').attrib.get('command','') for x in rc.findall('.//keybind')}
  for key,op in [('XF86AudioRaiseVolume','volume-up'),('XF86AudioMute','mute'),('XF86AudioMicMute','mic-mute'),('XF86MonBrightnessDown','brightness-down'),('Print','screenshot'),('S-Print','screenshot-region')]:
   self.assertTrue(bindings[key].endswith(' '+op));self.assertEqual(decode_action((op+'\n').encode()),op)
  self.assertFalse(any(key in bindings for key in ('F1','F2','F3','F5','F6')))
if __name__=='__main__':unittest.main()
