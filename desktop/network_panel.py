"""Wi-Fi scanning in the desktop; credentials handled by nmcli's own PTY prompt."""
import shutil
from PySide6.QtCore import QProcess,QProcessEnvironment,QTimer,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTreeWidget,QTreeWidgetItem,QInputDialog
from laptop_support import split_fields
class Network(QWidget):
    app_name='Network'
    def __init__(self,d):
        super().__init__();self.d=d;self.job=None;layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Wi-Fi & Network'))
        self.status=QLabel('');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.list=QTreeWidget();self.list.setHeaderLabels(['Network','Signal','Security','Connected']);self.list.setRootIsDecorated(False);layout.addWidget(self.list)
        row=QHBoxLayout();layout.addLayout(row)
        for title,fn in [('Scan',self.refresh),('Connect',self.connect_selected),('Hidden network',self.hidden),('Wi-Fi On',lambda:self.command(['radio','wifi','on'])),('Wi-Fi Off',lambda:self.command(['radio','wifi','off']))]:
            b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
        layout.addWidget(QLabel('Connect opens a Macaque Terminal for the Wi-Fi password.\nPasswords go directly to NetworkManager; this app does not store them.'))
        self.list.itemDoubleClicked.connect(lambda *_:self.connect_selected());self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(20000);self.refresh()
    def command(self,args,scan=False):
        if self.job is not None:return
        if not shutil.which('nmcli'):self.status.setText('NetworkManager tools are missing. Rebuild with network-manager installed.');return
        self.status.setText('Scanning Wi-Fi…' if scan else 'Updating Wi-Fi…');p=QProcess(self);self.job=p
        env=QProcessEnvironment.systemEnvironment();env.insert('LC_ALL','C');p.setProcessEnvironment(env)
        def finish(code,*_):
            output=bytes(p.readAllStandardOutput()).decode(errors='replace');error=bytes(p.readAllStandardError()).decode(errors='replace');self.job=None
            if code:self.status.setText(error.strip() or 'NetworkManager could not complete the request. Check airplane mode and the Wi-Fi hardware switch.')
            elif scan:
                self.list.clear()
                for line in output.splitlines():
                    f=split_fields(line)
                    if len(f)!=4 or not f[0]:continue
                    item=QTreeWidgetItem([f[0],f[1]+'%',f[2] or 'Open','Yes' if f[3]=='*' else '']);item.setData(0,Qt.UserRole,f[0]);self.list.addTopLevelItem(item)
                self.status.setText('Select a network and click Connect.' if self.list.topLevelItemCount() else 'No networks found. Turn Wi-Fi on, check airplane mode, then scan. The adapter may need a driver/firmware.')
                self.list.resizeColumnToContents(0)
            else:self.refresh()
            p.deleteLater()
        p.finished.connect(finish)
        def failed(*_):
            if self.job is p:self.job=None;self.status.setText('Unable to start nmcli: '+p.errorString());p.deleteLater()
        p.errorOccurred.connect(failed);p.start('nmcli',['--wait','15',*args]);QTimer.singleShot(20000,p,lambda:p.kill() if p.state()!=QProcess.NotRunning else None)
    def refresh(self):self.command(['--terse','--escape','yes','--fields','SSID,SIGNAL,SECURITY,IN-USE','device','wifi','list','--rescan','yes'],True)
    def connect_selected(self):
        item=self.list.currentItem()
        if item:self.connect_ssid(item.data(0,Qt.UserRole))
        else:self.status.setText('Select a Wi-Fi network first.')
    def hidden(self):
        ssid,ok=QInputDialog.getText(self,'Hidden Wi-Fi','Network name (SSID):')
        if ok and ssid:self.connect_ssid(ssid,True)
    def connect_ssid(self,ssid,hidden=False):
        from terminal_app import Terminal
        args=['nmcli','--ask','--wait','60','device','wifi','connect',ssid]
        if hidden:args+=['hidden','yes']
        panel=Terminal(self.d,command=args);self.d.window('Connect to Wi-Fi',panel,(900,560));panel.view.setFocus();self.status.setText('Complete the connection in Terminal, then click Scan. NetworkManager remembers successful connections.')
    def can_close(self):
        self.timer.stop()
        if self.job:self.job.kill()
        return True
