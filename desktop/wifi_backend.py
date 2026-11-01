#!/usr/bin/python3
"""NetworkManager D-Bus connection helper. Credentials arrive on stdin only."""
import json,sys,time,uuid,getpass
NM='org.freedesktop.NetworkManager';BASE='/org/freedesktop/NetworkManager'
def validate(payload):
    ssid=payload.get('ssid','');security=payload.get('security','open');password=payload.get('password','')
    if not isinstance(ssid,str) or not 1<=len(ssid.encode())<=32:raise ValueError('Network name must contain 1–32 UTF-8 bytes.')
    if security not in ('open','wpa-psk','sae'):raise ValueError('Use the advanced connection editor for this security type.')
    if security!='open' and not (8<=len(password)<=63 or security=='wpa-psk' and len(password)==64 and all(c in '0123456789abcdefABCDEF' for c in password)):raise ValueError('Enter an 8–63 character password, or a 64-digit hexadecimal WPA key.')
    interface=payload.get('interface','')
    if not isinstance(interface,str) or len(interface)>64:raise ValueError('Invalid network interface.')
    return ssid,security,password,interface

def connect(payload):
    ssid,security,password,interface=validate(payload)
    import dbus
    bus=dbus.SystemBus();manager=dbus.Interface(bus.get_object(NM,BASE),NM)
    def prop(path,iface,key):return dbus.Interface(bus.get_object(NM,path),'org.freedesktop.DBus.Properties').Get(iface,key)
    device=None
    for path in manager.GetDevices():
        if int(prop(path,NM+'.Device','DeviceType'))==2 and (not interface or str(prop(path,NM+'.Device','Interface'))==interface):device=path;break
    if device is None:raise ValueError('No matching Wi-Fi adapter is available. Check airplane mode and drivers.')
    connection={'id':dbus.String(ssid),'uuid':dbus.String(str(uuid.uuid4())),'type':dbus.String('802-11-wireless'),'autoconnect':dbus.Boolean(True),'permissions':dbus.Array(['user:'+getpass.getuser()+':'],signature='s')}
    wireless={'ssid':dbus.ByteArray(ssid.encode()),'mode':dbus.String('infrastructure'),'hidden':dbus.Boolean(bool(payload.get('hidden')))}
    settings={'connection':connection,'802-11-wireless':wireless,'ipv4':{'method':dbus.String('auto')},'ipv6':{'method':dbus.String('auto')}}
    if security!='open':settings['802-11-wireless-security']={'key-mgmt':dbus.String(security),'psk':dbus.String(password),'psk-flags':dbus.UInt32(0)}
    # Update an existing user-owned profile for the same SSID; leave system and
    # other users' profiles alone. Never print GetSettings() or supplied secrets.
    service=dbus.Interface(bus.get_object(NM,BASE+'/Settings'),NM+'.Settings');existing=None;existing_path=None
    for path in service.ListConnections():
        proxy=dbus.Interface(bus.get_object(NM,path),NM+'.Settings.Connection');old=proxy.GetSettings();c=old.get('connection',{})
        old_wifi=old.get('802-11-wireless',{});old_security=old.get('802-11-wireless-security',{})
        if bytes(old_wifi.get('ssid',b''))==ssid.encode() and 'user:'+getpass.getuser()+':' in c.get('permissions',[]) and c.get('interface-name','') in ('',interface) and old_wifi.get('mode','infrastructure')=='infrastructure' and old_security.get('key-mgmt','') in ('','wpa-psk','sae'):
            existing=proxy;existing_path=path
            # Preserve a user's IP/DNS/proxy settings when updating a personal
            # Wi-Fi profile, rather than silently replacing them with DHCP.
            merged={k:dict(v) for k,v in old.items()};merged['connection'].update({'autoconnect':dbus.Boolean(True)})
            merged.setdefault('802-11-wireless',{}).update(wireless)
            for key in ('ipv4','ipv6'):merged.setdefault(key,settings[key])
            if security=='open':merged.pop('802-11-wireless-security',None)
            else:merged.setdefault('802-11-wireless-security',{}).update(settings['802-11-wireless-security'])
            settings=merged;break
    typed=dbus.Dictionary({k:dbus.Dictionary(v,signature='sv') for k,v in settings.items()},signature='sa{sv}')
    if existing:
        existing.Update(typed,timeout=60);active=manager.ActivateConnection(existing_path,device,dbus.ObjectPath('/'),timeout=60)
    else:_,active=manager.AddAndActivateConnection(typed,device,dbus.ObjectPath('/'),timeout=60)
    deadline=time.monotonic()+65
    while time.monotonic()<deadline:
        state=int(prop(active,NM+'.Connection.Active','State'))
        if state==2:return {'message':'Connected to '+ssid}
        if state==4:raise ValueError('Connection failed. Check your password and signal, then try again.')
        time.sleep(.3)
    raise ValueError('Connection timed out. Check the password, signal and router.')

if __name__=='__main__':
    try:
        payload=json.loads(sys.stdin.read(16384));print(json.dumps(connect(payload)))
    except ImportError:print('Wi-Fi service support is missing. Install python3-dbus.',file=sys.stderr);sys.exit(1)
    except ValueError as ex:print(str(ex),file=sys.stderr);sys.exit(1)
    except Exception as ex:
        # D-Bus errors can contain settings. Report the error type, never payload.
        name=getattr(ex,'get_dbus_name',lambda:type(ex).__name__)();print('NetworkManager could not connect ('+name+'). Check permissions, password and adapter status.',file=sys.stderr);sys.exit(1)
