"""Classic Wi-Fi controls with private stdin-to-D-Bus credentials."""
import json,shutil
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTreeWidget,QTreeWidgetItem,QInputDialog,QLineEdit,QMessageBox,QTabWidget,QFormLayout,QDialog,QDialogButtonBox,QCheckBox,QComboBox
from laptop_support import split_fields
from system_tasks import Task
class WiFiDialog(QDialog):
    def __init__(self,parent,ssid='',security='wpa-psk',hidden=False):
        super().__init__(parent);self.setWindowTitle('Connect to Wi-Fi');form=QFormLayout(self)
        self.ssid=QLineEdit(ssid);self.ssid.setReadOnly(not hidden);form.addRow('Network name',self.ssid)
        self.security=QComboBox();self.security.addItem('WPA / WPA2 Personal','wpa-psk');self.security.addItem('WPA3 Personal','sae');self.security.addItem('Open network','open');self.security.setCurrentIndex(max(0,self.security.findData(security)));form.addRow('Security',self.security)
        self.password=QLineEdit();self.password.setEchoMode(QLineEdit.Password);form.addRow('Password',self.password)
        reveal=QCheckBox('Show password');reveal.toggled.connect(lambda v:self.password.setEchoMode(QLineEdit.Normal if v else QLineEdit.Password));form.addRow(reveal)
        self.security.currentIndexChanged.connect(lambda:self.password.setEnabled(self.security.currentData()!='open'));self.password.setEnabled(security!='open')
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Ok).setText('Connect');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)
        self.hidden=hidden
    def payload(self):return {'ssid':self.ssid.text(),'security':self.security.currentData(),'password':self.password.text(),'hidden':self.hidden}
class Network(QWidget):
    app_name='Network'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;layout=QVBoxLayout(self);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);layout.addWidget(self.status)
        tabs=QTabWidget();layout.addWidget(tabs);near=QWidget();n=QVBoxLayout(near);self.list=QTreeWidget();self.list.setHeaderLabels(['Network','Signal','Security','Connected','Adapter']);self.list.setRootIsDecorated(False);n.addWidget(self.list);row=QHBoxLayout();n.addLayout(row)
        for title,fn in [('Scan',self.refresh),('Connect',self.connect_selected),('Hidden…',self.hidden),('Wi-Fi On',lambda:self.command(['radio','wifi','on'])),('Wi-Fi Off',lambda:self.command(['radio','wifi','off']))]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        saved=QWidget();v=QVBoxLayout(saved);self.saved=QTreeWidget();self.saved.setHeaderLabels(['Saved connection','Active','Adapter']);v.addWidget(self.saved);row=QHBoxLayout();v.addLayout(row)
        for title,fn in [('Refresh',self.refresh_saved),('Connect',self.activate_saved),('Disconnect',self.disconnect_saved),('Forget…',self.forget_saved)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        tabs.addTab(near,'Nearby Wi-Fi');tabs.addTab(saved,'Saved Networks');tabs.currentChanged.connect(lambda i:self.refresh_saved() if i else self.refresh())
        note=QLabel('Passwords are sent directly to NetworkManager. Successful connections are remembered for your account. Enterprise/WEP networks need an advanced profile.');note.setWordWrap(True);layout.addWidget(note)
        self.list.itemDoubleClicked.connect(lambda *_:self.connect_selected());self.timer=QTimer(self);self.tabs=tabs;self.timer.timeout.connect(lambda:self.refresh_saved() if self.tabs.currentIndex() else self.refresh());self.timer.start(20000);self.refresh()
    def run(self,argv,callback,payload=None,timeout=25000):
        if self.job:return
        self.status.setText('Working…');task=Task(self,argv,payload,timeout);self.job=task
        def finished(ok,text):
            self.job=None
            if not ok:self.status.setText(text);return
            callback(text)
        task.done.connect(finished)
    def command(self,args,scan=False):
        if not shutil.which('nmcli'):self.status.setText('NetworkManager tools are missing.');return
        self.run(['nmcli','--wait','15',*args],self.scanned if scan else lambda text:(self.status.setText(text or 'Wi-Fi updated.'),self.refresh()))
    def scanned(self,text):
        self.list.clear()
        for line in text.splitlines():
            f=split_fields(line)
            if len(f) not in (4,5) or not f[0]:continue
            interface=f[4] if len(f)>4 else '';item=QTreeWidgetItem([f[0],f[1]+'%',f[2] or 'Open','Yes' if f[3]=='*' else '',interface]);item.setData(0,Qt.UserRole,(f[0],f[2],interface));self.list.addTopLevelItem(item)
        self.status.setText('Select a network and click Connect.' if self.list.topLevelItemCount() else 'No networks found. Check Wi-Fi, airplane mode and adapter firmware.');self.list.resizeColumnToContents(0)
    def refresh(self):self.command(['--terse','--escape','yes','--fields','SSID,SIGNAL,SECURITY,IN-USE,DEVICE','device','wifi','list','--rescan','yes'],True)
    def connect_selected(self):
        item=self.list.currentItem()
        if not item:self.status.setText('Select a Wi-Fi network first.');return
        ssid,security,interface=item.data(0,Qt.UserRole)
        if '802.1X' in security or 'WEP' in security or 'OWE' in security:self.status.setText('This security type needs an advanced connection profile.');return
        self.connect_dialog(ssid,'sae' if security=='WPA3' else 'wpa-psk' if 'WPA' in security else 'open',False,interface)
    def hidden(self):self.connect_dialog('', 'wpa-psk',True,'')
    def connect_dialog(self,ssid,security,hidden,interface):
        if self.job:return
        dialog=WiFiDialog(self,ssid,security,hidden)
        if dialog.exec()!=QDialog.Accepted:dialog.password.clear();dialog.deleteLater();return
        payload=dialog.payload();payload['interface']=interface;dialog.password.clear();dialog.deleteLater()
        from wifi_backend import validate
        try:validate(payload)
        except ValueError as ex:self.status.setText(str(ex));return
        self.run(Task.helper('wifi_backend.py'),lambda text:(self.status.setText(json.loads(text)['message']),QTimer.singleShot(1500,self.refresh)),payload,140000)
        payload=None
    def refresh_saved(self):
        self.run(['nmcli','--terse','--escape','yes','--fields','UUID,NAME,TYPE,ACTIVE,DEVICE','connection','show'],self.saved_result)
    def saved_result(self,text):
        self.saved.clear()
        for line in text.splitlines():
            f=split_fields(line)
            if len(f)==5 and f[2] in ('802-11-wireless','wifi'):
                item=QTreeWidgetItem([f[1],f[3],f[4]]);item.setData(0,Qt.UserRole,f[0]);self.saved.addTopLevelItem(item)
        self.status.setText('Saved Wi-Fi profiles. Forget removes the stored connection and password.')
    def saved_uuid(self):
        item=self.saved.currentItem();return item.data(0,Qt.UserRole) if item else None
    def activate_saved(self):
        uuid=self.saved_uuid()
        if uuid:self.run(['nmcli','--wait','60','connection','up','uuid',uuid],lambda text:(self.status.setText(text),self.refresh_saved()),timeout=70000)
    def disconnect_saved(self):
        uuid=self.saved_uuid()
        if uuid:self.run(['nmcli','connection','down','uuid',uuid],lambda text:(self.status.setText(text),self.refresh_saved()))
    def forget_saved(self):
        uuid=self.saved_uuid()
        if uuid and QMessageBox.question(self,'Forget network','Remove this saved connection and its password?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.run(['nmcli','connection','delete','uuid',uuid],lambda text:self.refresh_saved())
    def can_close(self):
        if self.job:
            self.status.setText('Wait for the current network request to finish before closing.');return False
        self.timer.stop();return True
