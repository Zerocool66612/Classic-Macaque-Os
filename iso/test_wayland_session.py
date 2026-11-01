"""Exercise the real session launcher with a fake compositor, never a host DM."""
import os,json,tempfile,subprocess,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);binary=root/'labwc';capture=root/'capture.json'
 binary.write_text('#!/usr/bin/python3\nimport os,sys,json\nopen(os.environ["CAPTURE"],"w").write(json.dumps({"args":sys.argv[1:],"env":dict(os.environ)}))\n');binary.chmod(0o755)
 env=dict(os.environ,HOME=temp,PATH=temp+':/usr/bin:/bin',CAPTURE=str(capture),DBUS_SESSION_BUS_ADDRESS='fixture-bus',DISPLAY=':77',XAUTHORITY='host',WAYLAND_DISPLAY='host-wayland',QT_PLUGIN_PATH='host')
 subprocess.run(['/bin/sh',str(ROOT/'iso/macaque-session')],env=env,check=True)
 result=json.loads(capture.read_text());e=result['env'];args=result['args']
 assert e['QT_QPA_PLATFORM']=='wayland' and e['WLR_XWAYLAND']=='/usr/bin/false'
 assert e['XDG_SESSION_TYPE']=='wayland' and e['MACAQUE_WAYLAND_SESSION']=='1'
 assert not any(k in e for k in ('DISPLAY','XAUTHORITY','WAYLAND_DISPLAY','QT_PLUGIN_PATH'))
 assert '-S' in args and 'wayland_session.py' in args[-1]
 assert args[:2]==['-C','/etc/xdg/macaque/labwc']
# Root installer validates the source runtime and socket before running anything.
spec=importlib.util.spec_from_file_location('installer',ROOT/'iso/wayland/installer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for name in ('','../wayland-0','/tmp/wayland-0','.'):
 try:m.socket_for(1000,name)
 except ValueError:pass
 else:raise AssertionError('Invalid installer socket accepted')
print('Actual session shell environment/compositor argv and installer socket traversal checks passed (fake compositor).')
