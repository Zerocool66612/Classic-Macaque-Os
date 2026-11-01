import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from creative_apps import CREATIVE_APPS,CreativeApps,child_environment
import creative_session
class DesktopStub:
    def __init__(self,path):self.base=path;self.messages=[]
    def text_window(self,title,text):self.messages.append((title,text));return title
class Checks(unittest.TestCase):
    def test_no_host_launch_in_regular_mode(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'0'}),patch('creative_apps.subprocess.Popen') as start:
            d=DesktopStub(Path(t));apps=CreativeApps(d)
            for name in CREATIVE_APPS:apps.launch(name)
            self.assertEqual(len(d.messages),3);start.assert_not_called()
    def test_nested_environment(self):
        env=child_environment({'DISPLAY':':123','XAUTHORITY':'private','WAYLAND_DISPLAY':'wayland-0','QT_PLUGIN_PATH':'host','LD_LIBRARY_PATH':'qt','DBUS_SESSION_BUS_ADDRESS':'private-bus'},'/config')
        self.assertEqual(env['DISPLAY'],':123');self.assertEqual(env['XAUTHORITY'],'private');self.assertEqual(env['DBUS_SESSION_BUS_ADDRESS'],'private-bus')
        self.assertEqual(env['QT_QPA_PLATFORM'],'xcb');self.assertNotIn('WAYLAND_DISPLAY',env);self.assertNotIn('QT_PLUGIN_PATH',env)
    def test_allowlisted_launches_and_no_duplicate(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{'MACAQUE_NATIVE_SESSION':'1','DISPLAY':':123','XAUTHORITY':'private'}),patch('creative_apps.shutil.which',side_effect=lambda n:'/usr/bin/'+n),patch('creative_apps.subprocess.run',return_value=Mock(returncode=1)),patch('creative_apps.subprocess.Popen') as start:
            start.side_effect=lambda *a,**kw:Mock(poll=lambda:None)
            d=DesktopStub(Path(t));apps=CreativeApps(d)
            for name in CREATIVE_APPS:apps.launch(name)
            self.assertEqual(start.call_count,3)
            for call in start.call_args_list:self.assertEqual(call.kwargs['env']['DISPLAY'],':123')
            self.assertIn('--new-instance',start.call_args_list[0].args[0]);self.assertIn('--multi',start.call_args_list[2].args[0])
            apps.launch('GIMP');self.assertEqual(start.call_count,3)
            for log in apps.logs:log.close()
    def test_missing_dependencies_fail_before_launch(self):
        with patch('creative_session.shutil.which',return_value=None),patch('creative_session.subprocess.Popen') as start:
            with self.assertRaisesRegex(RuntimeError,'Missing:'):creative_session.main()
            start.assert_not_called()
    def test_wm_config_is_valid_xml(self):
        import xml.etree.ElementTree as ET
        root=ET.fromstring(creative_session.CONFIG);self.assertTrue(root.tag=='labwc_config')
        self.assertIn('ToggleAlwaysOnBottom',creative_session.CONFIG)
app=QApplication([])
unittest.main()
