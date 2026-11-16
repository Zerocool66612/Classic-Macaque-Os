#!/usr/bin/python3
"""Explicit interactive maintenance; never downloads or executes raw source."""
import hashlib,os,re,subprocess,sys,tempfile,shutil,fcntl
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
    if len(args)==3 and args[0] in ('install-desktop','rollback-desktop'):
        source=Path(args[1]);expected=args[2]
        if not source.is_absolute() or not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('Invalid package path or checksum.')
        from update_store import STORE,installed_version,older,cache_package,receipt
        STORE.mkdir(parents=True,exist_ok=True)
        lock=(STORE/'update.lock').open('w')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another desktop update is already running.')
        rollback=args[0]=='rollback-desktop'
        if rollback and (source.is_symlink() or source.resolve().parent!=STORE.resolve()):raise ValueError('Choose a saved desktop package from update history.')
        previous=installed_version()
        # Root-owned snapshot closes the inspection-to-install race. No scripts
        # from the source package execute before APT's final confirmation.
        with tempfile.TemporaryDirectory(prefix='macaque-desktop-update-') as temp:
            os.chmod(temp,0o755);target=Path(temp)/'macaque-classic.deb';shutil.copyfile(source,target);target.chmod(0o644)
            if digest(target)!=expected:raise ValueError('Package changed after inspection. Select it again.')
            data=metadata(target)
            if rollback and not older(data['version'],previous):raise ValueError('Rollback requires an older saved desktop package.')
            if not rollback and older(data['version'],previous):raise ValueError('Use Roll Back for an older desktop package.')
            # APT may already have the previous package; retain it when available.
            if previous:
                old=Path('/var/cache/apt/archives')/('macaque-classic_'+previous+'_amd64.deb')
                if old.is_file() and metadata(old)['version']==previous:cache_package(old)
            print(('Roll back to' if rollback else 'Install')+' Macaque Classic '+data['version'],flush=True)
            try:
                subprocess.run(['/usr/bin/apt-get',*(['--allow-downgrades'] if rollback else []),'install',str(target)],check=True)
            except Exception:
                receipt(data['version'],previous,'failed or cancelled',args[0]);raise
            if installed_version()!=data['version']:
                receipt(data['version'],previous,'not applied',args[0]);raise ValueError('APT did not apply the selected desktop version.')
            cache_package(target);receipt(data['version'],previous,'installed',args[0])
        print('Desktop package installed. Save your work and log out/in to load the new desktop.');return
    raise ValueError('Unknown maintenance action.')
if __name__=='__main__':
    try:main(sys.argv[1:])
    except Exception as ex:print('Maintenance stopped:',ex,file=sys.stderr);sys.exit(1)
