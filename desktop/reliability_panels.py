"""Classic panels for real hardware services and installation diagnostics."""
import json,os,subprocess,shutil
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QPushButton,QComboBox,QCheckBox,QDoubleSpinBox,QSpinBox,QSlider,QListWidget,QListWidgetItem,QPlainTextEdit,QMessageBox,QDialog
from system_tasks import Task
class Panel(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.job=None;self.v=QVBoxLayout(self);self.status=QLabel();self.status.setTextFormat(Qt.PlainText);self.status.setWordWrap(True);self.v.addWidget(self.status)
 def button(self,text,fn):
  b=QPushButton(text);b.clicked.connect(fn);self.v.addWidget(b);return b
 def request(self,p,callback=None,helper='reliability_backend.py',timeout=30000):
  if self.job:return
  self.status.setText('Working…');self.job=Task(self,Task.helper(helper),p,timeout=timeout)
  def done(ok,text):
   self.job=None
   if not ok:self.status.setText(text);return
   try:data=json.loads(text)
   except ValueError:self.status.setText('Could not read the service response.');return
   self.status.setText(data.get('message','Loaded.'))
   if callback:callback(data)
  self.job.done.connect(done)
 def can_close(self):
  if self.job:self.status.setText('Wait for the current request to finish.');return False
  return True
class Touchpad(Panel):
 app_name='Touchpad'
 def __init__(self,d):
  super().__init__(d);self.fields={}
  for key,text in [('tap','Tap to click'),('naturalScroll','Natural scrolling'),('disableWhileTyping','Disable touchpad while typing')]:
   box=QCheckBox(text);self.v.addWidget(box);self.fields[key]=box
  self.speed=QSlider(Qt.Horizontal);self.speed.setRange(-100,100);self.v.addWidget(QLabel('Touchpad pointer speed'));self.v.addWidget(self.speed);self.button('Apply',self.apply);self.button('Refresh',self.refresh);self.v.addWidget(QLabel('Touchpad settings are saved per user. A mouse/VM pointer is not a touchpad.'));self.v.addStretch();self.refresh()
 def refresh(self):self.request({'action':'touchpad-status'},self.loaded)
 def loaded(self,data):
  for key,field in self.fields.items():field.setChecked(data[key])
  self.speed.setValue(round(data['pointerSpeed']*100))
 def apply(self):self.request({'action':'touchpad-apply','values':dict({k:v.isChecked() for k,v in self.fields.items()},pointerSpeed=self.speed.value()/100)})
class Displays(Panel):
 app_name='Displays'
 def __init__(self,d):
  super().__init__(d);self.outputs=[];self.token=None;form=QFormLayout();self.v.addLayout(form);self.output=QComboBox();self.output.currentIndexChanged.connect(self.selected);form.addRow('Display',self.output);self.mode=QComboBox();form.addRow('Resolution / refresh',self.mode);self.scale=QDoubleSpinBox();self.scale.setRange(.5,3);self.scale.setSingleStep(.25);form.addRow('Scale',self.scale);self.x=QSpinBox();self.y=QSpinBox()
  for field in (self.x,self.y):field.setRange(-20000,20000)
  form.addRow('Horizontal position',self.x);form.addRow('Vertical position',self.y);self.rotation=QComboBox();self.rotation.addItems(['normal','90','180','270']);form.addRow('Rotation',self.rotation);self.button('Preview for 20 seconds',self.preview);self.button('Refresh',self.refresh);self.v.addWidget(QLabel('Positions arrange external monitors. For a display to the right, set X to the first screen’s logical width. Unconfirmed changes roll back independently of this window.'));self.v.addStretch();self.refresh()
 def refresh(self):self.request({'action':'display-status'},self.loaded)
 def loaded(self,data):
  self.outputs=data['outputs'];self.output.blockSignals(True);self.output.clear()
  for output in self.outputs:self.output.addItem(output['description'],output['name'])
  self.output.blockSignals(False);self.selected()
 def selected(self,*_):
  i=self.output.currentIndex()
  if not 0<=i<len(self.outputs):return
  item=self.outputs[i];self.mode.clear();self.mode.addItems(item['modes']);self.mode.setCurrentText(item['current'] or (item['modes'][0] if item['modes'] else ''));self.scale.setValue(item['scale']);self.x.setValue(item['position'][0]);self.y.setValue(item['position'][1]);self.rotation.setCurrentText(item['transform'])
 def preview(self):
  if not self.output.currentData():return
  value={'name':self.output.currentData(),'mode':self.mode.currentText(),'scale':self.scale.value(),'x':self.x.value(),'y':self.y.value(),'transform':self.rotation.currentText()}
  self.request({'action':'display-preview','value':value},self.confirm)
 def confirm(self,data):
  self.token=data['token'];box=QMessageBox(QMessageBox.Question,'Keep display settings?','Keep this display change? It automatically reverts after 20 seconds.',QMessageBox.Yes|QMessageBox.No,self);box.setDefaultButton(QMessageBox.No);timer=QTimer(box);timer.setSingleShot(True);timer.timeout.connect(box.reject);timer.start(15000);keep=box.exec()==QMessageBox.Yes
  self.request({'action':'display-keep' if keep else 'display-revert','token':self.token},lambda _:self.refresh());self.token=None
class PowerProfiles(Panel):
 app_name='Power Profiles'
 def __init__(self,d):
  super().__init__(d);self.profiles=QComboBox();self.v.addWidget(self.profiles);self.details=QPlainTextEdit();self.details.setReadOnly(True);self.v.addWidget(self.details);self.button('Apply profile',lambda:self.request({'action':'profile-set','profile':self.profiles.currentData()},lambda _:self.refresh()));self.button('Refresh',self.refresh);self.refresh()
 def refresh(self):self.request({'action':'profiles-status'},self.loaded)
 def loaded(self,data):
  self.profiles.clear()
  for name in data['profiles']:self.profiles.addItem(name.replace('-',' ').title(),name)
  self.profiles.setCurrentIndex(max(0,self.profiles.findData(data['active'])));self.details.setPlainText(data['details'])
class AudioDevices(Panel):
 app_name='Audio Devices'
 def __init__(self,d):
  super().__init__(d);self.output=QComboBox();self.input=QComboBox();form=QFormLayout();self.v.addLayout(form);form.addRow('Speakers / headphones',self.output);form.addRow('Microphone',self.input);self.level=QSlider(Qt.Horizontal);self.level.setRange(0,100);form.addRow('Microphone level',self.level);self.input.currentIndexChanged.connect(self.selected);self.devices=[]
  self.button('Use selected output',lambda:self.change('audio-output',self.output));self.button('Use selected microphone',lambda:self.change('audio-input',self.input));self.button('Apply microphone level',lambda:self.change('audio-input-volume',self.input,percent=self.level.value()));self.button('Mute / unmute microphone',lambda:self.change('audio-input-mute',self.input));self.button('Play quiet test tone',lambda:self.request({'action':'audio-test'}));self.button('Refresh',self.refresh);self.refresh()
 def change(self,action,field,**kwargs):
  if field.currentData():self.request(dict(action=action,name=field.currentData(),**kwargs),lambda _:self.refresh())
 def refresh(self):self.request({'action':'audio-status'},self.loaded)
 def loaded(self,data):
  self.devices=data['inputs']
  for combo,key,default in [(self.output,'outputs','default_output'),(self.input,'inputs','default_input')]:
   combo.blockSignals(True);combo.clear()
   for item in data[key]:combo.addItem(item['description']+(' (muted)' if item['muted'] else ''),item['name'])
   combo.setCurrentIndex(max(0,combo.findData(data[default])));combo.blockSignals(False)
  self.selected()
 def selected(self,*_):
  item=next((x for x in self.devices if x['name']==self.input.currentData()),None)
  if item:self.level.setValue(item['percent'])
class Bluetooth(Panel):
 app_name='Bluetooth'
 def __init__(self,d):
  super().__init__(d);self.adapter=None;self.powered=False;self.items=QListWidget();self.v.addWidget(self.items);self.button('Bluetooth on / off',lambda:self.request({'action':'bluetooth-power','enabled':not self.powered,'adapter':self.adapter},self.loaded));self.button('Scan nearby devices',lambda:self.request({'action':'bluetooth-scan','adapter':self.adapter},self.loaded));self.button('Pair New Device…',self.pair)
  for text,op in [('Connect','bluetooth-connect'),('Disconnect','bluetooth-disconnect'),('Forget device…','bluetooth-forget')]:self.button(text,lambda checked=False,a=op:self.change(a))
  self.button('Refresh',self.refresh);self.refresh()
 def refresh(self):self.request({'action':'bluetooth-status'},self.loaded)
 def loaded(self,data):
  self.adapter=data['adapter'];self.powered=data['powered'];self.items.clear();self.status.setText('Bluetooth on' if self.powered else 'Bluetooth off')
  for item in data['devices']:
   row=QListWidgetItem(item['name']+(' · connected' if item['connected'] else ' · paired' if item['paired'] else ' · nearby'));row.setData(Qt.UserRole,item);self.items.addItem(row)
 def change(self,op):
  row=self.items.currentItem()
  if not row:return
  if op=='bluetooth-forget' and QMessageBox.question(self,'Forget device','Remove this device pairing?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  self.request({'action':op,'device':row.data(Qt.UserRole)['path'],'adapter':self.adapter},self.loaded)
 def pair(self):
  if os.environ.get('MACAQUE_NATIVE_SESSION')!='1' or os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':self.status.setText('Pair devices from the live/installed Macaque login session.');return
  if not shutil.which('blueman-assistant'):self.status.setText('Bluetooth pairing wizard is unavailable.');return
  try:subprocess.Popen(['blueman-assistant'],env=dict(os.environ,GDK_BACKEND='wayland'));self.status.setText('Complete the native pairing wizard and any PIN/passkey confirmation, then Refresh.')
  except OSError as ex:self.status.setText(str(ex))
class Diagnostics(Panel):
 app_name='Recovery & Diagnostics'
 def __init__(self,d):
  super().__init__(d);self.text=QPlainTextEdit();self.text.setReadOnly(True);self.v.addWidget(self.text);self.button('Refresh report preview',self.refresh);self.button('Save support report to Documents',self.export);self.button('Open Documents',lambda:d.open_finder(d.disk.root/'Documents'));self.button('Installer status and logs',lambda:d.launch('Installer Status'));self.v.addWidget(QLabel('Reports stay local. Credential-like lines and common addresses are filtered; review the preview before sharing. No saved network profiles or environment dump is collected.'));self.refresh()
 def refresh(self):self.request({'action':'diagnostics-status'},lambda x:self.text.setPlainText(x['text']),helper='diagnostics_backend.py',timeout=65000)
 def export(self):self.request({'action':'diagnostics-export','directory':str(self.d.disk.root/'Documents')},lambda _:self.d.disk_changed.emit(),helper='diagnostics_backend.py',timeout=65000)
class InstallerStatus(Panel):
 app_name='Installer Status'
 def __init__(self,d):
  super().__init__(d);self.text=QPlainTextEdit();self.text.setReadOnly(True);self.v.addWidget(self.text);self.button('Refresh installer log',self.refresh);self.button('Recovery & Diagnostics',lambda:d.launch('Recovery & Diagnostics'));self.button('Restart computer…',self.restart);self.refresh()
 def refresh(self):self.request({'action':'installer-status'},self.loaded,helper='diagnostics_backend.py')
 def loaded(self,data):self.status.setText(data.get('message','Installer status unavailable.'));self.text.setPlainText(data.get('log_text',data.get('log','')))
 def restart(self):
  if os.environ.get('MACAQUE_NATIVE_SESSION')!='1' or os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':self.status.setText('Restart is available only in the live/installed Macaque session.');return
  if self.d.installer_busy():self.status.setText('Finish or cancel the installer first.');return
  if QMessageBox.question(self,'Restart computer','Save work first. Restart this computer now? Remove the live USB when reboot begins to try the installed disk.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  if self.job:return
  self.job=Task(self,['systemctl','reboot'])
  def done(ok,text):self.job=None;self.status.setText('Restart requested.' if ok else text)
  self.job.done.connect(done)
