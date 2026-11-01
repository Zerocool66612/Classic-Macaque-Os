import json,os
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QFormLayout,QHBoxLayout,QLabel,QSpinBox,QComboBox,QPushButton,QSlider,QCheckBox,QMessageBox
from system_tasks import Task
from laptop_support import batteries,battery_summary
class PowerPanel(QWidget):
    app_name='Battery & Power'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;self.backlight=None;v=QVBoxLayout(self);self.battery=QLabel();v.addWidget(self.battery);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status)
        form=QFormLayout();v.addLayout(form);self.fields={}
        for key,label in [('blank_ac','Blank screen on AC (minutes; 0 = never)'),('blank_battery','Blank screen on battery (minutes; 0 = never)'),('dim_ac','Dim on AC (seconds; 9 = never)'),('dim_battery','Dim on battery (seconds; 9 = never)')]:
            b=QSpinBox();b.setRange(9 if key.startswith('dim') else 0,3600 if key.startswith('dim') else 120);form.addRow(label,b);self.fields[key]=b
        for key,label in [('lid_ac','Close lid on AC'),('lid_battery','Close lid on battery')]:
            b=QComboBox();b.addItem('Blank screen',0);b.addItem('Suspend',1);b.addItem('Lock screen',3);b.addItem('Do nothing',4);form.addRow(label,b);self.fields[key]=b
        self.brightness=QSlider(Qt.Horizontal);self.brightness.setRange(5,100);self.brightness.setEnabled(False);self.brightness.sliderReleased.connect(self.set_brightness);form.addRow('Screen brightness',self.brightness)
        self.warning=QCheckBox('Show low-battery notifications (20%, 10%, 5%)');self.warning.setChecked(d.state.get('low_battery_warnings',True));self.warning.toggled.connect(lambda v:d.set_preference('low_battery_warnings',v));v.addWidget(self.warning)
        row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('Refresh',self.refresh),('Apply',self.apply),('Lock Screen',self.lock),('Suspend…',self.suspend)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        note=QLabel('Power actions affect this laptop. Save your work before suspending. Lid and idle behavior use the system power service; hardware support varies.');note.setWordWrap(True);v.addWidget(note);v.addStretch(1)
        self.timer=QTimer(self);self.timer.timeout.connect(self.battery_status);self.timer.start(10000);self.battery_status();self.refresh()
    def battery_status(self):self.battery.setText(battery_summary(batteries())[1])
    def run(self,payload,callback=None):
        if self.job:return
        self.job=Task(self,Task.helper('power_backend.py'),payload)
        def done(ok,text):
            self.job=None
            if not ok:self.status.setText(text);return
            try:data=json.loads(text)
            except ValueError:self.status.setText('Could not read power information.');return
            if callback:callback(data)
            else:self.status.setText(data.get('message','Done.'))
        self.job.done.connect(done)
    def refresh(self):self.run({'action':'status'},self.loaded)
    def loaded(self,data):
        for key,value in data['values'].items():
            field=self.fields[key]
            if isinstance(field,QComboBox):field.setCurrentIndex(max(0,field.findData(value)))
            else:field.setValue(value)
        if data.get('lid_managed') is False:
            for key in ('lid_ac','lid_battery'):
                field=self.fields[key];field.setEnabled(False);field.setItemText(field.currentIndex(),'System lid policy (managed by logind)')
        self.backlight=data['backlights'][0] if data['backlights'] else None;self.brightness.setEnabled(bool(self.backlight))
        if self.backlight:self.brightness.setValue(self.backlight['percent'])
        self.status.setText(('Wayland idle preferences loaded. Lid closing uses system suspend settings.' if data.get('lid_managed') is False else 'Power preferences loaded (defaults where unset). Click Apply to change them.') if data['available'] else 'Power manager is missing. Use the new ISO or install the desktop update package.')
    def apply(self):
        values={k:v.currentData() if isinstance(v,QComboBox) else v.value() for k,v in self.fields.items()};self.run({'action':'apply','values':values})
    def set_brightness(self):
        if self.backlight:self.run({'action':'brightness','device':self.backlight['name'],'percent':self.brightness.value()})
    def session_action(self,args):
        if os.environ.get('MACAQUE_PREVIEW_SESSION')=='1':self.status.setText('Lock and suspend are disabled in the nested preview.');return
        if os.environ.get('MACAQUE_NATIVE_SESSION')!='1':self.status.setText('Use the Macaque login session for locking and suspend.');return
        if self.job:return
        self.job=Task(self,args,timeout=20000)
        def done(ok,text):self.job=None;self.status.setText('Request sent to the session service.' if ok else text)
        self.job.done.connect(done)
    def lock(self):self.session_action(['/usr/local/bin/macaque-lock'] if os.environ.get('MACAQUE_WAYLAND_SESSION')=='1' else ['light-locker-command','--lock'])
    def suspend(self):
        if QMessageBox.question(self,'Suspend laptop','Save your work first. Suspend this laptop now?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.session_action(['systemctl','suspend'])
    def can_close(self):
        if self.job:self.status.setText('Wait for the power request to finish.');return False
        self.timer.stop();return True
