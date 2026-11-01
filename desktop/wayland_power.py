#!/usr/bin/python3
"""Wayland idle service. logind retains lid handling and suspend ownership."""
import json,os,shlex,signal,subprocess,sys,time
from pathlib import Path

def config_path():return Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'macaque/wayland-power.json'
def preferences():
    from power_backend import PROPS
    defaults={k:v[2] for k,v in PROPS.items()}
    try:defaults.update(json.loads(config_path().read_text()))
    except (OSError,ValueError):pass
    return defaults

def save(values):
    from power_backend import settings_commands
    settings_commands(values) # Reuse range/type validation, execute no X11 commands.
    p=config_path();p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(values));tmp.chmod(0o600);tmp.replace(p)

def idle_command(values,battery):
    suffix='battery' if battery else 'ac';blank=values['blank_'+suffix];dim=values['dim_'+suffix]
    helper=shlex.join(['/usr/bin/python3',str(Path(__file__).resolve())])
    args=['swayidle','-w','before-sleep','/usr/local/bin/macaque-lock','after-resume',"wlopm --on '*' "]
    if dim!=9:args += ['timeout',str(dim),helper+' dim','resume',helper+' restore']
    if blank:args += ['timeout',str(blank*60),"/usr/local/bin/macaque-lock && wlopm --off '*'",'resume',"wlopm --on '*'"]
    return args

def dim(restore=False):
    from power_backend import backlights,action
    state=Path(os.environ['XDG_RUNTIME_DIR'])/'macaque-backlight.json'
    if restore:
        try:items=json.loads(state.read_text());state.unlink()
        except (OSError,ValueError):return
    else:
        items=backlights();state.write_text(json.dumps(items));state.chmod(0o600)
    for item in items:
        try:action({'action':'brightness','device':item['name'],'percent':max(5,min(100,item['percent'])) if restore else 15})
        except Exception as ex:print('Backlight:',ex,file=sys.stderr)

def daemon():
    from laptop_support import batteries
    running=True;child=None;previous=None
    def stop(*_):
        nonlocal running
        running=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        while running:
            packs=batteries();battery=any(p.get('status','').lower()=='discharging' for p in packs)
            values=preferences();key=(tuple(sorted(values.items())),battery)
            if key!=previous or child is None or child.poll() is not None:
                if child and child.poll() is None:child.terminate();child.wait(timeout=5)
                child=subprocess.Popen(idle_command(values,battery));previous=key
            time.sleep(1)
    finally:
        if child and child.poll() is None:child.terminate();child.wait(timeout=5)
        dim(True)
if __name__=='__main__':
    operation=sys.argv[1] if len(sys.argv)>1 else 'daemon'
    if operation=='daemon':daemon()
    elif operation in ('dim','restore'):dim(operation=='restore')
    else:raise SystemExit('Unknown power operation')
