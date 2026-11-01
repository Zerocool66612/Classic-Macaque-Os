#!/usr/bin/python3
"""Unprivileged PipeWire and logind controls; never changes host preview hardware."""
import json,os,re,shutil,subprocess,sys
from power_backend import action as power,backlights
from laptop_support import batteries
ACTIONS=('volume-up','volume-down','mute','mic-mute','brightness-up','brightness-down')
def call(args):return subprocess.run(args,capture_output=True,text=True,check=True,timeout=5).stdout

def audio(source=False):
    if not shutil.which('wpctl'):raise ValueError('WirePlumber audio controls are unavailable.')
    text=call(['wpctl','get-volume','@DEFAULT_AUDIO_SOURCE@' if source else '@DEFAULT_AUDIO_SINK@'])
    match=re.search(r'Volume:\s*([0-9]+(?:\.[0-9]+)?)',text)
    if not match:raise ValueError('Could not read the default audio device.')
    return {'percent':max(0,min(100,round(float(match[1])*100))),'muted':'[MUTED]' in text}

def action(payload):
    op=payload.get('action','status')
    if op=='status':
        try:sound=audio();error=''
        except (ValueError,subprocess.SubprocessError,OSError) as ex:sound=None;error=str(ex)
        return {'audio':sound,'audio_error':error,'backlights':backlights(),'batteries':batteries()}
    if os.environ.get('MACAQUE_NATIVE_SESSION')!='1' or os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':raise ValueError('Use the installed/live Macaque session for laptop controls.')
    if op in ('volume-up','volume-down','mute','mic-mute','volume'):
        if not shutil.which('wpctl'):raise ValueError('WirePlumber audio controls are unavailable.')
        target='@DEFAULT_AUDIO_SOURCE@' if op=='mic-mute' else '@DEFAULT_AUDIO_SINK@'
        if op in ('mute','mic-mute'):call(['wpctl','set-mute',target,'toggle'])
        else:
            value=payload.get('percent')
            if op=='volume':
                if type(value) is not int or not 0<=value<=100:raise ValueError('Volume must be 0–100%.')
                amount=str(value)+'%'
            else:amount='5%+' if op=='volume-up' else '5%-'
            call(['wpctl','set-volume','--limit','1.0',target,amount])
        result=audio(op=='mic-mute');result.update(kind='Microphone' if op=='mic-mute' else 'Volume');return result
    if op in ('brightness-up','brightness-down','brightness'):
        devices=backlights()
        if not devices:raise ValueError('No laptop backlight was found. Virtual machines and external monitors may not expose one.')
        device=devices[0];value=payload.get('percent') if op=='brightness' else max(5,min(100,device['percent']+(5 if op=='brightness-up' else -5)))
        power({'action':'brightness','device':device['name'],'percent':value});return {'kind':'Brightness','percent':value,'muted':False}
    raise ValueError('Unknown laptop action.')
if __name__=='__main__':
    try:print(json.dumps(action(json.loads(sys.stdin.read(4096)))))
    except Exception as ex:
        print(ex.stderr.strip() if isinstance(ex,subprocess.CalledProcessError) and ex.stderr else str(ex),file=sys.stderr);sys.exit(1)
