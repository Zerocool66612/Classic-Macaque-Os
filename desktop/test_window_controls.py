import os,tempfile
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from desktop import Desktop
from window_controls import classic_controls
app=QApplication([])
from pathlib import Path
from PySide6.QtGui import QImage
import runpy,shutil,subprocess,sys

def check_native_assets(root):
 for name in ['close','iconify','max','max_toggled']:
  image=QImage(str(root/'usr/share/themes/Macaque Platinum/openbox-3'/(name+'.xbm')))
  assert not image.isNull() and image.width()==16 and image.height()==16,name
  image=QImage(str(root/'usr/share/themes/Macaque Traffic/openbox-3'/(name+'.svg')))
  assert not image.isNull() and image.width()==16 and image.height()==16,name

stager=Path(__file__).resolve().parent.parent/'iso/stage-wayland.py'
if stager.is_file():
 with tempfile.TemporaryDirectory() as staged:
  root=Path(staged);runpy.run_path(str(stager))['stage'](root);check_native_assets(root)
  # Also execute in the installed layout, which has no source-only iso/ helpers.
  installed=root/'opt/macaque-classic'
  shutil.copytree(Path(__file__).parent,installed,ignore=shutil.ignore_patterns('__pycache__','.venv','*.so','*.pyc'))
  env=dict(os.environ,MACAQUE_TEST_STAGED_ROOT=str(root))
  subprocess.run([sys.executable,str(installed/'test_window_controls.py')],env=env,check=True,timeout=45)
else:
 check_native_assets(Path(os.environ.get('MACAQUE_TEST_STAGED_ROOT','/')))
with tempfile.TemporaryDirectory() as path:
 d=Desktop(path);d.state.update(startup_files=False,startup_notes=False,reduce_motion=True);d.show();QTest.qWait(30)
 w=d.text_window('Window controls fixture','Test controls');QTest.qWait(30)
 buttons=w.bar.control_buttons
 from decoration_settings import controls
 for font in ['Classic','Standard']:
  d.state['interface_font']=font
  for mode in ['light','dark']:
   d.set_mode(mode)
   for style in ['Classic','Traffic lights']:
    d.set_preference('window_buttons',style)
    for side in ['Left','Right']:
     d.set_preference('window_button_side',side);QTest.qWait(10)
     assert classic_controls(d.state)==(style=='Classic')
     xs=[b.x() for b in [*buttons.values(),w.bar.shade_button]]
     assert (max(xs)<w.bar.label.x()) if side=='Left' else (min(xs)>w.bar.label.x()+w.bar.label.width())
     assert not buttons['Close'].grab().isNull()
 assert controls({'interface_font':'Standard','mode':'dark','window_buttons':'Match theme'})['window_buttons']=='Classic'
 d.set_preference('window_buttons','Classic');d.set_preference('window_button_side','Left');QTest.qWait(20)
 QTest.mouseClick(buttons['Zoom'],Qt.LeftButton);QTest.qWait(20);assert w.isMaximized()
 QTest.mouseClick(buttons['Zoom'],Qt.LeftButton);QTest.qWait(20);assert not w.isMaximized()
 QTest.mouseClick(buttons['Minimize'],Qt.LeftButton);QTest.qWait(20);assert w.isMinimized()
 w.showNormal();QTest.qWait(20);QTest.mouseClick(buttons['Close'],Qt.LeftButton);QTest.qWait(30)
 assert w not in d.area.subWindowList()
 d.quitting=True;d.close()
print('PASS: independent style/side in both colors and fonts, live switching, close/minimize/zoom, and native assets.')

# Native compositor preferences persist without font or color coupling.
import json,os,xml.etree.ElementTree as ET
from unittest.mock import patch
import input_settings,decoration_settings
with tempfile.TemporaryDirectory() as config,patch.dict(os.environ,{'XDG_CONFIG_HOME':config}):
 source=Path(__file__).resolve().parent/'labwc-rc.xml'
 for style in ['Classic','Traffic lights']:
  for side in ['Left','Right']:
   input_settings.atomic(input_settings.folder()/'window-controls.json',json.dumps({'window_buttons':style,'window_button_side':side}))
   root=ET.parse(input_settings.render(source)/'rc.xml').getroot()
   assert root.findtext('theme/name')==('Macaque Platinum' if style=='Classic' else 'Macaque Traffic')
   assert root.findtext('theme/titlebar/layout')==('close,iconify,max,shade:menu' if side=='Left' else 'menu:iconify,max,shade,close')
print('PASS: persisted native compositor style and placement combinations.')

with tempfile.TemporaryDirectory() as config,patch.dict(os.environ,{'XDG_CONFIG_HOME':config,'MACAQUE_WAYLAND_SESSION':'1','MACAQUE_PREVIEW_SESSION':'0'}),patch('input_settings.render') as render,patch('decoration_settings.subprocess.run') as reload:
 decoration_settings.sync({'window_buttons':'Traffic lights','window_button_side':'Right'})
 decoration_settings.sync({'window_buttons':'Traffic lights','window_button_side':'Right','mode':'dark','interface_font':'Classic'})
 assert render.call_count==1 and reload.call_count==1
 decoration_settings.sync({'window_buttons':'Traffic lights','window_button_side':'Left'})
 assert render.call_count==2 and reload.call_args.args[0]==['labwc','--reconfigure']
print('PASS: native style/position reload independently; color/font changes leave them alone.')
