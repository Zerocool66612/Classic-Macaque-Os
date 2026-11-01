#!/usr/bin/python3
"""Explicit interactive maintenance; never downloads or executes raw source."""
import hashlib,os,re,subprocess,sys,tempfile,shutil
from pathlib import Path
PACKAGE='macaque-classic'
def installed_target(root='/'):
    root=Path(root)
    return not (root/'etc/macaque-live').exists() and ((root/'etc/macaque-installed').is_file() or ((root/'opt/macaque-classic/desktop.py').is_file() and ((root/'usr/share/xsessions/macaque.desktop').is_file() or (root/'usr/share/wayland-sessions/macaque.desktop').is_file())))
def metadata(path):
    out=subprocess.check_output(['/usr/bin/dpkg-deb','--show','--showformat=${Package}\n${Version}\n${Architecture}\n',str(path)],text=True,timeout=20).splitlines()
    if len(out)!=3 or out[0]!=PACKAGE or out[2] not in ('amd64','all') or not re.fullmatch(r'[0-9][A-Za-z0-9.+:~\-]*',out[1]):raise ValueError('Choose an amd64 Macaque Classic desktop package.')
    return {'package':out[0],'version':out[1],'architecture':out[2]}
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def main(args):
    if not args:raise ValueError('Select a maintenance action.')
    if os.geteuid()!=0:raise ValueError('Maintenance requires administrator authentication through sudo.')
    if Path('/etc/macaque-live').exists():raise ValueError('System/desktop installation is disabled on the live USB. Install Macaque on a disk first.')
    if not installed_target():raise ValueError('Maintenance requires an installed Macaque system; it is disabled in the standalone prototype.')
    if args==['system-update']:
        subprocess.run(['/usr/bin/apt-get','update'],check=True)
        # APT asks before applying the package changes; signatures remain enabled.
        subprocess.run(['/usr/bin/apt-get','upgrade'],check=True);return
    if len(args)==3 and args[0]=='install-desktop':
        source=Path(args[1]);expected=args[2]
        if not source.is_absolute() or not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Invalid package path or checksum.')
        # Root-owned snapshot closes the inspection-to-install race. No scripts
        # from the source package execute before APT's final confirmation.
        with tempfile.TemporaryDirectory(prefix='macaque-desktop-update-') as temp:
            os.chmod(temp,0o755);target=Path(temp)/'macaque-classic.deb';shutil.copyfile(source,target);target.chmod(0o644)
            if digest(target)!=expected:raise ValueError('Package changed after inspection. Select it again.')
            data=metadata(target);print('Install Macaque Classic',data['version'],flush=True)
            subprocess.run(['/usr/bin/apt-get','install',str(target)],check=True)
        print('Desktop package installed. Save your work and log out/in to load the new desktop.');return
    raise ValueError('Unknown maintenance action.')
if __name__=='__main__':
    try:main(sys.argv[1:])
    except Exception as ex:print('Maintenance stopped:',ex,file=sys.stderr);sys.exit(1)
