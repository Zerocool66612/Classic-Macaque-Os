import json,os
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from system_tasks import Task

class ServicesPanel(QWidget):
    def __init__(self,d):super().__init__();self.d=d;self.job=None;self.v=QVBoxLayout(self);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);self.v.addWidget(self.status)
    def request(self,p,callback=None):
        if self.job:return
        self.status.setText('Working…');self.job=Task(self,Task.helper('desktop_services.py'),p,timeout=630000 if p['action'].startswith('flatpak-') else 65000 if p['action']=='suspend' else 35000)
        def done(ok,text):
            self.job=None
            if not ok:self.status.setText(text);return
            try:data=json.loads(text)
            except ValueError:self.status.setText('The service returned unreadable data.');return
            self.status.setText(data.get('message','Completed.'))
            if callback:callback(data)
        self.job.done.connect(done)
    def can_close(self):
        if self.job:self.status.setText('Wait for the current operation to finish.');return False
        return True

class SoftwareCenter(ServicesPanel):
    app_name='Software Center'
    def __init__(self,d):
        super().__init__(d);self.status.setText('Flatpak apps for your user. Enable Flathub once, then search for an app. Network access is needed for browsing and downloads.')
        self.query=QLineEdit();self.query.setPlaceholderText('Search Flathub by app name…');self.query.returnPressed.connect(self.search);self.v.addWidget(self.query)
        row=QHBoxLayout();self.v.addLayout(row)
        for title,fn in [('Enable Flathub…',self.enable),('Search',self.search),('Installed',lambda:self.rows('flatpak-installed')),('Available Updates',lambda:self.rows('flatpak-updates'))]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        self.items=QListWidget();self.items.setWordWrap(True);self.v.addWidget(self.items,1)
        row=QHBoxLayout();self.v.addLayout(row)
        for title,fn in [('Install selected…',self.install),('Launch selected',self.launch),('Remove selected…',self.remove),('Update all…',self.update)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        note=QLabel('Launching requires a Wayland-capable app. Existing Flatpak Apps remains available for local .flatpakref files.');note.setWordWrap(True);self.v.addWidget(note)
    def rows(self,op):self.request({'action':op},self.loaded)
    def loaded(self,data):
        self.items.clear()
        for line in data.get('rows',[]):
            fields=line.split('\t');appid=fields[0].strip();item=QListWidgetItem(' · '.join(f.strip() for f in fields));item.setData(Qt.UserRole,appid);self.items.addItem(item)
        self.status.setText(f'{self.items.count()} results. Select an app for actions.')
    def search(self):self.request({'action':'flatpak-search','query':self.query.text()},self.loaded)
    def selected(self):
        item=self.items.currentItem();return item.data(Qt.UserRole) if item else None
    def confirm(self,title,text):return QMessageBox.question(self,title,text,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes
    def enable(self):
        if self.confirm('Enable Flathub','Add the official Flathub repository for your user?'):self.request({'action':'flatpak-enable'})
    def install(self):
        appid=self.selected()
        if appid and self.confirm('Install app','Download and install '+appid+' from Flathub?'):self.request({'action':'flatpak-install','id':appid})
    def remove(self):
        appid=self.selected()
        if appid and self.confirm('Remove app','Uninstall '+appid+' for your user? App data will be retained.'):self.request({'action':'flatpak-remove','id':appid})
    def update(self):
        if self.confirm('Update applications','Download and apply all available user Flatpak updates?'):self.request({'action':'flatpak-update'})
    def launch(self):
        if self.selected():self.d.app_support.launch_flatpak(self.selected())

class Accessibility(QWidget):
    app_name='Accessibility'
    def __init__(self,d):
        super().__init__();self.d=d;v=QVBoxLayout(self);v.addWidget(QLabel('Accessibility · built-in Macaque windows'))
        self.size=QSpinBox();self.size.setRange(11,24);self.size.setValue(d.state.get('text_size',13));self.size.setSuffix(' px');v.addWidget(QLabel('Interface text size'));v.addWidget(self.size)
        self.contrast=QCheckBox('High contrast');self.contrast.setChecked(d.state.get('high_contrast',False));v.addWidget(self.contrast)
        self.motion=QCheckBox('Reduce motion');self.motion.setChecked(d.state.get('reduce_motion',False));v.addWidget(self.motion)
        apply=QPushButton('Apply accessibility settings');apply.clicked.connect(self.apply);v.addWidget(apply)
        text=QLabel('Keyboard navigation: Tab / Shift+Tab moves focus; Space activates buttons; F6 searches; Ctrl+, opens Settings; Ctrl+W closes an app. High contrast adds stronger focus borders. Reduced motion disables window effects and shows a still welcome card for the full intro duration. Native apps have their own accessibility settings.');text.setWordWrap(True);v.addWidget(text);v.addStretch()
    def apply(self):
        for k,v in [('text_size',self.size.value()),('high_contrast',self.contrast.isChecked()),('reduce_motion',self.motion.isChecked())]:self.d.set_preference(k,v)
        self.d.apply_ui_theme();self.d.top_bar.update_layout()

class LockSleep(ServicesPanel):
    app_name='Lock & Sleep'
    def __init__(self,d):
        super().__init__(d);self.status.setText('Secure locking uses swaylock and your account password. Suspend is requested only after swaylock confirms that the lock is established. Lid handling belongs to systemd-logind.')
        for title,fn in [('Lock now',lambda:self.d.launch('Battery & Power').content.lock()),('Lock then suspend…',self.suspend),('Inspect lock and lid policy',lambda:self.request({'action':'lock-status'})),('Idle and brightness settings',lambda:self.d.launch('Battery & Power'))]:b=QPushButton(title);b.clicked.connect(fn);self.v.addWidget(b)
        self.v.addWidget(QLabel('After waking, authenticate to unlock. Actual wake and lid behavior needs testing on your laptop.'));self.v.addStretch()
    def suspend(self):
        if QMessageBox.question(self,'Suspend','Lock the session and suspend now?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.request({'action':'suspend'})

class SetupAssistant(ServicesPanel):
    app_name='Setup Assistant'
    def __init__(self,d):
        super().__init__(d);self.status.setText('Welcome! Choose your desktop preferences, connect to Wi-Fi, and review the essentials. Each system change has its own Apply action.')
        self.pages=QStackedWidget();self.v.addWidget(self.pages,1)
        appearance=QWidget();a=QVBoxLayout(appearance);a.addWidget(QLabel('1 · Appearance and sound'));self.mode=QComboBox();self.mode.addItems(['light','dark']);self.mode.setCurrentText(d.state.get('mode','light'));a.addWidget(self.mode);self.sounds=QCheckBox('Enable desktop sounds');self.sounds.setChecked(d.state.get('sounds_enabled',True));a.addWidget(self.sounds);b=QPushButton('Apply appearance and sound');b.clicked.connect(self.appearance);a.addWidget(b);a.addStretch();self.pages.addWidget(appearance)
        network=QWidget();a=QVBoxLayout(network);a.addWidget(QLabel('2 · Connect and set the time'));b=QPushButton('Wi-Fi and network…');b.clicked.connect(lambda:d.launch('Network'));a.addWidget(b);self.zones=QComboBox();self.zones.setEditable(True);a.addWidget(self.zones);b=QPushButton('Load system time zones');b.clicked.connect(lambda:self.request({'action':'zones'},lambda data:self.zones.addItems(data['zones'])));a.addWidget(b);b=QPushButton('Apply system time zone');b.clicked.connect(lambda:self.request({'action':'timezone','zone':self.zones.currentText()}));a.addWidget(b);a.addStretch();self.pages.addWidget(network)
        review=QWidget();a=QVBoxLayout(review);a.addWidget(QLabel('3 · Make it yours'))
        for name in ['Accessibility','Lock & Sleep','Software Center','Backup & Recovery']:
            b=QPushButton(name+'…');b.clicked.connect(lambda _,n=name:d.launch(n));a.addWidget(b)
        a.addStretch();self.pages.addWidget(review);row=QHBoxLayout();self.v.addLayout(row);self.back=QPushButton('Back');self.back.clicked.connect(lambda:self.page(-1));row.addWidget(self.back);self.next=QPushButton('Next');self.next.clicked.connect(self.advance);row.addWidget(self.next);self.page(0)
    def appearance(self):self.d.set_mode(self.mode.currentText());self.d.set_preference('sounds_enabled',self.sounds.isChecked())
    def page(self,delta):self.pages.setCurrentIndex(max(0,min(2,self.pages.currentIndex()+delta)));self.back.setEnabled(self.pages.currentIndex()>0);self.next.setText('Finish' if self.pages.currentIndex()==2 else 'Next')
    def advance(self):
        if self.job:return
        if self.pages.currentIndex()<2:self.page(1);return
        self.d.set_preference('setup_completed',True);self.next.setEnabled(False);self.status.setText('Setup complete. You can reopen this assistant from the monkey menu.');self.d.launch('Welcome Center')
