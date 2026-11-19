"""Installer logging tested with harmless subprocesses and a temporary folder."""
import importlib.util,tempfile,sys,os,json,yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('monitor',ROOT/'iso/wayland/installer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as temp:
 folder=Path(temp)/'logs';code=m.monitor([sys.executable,'-c','import sys; print("fixture installer error"); sys.exit(7)'],dict(os.environ),os.getuid(),folder)
 data=json.loads((folder/'last.json').read_text());assert code==7 and not data['running'] and data['returncode']==7
 assert 'fixture installer error' in Path(data['log']).read_text();assert Path(data['log']).stat().st_mode&0o777==0o600
 m.monitor([sys.executable,'-c','print("cancel fixture")'],dict(os.environ),os.getuid(),folder)
 data=json.loads((folder/'last.json').read_text());assert 'cancellation' in data['message'] and 'successfully installed' not in data['message']
print('Installer stdout/stderr preservation, private log permissions, error status and honest cancellation status passed (no installer/disk operations).')

env=m.client_environment('/run/user/1000/wayland-0','/run/private-root')
assert env['QT_QPA_PLATFORM']=='wayland' and env['QT_QUICK_BACKEND']=='software'
assert env['QT_OPENGL']=='software' and env['WAYLAND_DISPLAY']=='/run/user/1000/wayland-0'
assert not any(k in env for k in ['DISPLAY','XAUTHORITY','QT_PLUGIN_PATH','LD_LIBRARY_PATH'])
assert m.installer_command()==['/usr/bin/calamares','-platform','wayland','-D','8']
print('Native Wayland environment, software slideshow and verbose logging checks passed.')

# Avoid animated Qt Quick transitions during the critical partition/unpack phase.
assert 'Timer {' not in (ROOT/'iso/branding/show.qml').read_text()
print('PASS: installer slideshow has no timed transitions during installation.')
