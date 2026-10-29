"""Battery edge cases and Wi-Fi scan/UI behavior using a fake nmcli executable."""
import os,tempfile,time
from pathlib import Path
from laptop_support import batteries,battery_summary,split_fields
assert split_fields(r'Cafe\:North:82:WPA2:*')==['Cafe:North','82','WPA2','*']
assert split_fields(r'Home\\Room:50:WPA3:')==['Home\\Room','50','WPA3','']
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp)
 def supply(name,values):
  p=root/name;p.mkdir()
  for k,v in values.items():(p/k).write_text(str(v))
 supply('BAT0',{'type':'Battery','capacity':67,'status':'Charging','present':1,'scope':'System'})
 supply('mouse',{'type':'Battery','capacity':90,'scope':'Device'})
 supply('absent',{'type':'Battery','present':0})
 supply('AC',{'type':'Mains','online':1})
 assert batteries(root)==[{'name':'BAT0','percent':67,'status':'Charging'}]
 assert battery_summary(batteries(root))[0]=='+ 67%'
 (root/'BAT0/capacity').write_text('bad');assert batteries(root)[0]['percent'] is None
 (root/'BAT0/capacity').write_text('150');assert batteries(root)[0]['percent']==100
 (root/'BAT0').rename(root/'removed');assert batteries(root)[0]['name']=='removed'
assert battery_summary([])[0]==''
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QProcess
from network_panel import Network
app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp)/'nmcli';p.write_text('#!/bin/sh\nprintf "%s\\n" "Cafe\\:North:82:WPA2:*" "Guest:33::"\n');p.chmod(0o755)
 old=os.environ['PATH'];os.environ['PATH']=temp+':'+old
 class D:pass
 panel=Network(D())
 deadline=time.monotonic()+5
 while panel.job and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
 assert panel.job is None and panel.list.topLevelItemCount()==2,panel.status.text()
 assert panel.list.topLevelItem(0).text(0)=='Cafe:North'
 assert panel.list.topLevelItem(0).text(3)=='Yes'
 panel.can_close();panel.deleteLater();app.processEvents();os.environ['PATH']=old
print('Laptop battery filtering/unknown readings and asynchronous Wi-Fi scan tests passed (fake nmcli).')
