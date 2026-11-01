#!/usr/bin/python3
"""User-owned laptop preferences; privileged actions stay with logind/polkit."""
import json,subprocess,sys,os,shutil
from pathlib import Path
# Xfce power manager properties; blanking minutes, dimming seconds.
PROPS={'blank_ac':('blank-on-ac','int',10),'blank_battery':('blank-on-battery','int',5),'dim_ac':('brightness-on-ac','uint',120),'dim_battery':('brightness-on-battery','uint',60),'lid_ac':('lid-action-on-ac','uint',3),'lid_battery':('lid-action-on-battery','uint',3)}
def settings_commands(values):
    args=[]
    for key,(name,kind,default) in PROPS.items():
        value=values.get(key,default)
        if type(value) is not int:raise ValueError('Power settings must be whole numbers.')
        if key.startswith('lid_'):
            if value not in (0,1,3,4):raise ValueError('Choose a supported lid-close action.')
        elif key.startswith('dim_'):
            if not 9<=value<=3600:raise ValueError('Dimming must be 9–3600 seconds (9 disables dimming).')
        elif not 0<=value<=120:raise ValueError('Screen blanking must be 0–120 minutes.')
        args.append(['xfconf-query','-c','xfce4-power-manager','-p','/xfce4-power-manager/'+name,'--create','--type',kind,'--set',str(value)])
    args += [['xfconf-query','-c','xfce4-power-manager','-p','/xfce4-power-manager/'+name,'--create','--type','bool','--set',value] for name,value in [('logind-handle-lid-switch','false'),('lock-screen-suspend-hibernate','true')]]
    return args

def backlights(root='/sys/class/backlight'):
    items=[]
    for p in sorted(Path(root).glob('*')):
        try:
            maximum=int((p/'max_brightness').read_text());value=int((p/'brightness').read_text())
            if maximum>0:items.append({'name':p.name,'maximum':maximum,'value':value,'percent':round(value*100/maximum)})
        except (OSError,ValueError):pass
    return items

def action(payload):
    operation=payload.get('action','status')
    if operation=='status':
        values={}
        for key,(name,kind,default) in PROPS.items():
            value=default
            if shutil.which('xfconf-query'):
                r=subprocess.run(['xfconf-query','-c','xfce4-power-manager','-p','/xfce4-power-manager/'+name],capture_output=True,text=True,timeout=5)
                try:value=int(r.stdout.strip()) if r.returncode==0 else default
                except ValueError:pass
            values[key]=value
        return {'available':bool(shutil.which('xfconf-query')),'values':values,'backlights':backlights()}
    if os.environ.get('MACAQUE_NATIVE_SESSION')!='1':raise ValueError('Power changes are available in the installed/live Macaque login session.')
    if operation=='apply':
        commands=settings_commands(payload['values'])
        for cmd in commands:subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=15)
        return {'message':'Lid, dimming and screen-blanking preferences applied to the power service.'}
    if operation=='brightness':
        percent=payload.get('percent');name=payload.get('device')
        if type(percent) is not int or not 5<=percent<=100:raise ValueError('Brightness must be 5–100%.')
        device=next((d for d in backlights() if d['name']==name),None)
        if not device:raise ValueError('Backlight device is unavailable.')
        import dbus
        bus=dbus.SystemBus();manager=dbus.Interface(bus.get_object('org.freedesktop.login1','/org/freedesktop/login1'),'org.freedesktop.login1.Manager');session=manager.GetSessionByPID(dbus.UInt32(os.getpid()))
        proxy=dbus.Interface(bus.get_object('org.freedesktop.login1',session),'org.freedesktop.login1.Session');proxy.SetBrightness('backlight',name,dbus.UInt32(max(1,round(device['maximum']*percent/100))),timeout=15)
        return {'message':'Brightness updated.'}
    raise ValueError('Unknown power request.')
if __name__=='__main__':
    try:print(json.dumps(action(json.loads(sys.stdin.read(16384)))))
    except Exception as ex:
        print(ex.stderr.strip() if isinstance(ex,subprocess.CalledProcessError) and ex.stderr else str(ex),file=sys.stderr);sys.exit(1)
