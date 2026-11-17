#!/usr/bin/python3
"""Read-only GUI smoke test in an extracted ISO filesystem; never starts jobs."""
import json,os,shutil,subprocess,sys,tempfile
from pathlib import Path

def inside():
 import importlib.util,time
 from PySide6.QtCore import QUrl
 from PySide6.QtWidgets import QApplication
 from PySide6.QtQuickWidgets import QQuickWidget
 spec=importlib.util.spec_from_file_location('launcher','/usr/local/libexec/macaque-wayland-installer')
 # Installed helper has no .py suffix.
 from importlib.machinery import SourceFileLoader
 launcher=SourceFileLoader('launcher','/usr/local/libexec/macaque-wayland-installer').load_module()
 env=launcher.client_environment(Path(os.environ['XDG_RUNTIME_DIR'])/os.environ['WAYLAND_DISPLAY'],os.environ['XDG_RUNTIME_DIR'])
 os.environ.update(env)
 app=QApplication([])
 with open('/tmp/macaque-graphics/calamares.log','w') as log:
  process=subprocess.Popen(launcher.installer_command(),env=env,stdout=log,stderr=subprocess.STDOUT)
  try:
   for _ in range(150):
    if process.poll() is not None:raise RuntimeError('Calamares exited during Wayland startup: '+str(process.returncode))
    app.processEvents();time.sleep(.1)
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
 widget=QQuickWidget();widget.engine().addImportPath('/usr/share/calamares/qml')
 widget.setResizeMode(QQuickWidget.SizeRootObjectToView);widget.resize(800,500)
 widget.setSource(QUrl.fromLocalFile('/etc/calamares/branding/macaque/show.qml'))
 widget.show()
 for _ in range(50):app.processEvents();time.sleep(.1)
 if widget.status()!=QQuickWidget.Ready:raise RuntimeError(str([x.toString() for x in widget.errors()]))
 if widget.grabFramebuffer().isNull():raise RuntimeError('Slideshow did not render')
 widget.grabFramebuffer().save('/tmp/macaque-graphics/slideshow.png')
 Path('/tmp/macaque-graphics/passed.json').write_text(json.dumps({'wayland_installer_startup':True,'software_slideshow_rendered':True,'full_install_tested':False}))

def outside(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 folder=root/'tmp/macaque-graphics';folder.mkdir(mode=0o700,exist_ok=True)
 runtime=folder/'runtime';runtime.mkdir(mode=0o700,exist_ok=True)
 config=folder/'config';config.mkdir(exist_ok=True)
 shutil.copyfile(root/'etc/xdg/macaque/labwc/rc.xml',config/'rc.xml')
 shutil.copyfile(__file__,folder/'test.py')
 env=dict(os.environ,XDG_RUNTIME_DIR='/tmp/macaque-graphics/runtime',WLR_BACKENDS='headless',WLR_RENDERER='pixman',WLR_LIBINPUT_NO_DEVICES='1',WLR_XWAYLAND='/usr/bin/false',QT_QPA_PLATFORM='wayland')
 mounted=[]
 try:
  for name in ('dev','proc','sys'):
   subprocess.run(['mount','--rbind','/'+name,str(root/name)],check=True);mounted.append(root/name)
   subprocess.run(['mount','--make-rslave',str(root/name)],check=True)
  with (folder/'compositor.log').open('w') as log:
   process=subprocess.Popen(['chroot',str(root),'/usr/bin/labwc','-C','/tmp/macaque-graphics/config','-S','/usr/bin/python3 /tmp/macaque-graphics/test.py --inside'],env=env,stdout=log,stderr=subprocess.STDOUT)
   import time
   try:
    deadline=time.monotonic()+60
    while time.monotonic()<deadline and not (folder/'passed.json').exists():
     if process.poll() is not None:raise RuntimeError('Headless compositor exited')
     time.sleep(.2)
    if not (folder/'passed.json').exists():raise RuntimeError('Installer graphical smoke test timed out')
   finally:
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
 finally:
  for p in folder.glob('*'):
   if p.is_file():shutil.copyfile(p,out/('installer-graphics-'+p.name))
  for p in reversed(mounted):subprocess.run(['umount','-R',str(p)],check=True)
  shutil.rmtree(folder)
 print('PASS: native Wayland Calamares remained running; branded Qt Quick slideshow rendered with software. No installation jobs started.')
if __name__=='__main__':
 if sys.argv[1:]==['--inside']:inside()
 else:outside(*sys.argv[1:])
