#!/usr/bin/python3
"""Small user-only control socket for compositor shortcuts; no arbitrary commands."""
import hashlib,os,socket,sys
from pathlib import Path
ACTIONS=('terminal','power','updates','files','screenshot','screenshot-region','screenshot-full','volume-up','volume-down','mute','mic-mute','brightness-up','brightness-down')
def socket_path(env=None):
    env=os.environ if env is None else env
    runtime=env.get('XDG_RUNTIME_DIR','');display=env.get('WAYLAND_DISPLAY','')
    if not runtime or not display:raise ValueError('Wayland runtime/display is missing.')
    return str(Path(runtime)/('macaque-control-'+hashlib.sha256(display.encode()).hexdigest()[:12]+'.sock'))
def decode_action(data):
    if len(data)>64 or b'\n' not in data:raise ValueError('Invalid desktop request.')
    action=data.split(b'\n',1)[0].decode(errors='replace')
    if action not in ACTIONS:raise ValueError('Unknown desktop action.')
    return action

def request(action):
    if action not in ACTIONS:raise ValueError('Unknown desktop action.')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(2);client.connect(socket_path());client.sendall((action+'\n').encode())
        if client.recv(16)!=b'ok\n':raise RuntimeError('Desktop did not acknowledge the action.')
def serve(desktop):
    from PySide6.QtNetwork import QLocalServer
    from PySide6.QtCore import QTimer
    path=socket_path();server=QLocalServer(desktop);server.setSocketOptions(QLocalServer.UserAccessOption)
    # Do not unlink a live socket belonging to another instance.
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:client.settimeout(.2);client.connect(path)
    except OSError:QLocalServer.removeServer(path)
    else:return None
    if not server.listen(path):return None
    def connected():
        while server.hasPendingConnections():
            client=server.nextPendingConnection();buffer=bytearray()
            def read(c=client,b=buffer):
                b.extend(bytes(c.readAll()))
                if len(b)>64:c.disconnectFromServer();return
                if b'\n' not in b:return
                try:action=decode_action(bytes(b))
                except ValueError:c.write(b'error\n');c.disconnectFromServer();return
                b.clear()
                c.write(b'ok\n');c.flush();c.disconnectFromServer()
                def launch():
                    if action in ('volume-up','volume-down','mute','mic-mute','brightness-up','brightness-down'):desktop.hardware_keys.run(action)
                    elif action.startswith('screenshot'):
                        panel=desktop.launch('Screenshot').content
                        if action!='screenshot':
                            panel.mode.setCurrentText('Select region' if action.endswith('region') else 'Full screen');panel.capture()
                    elif action=='terminal':desktop.launch_terminal()
                    else:desktop.launch({'power':'Battery & Power','updates':'Software Update','files':'Macaque Files'}[action])
                QTimer.singleShot(0,desktop,launch)
            client.readyRead.connect(read);client.disconnected.connect(client.deleteLater);QTimer.singleShot(3000,client,client.disconnectFromServer)
    server.newConnection.connect(connected);return server
if __name__=='__main__':
    try:request(sys.argv[1] if len(sys.argv)==2 else '')
    except Exception as ex:
        if sys.argv[1:]==['terminal']:
            import subprocess
            sys.exit(subprocess.call(['foot','--title=Macaque Recovery Terminal']))
        print(ex,file=sys.stderr);sys.exit(1)
