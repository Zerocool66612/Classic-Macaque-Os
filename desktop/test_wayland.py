"""Native client environment, idle policy and user-only shortcut IPC checks."""
import os,tempfile,time,json,socket,errno
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtNetwork import QLocalSocket
from wayland_session import native_environment
from creative_apps import child_environment
from app_support import flatpak_command
from wayland_power import idle_command,preferences,save
from power_backend import action
from session_control import serve,socket_path,decode_action
app=QApplication([])
base={'MACAQUE_WAYLAND_SESSION':'1','WAYLAND_DISPLAY':'wayland-9','XDG_RUNTIME_DIR':'/run/user/1000','DISPLAY':':0','XAUTHORITY':'host','QT_PLUGIN_PATH':'host','LD_LIBRARY_PATH':'host','DBUS_SESSION_BUS_ADDRESS':'user-bus'}
env=native_environment(base)
assert all(k not in env for k in ('DISPLAY','XAUTHORITY','QT_PLUGIN_PATH','LD_LIBRARY_PATH'))
assert env['QT_QPA_PLATFORM']=='wayland' and env['GDK_BACKEND']=='wayland' and env['DBUS_SESSION_BUS_ADDRESS']=='user-bus'
assert child_environment(base,'/private')['XDG_CONFIG_HOME']=='/private'
args=flatpak_command('org.gimp.GIMP','/volume',env)
assert '--socket=wayland' in args and '--nosocket=x11' in args and '--nosocket=fallback-x11' in args
try:native_environment({})
except RuntimeError:pass
else:raise AssertionError('Missing compositor socket accepted')
with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'XDG_CONFIG_HOME':temp,'MACAQUE_WAYLAND_SESSION':'1','MACAQUE_NATIVE_SESSION':'1'}):
 values=preferences();values.update(blank_ac=0,dim_ac=9,blank_battery=2,dim_battery=30)
 save(values);assert preferences()==values
 ac=idle_command(values,False);bat=idle_command(values,True)
 assert 'timeout' not in ac and 'before-sleep' in ac
 assert '120' in bat and '30' in bat and any('macaque-lock && wlopm' in x for x in bat)
 assert action({'action':'status'})['lid_managed'] is False
 with patch('power_backend.subprocess.run',side_effect=AssertionError('No X11 power commands allowed')):action({'action':'apply','values':values})
 try:save(dict(values,blank_ac=-1))
 except ValueError:pass
 else:raise AssertionError('Invalid idle delay accepted')
with patch.dict(os.environ,{'MACAQUE_PREVIEW_SESSION':'1'}):
 try:action({'action':'brightness'})
 except ValueError:pass
 else:raise AssertionError('Nested preview allowed host power changes')
assert decode_action(b'terminal\n')=='terminal'
for payload in (b'/bin/sh\n',b'files',b'X'*65+b'\n'):
 try:decode_action(payload)
 except ValueError:pass
 else:raise AssertionError('Invalid desktop request accepted')
# A blocked transport must be reported as untested, never as an IPC pass.
try:
 probe=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);probe.close()
except PermissionError:
 print('SKIP live shortcut socket: runtime denies AF_UNIX socket creation.')
else:
 with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'XDG_RUNTIME_DIR':temp,'WAYLAND_DISPLAY':'wayland-test'}):
  class Desktop(QWidget):
   def __init__(self):super().__init__();self.actions=[]
   def launch_terminal(self):self.actions.append('terminal')
   def launch(self,name):self.actions.append(name)
  d=Desktop();server=serve(d);assert server is not None and server.isListening(),server.errorString() if server else 'no server'
  assert Path(socket_path()).stat().st_mode&0o077==0
  def send(message):
   client=QLocalSocket();client.connectToServer(socket_path());assert client.waitForConnected(1000);client.write(message);client.flush();deadline=time.monotonic()+3;reply=b''
   while time.monotonic()<deadline:
    app.processEvents();reply+=bytes(client.readAll())
    if reply:break
    time.sleep(.005)
   app.processEvents();return reply
  assert send(b'terminal\n')==b'ok\n' and d.actions==['terminal']
  assert send(b'/bin/sh\n')==b'error\n' and d.actions==['terminal']
  assert send(b'updates\n')==b'ok\n' and d.actions[-1]=='Software Update'
  server.close()
print('Wayland client/Flatpak environment, idle policy, validation and shortcut protocol checks passed. Hardware login/lock/suspend not exercised.')
