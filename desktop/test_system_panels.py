import os,tempfile,json,types,getpass,sys
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['MACAQUE_SILENT']='1'
from unittest.mock import patch
from PySide6.QtCore import QObject,Signal,QTimer,Qt
from PySide6.QtWidgets import QApplication,QDialog,QMessageBox
from PySide6.QtTest import QTest
import network_panel,power_panel,removable_drives,update_panel
from desktop import Desktop
app=QApplication([])
class FakeTask(QObject):
    done=Signal(bool,str);calls=[]
    @staticmethod
    def helper(name):return ['fixture-python',name]
    def __init__(self,parent,argv,payload=None,timeout=0):
        super().__init__(parent);self.calls.append((argv,payload));self.payload=payload;self.process=types.SimpleNamespace()
        def finish():
            if 'wifi_backend.py' in argv:self.done.emit(True,json.dumps({'message':'Connected to Fixture'}))
            elif 'power_backend.py' in argv:
                if payload['action']=='status':result={'available':True,'values':{'blank_ac':10,'blank_battery':5,'dim_ac':120,'dim_battery':60,'lid_ac':0,'lid_battery':1},'backlights':[{'name':'fixture','percent':40}]}
                else:result={'message':'Applied'}
                self.done.emit(True,json.dumps(result))
            elif 'removable_backend.py' in argv:self.done.emit(True,json.dumps({'disks':[]}))
            elif 'update_backend.py' in argv:self.done.emit(True,json.dumps({'releases':[]}))
            elif argv[0]=='nmcli':self.done.emit(True,'Fixture:90:WPA2:*:wlan0\n' if 'wifi' in argv else 'uuid-fixture:Fixture:802-11-wireless:yes:wlan0\n')
            else:self.done.emit(True,'')
        QTimer.singleShot(0,finish)
    def cancel(self):pass
original_which=network_panel.shutil.which
with patch.object(network_panel.shutil,'which',side_effect=lambda name:'/fixture/nmcli' if name=='nmcli' else original_which(name)),tempfile.TemporaryDirectory() as data,patch.object(network_panel,'Task',FakeTask),patch.object(power_panel,'Task',FakeTask),patch.object(removable_drives,'Task',FakeTask),patch.object(update_panel,'Task',FakeTask):
    d=Desktop(data);d.state.update(startup_files=False,startup_notes=False);d.show();QTest.qWait(50)
    windows={n:d.launch(n) for n in ['Network','Battery & Power','USB Drives','Software Update']};QTest.qWait(60)
    assert all(w.parent() is not None for w in windows.values())
    assert windows['Network'].content.list.topLevelItem(0).text(0)=='Fixture'
    assert d.launch('Battery & Power') is windows['Battery & Power']
    real=network_panel.WiFiDialog
    def dialog(*args,**kw):
        obj=real(*args,**kw);obj.password.setText('test-private-password');obj.exec=lambda:QDialog.Accepted;return obj
    with patch.object(network_panel,'WiFiDialog',side_effect=dialog):windows['Network'].content.connect_dialog('Fixture','wpa-psk',False,'wlan0')
    QTest.qWait(30);argv,payload=next((a,p) for a,p in FakeTask.calls if 'wifi_backend.py' in a)
    assert 'test-private-password' not in repr(argv) and payload['password']=='test-private-password'
    n=windows['Network'].content;n.refresh_saved();QTest.qWait(20);assert n.saved.topLevelItemCount()==1
    n.saved.setCurrentItem(n.saved.topLevelItem(0))
    with patch.object(QMessageBox,'question',return_value=QMessageBox.No):
        before=len(FakeTask.calls);n.forget_saved();assert len(FakeTask.calls)==before
    p=windows['Battery & Power'].content;p.apply();QTest.qWait(20);assert any(v and v.get('action')=='apply' for a,v in FakeTask.calls)
    with patch.object(QMessageBox,'question',return_value=QMessageBox.No):
        before=len(FakeTask.calls);p.suspend();assert len(FakeTask.calls)==before
    u=windows['Software Update'].content;u.check();QTest.qWait(20);assert 'No desktop' in u.status.text()
    # One alert per threshold, reset on charging; all notifications are desktop-local.
    sample=[{'name':'BAT0','percent':19,'status':'Discharging'}]
    with patch('laptop_support.batteries',return_value=sample),patch.object(d,'notify') as notify:
        d.top_bar.refresh_battery();d.top_bar.refresh_battery();assert notify.call_count==1
        sample[0]['percent']=9;d.top_bar.refresh_battery();assert notify.call_count==2
        sample[0]['status']='Charging';d.top_bar.refresh_battery();sample[0]['status']='Discharging';d.top_bar.refresh_battery();assert notify.call_count==3
    for w in windows.values():
        if hasattr(w.content,'timer'):w.content.timer.stop()
    d.removable.timer.stop();d.quitting=True;d.hide()
# Exercise NetworkManager settings/activation through a fake bus, with no network.
import wifi_backend
calls=[]
class Proxy:
    def __init__(self,path):self.path=path
    def GetDevices(self):return ['/device/wlan0']
    def Get(self,iface,key):return {'DeviceType':2,'Interface':'wlan0','State':2}[key]
    def ListConnections(self):return ['/settings/owned']
    def GetSettings(self):return {'connection':{'permissions':['user:'+getpass.getuser()+':'],'uuid':'existing'},'802-11-wireless':{'ssid':b'Fixture'},'ipv4':{'method':'manual'}}
    def Update(self,settings,**kw):calls.append(('update',settings))
    def ActivateConnection(self,path,device,ap,**kw):calls.append(('activate',path));return '/active/1'
class Bus:
    def get_object(self,service,path):return Proxy(path)
fake=types.SimpleNamespace(SystemBus=Bus,Interface=lambda proxy,iface:proxy,String=str,Boolean=bool,ByteArray=bytes,UInt32=int,ObjectPath=str,Array=lambda a,**kw:a,Dictionary=lambda a,**kw:a)
with patch.dict(sys.modules,dbus=fake):
    result=wifi_backend.connect({'ssid':'Fixture','security':'wpa-psk','password':'test-private-password','interface':'wlan0'})
assert calls[0][1]['ipv4']['method']=='manual'
assert calls[-1]==('activate','/settings/owned') and 'test-private-password' not in json.dumps(result)
print('Internal laptop panels, private Wi-Fi stdin payload, NetworkManager profile reuse, cancel guards and battery-notification tests passed (services mocked).')
