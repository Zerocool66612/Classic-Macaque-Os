"""Installed-session-only, at-most-once-per-install/account welcome claim."""
import os,re
from pathlib import Path

def claim_welcome(root=Path('/'),state=None,environ=None,cmdline=None):
    env=os.environ if environ is None else environ;root=Path(root)
    if env.get('MACAQUE_NATIVE_SESSION')!='1' or env.get('MACAQUE_PREVIEW_SESSION')=='1':return False
    try:
        if cmdline is None:cmdline=(root/'proc/cmdline').read_text()
        if 'boot=live' in cmdline.split() or (root/'etc/macaque-live').exists():return False
        if not (root/'etc/macaque-installed').is_file():return False
        token=(root/'etc/macaque-welcome-install-id').read_text().strip()
        if not re.fullmatch(r'[0-9a-f-]{36}',token):return False
        folder=Path(state) if state is not None else Path(env.get('XDG_STATE_HOME') or Path.home()/'.local/state')/'macaque'
        folder.mkdir(parents=True,exist_ok=True)
        # Claim BEFORE showing: skipping, a crash or an interrupted login must not loop.
        fd=os.open(folder/('welcome-'+token+'.seen'),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as f:f.write('Welcome started or skipped; automatic replay disabled.\n')
        return True
    except OSError:return False

def start_welcome(d):
    if not claim_welcome():return False
    from welcome_animation import WelcomeAnimation
    d.welcome_intro=WelcomeAnimation(d)
    def finished(_):
        if not getattr(d,'quitting',False):d.initial();d.launch('Welcome Center')
    d.welcome_intro.finished.connect(finished);d.welcome_intro.showFullScreen();return True
