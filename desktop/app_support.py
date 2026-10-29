"""External-app integration. No silent launch on the host display."""
import os,re,json,shutil,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,QProcess,QProcessEnvironment,QTimer,QSize
from PySide6.QtWidgets import *
from creative_apps import child_environment
from visuals import icon
ID=re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_][A-Za-z0-9_-]*){2,}$')

def parse_flatpaks(text):
    apps={}
    for line in text.splitlines():
        columns=line.split('\t')
        if len(columns)>=2 and ID.fullmatch(columns[0]):apps[columns[0]]=columns[1].strip() or columns[0]
    return sorted(apps.items(),key=lambda pair:pair[1].casefold())

def flatpak_command(app_id,volume,env):
    if not ID.fullmatch(app_id):raise ValueError('Invalid Flatpak application ID.')
    if env.get('MACAQUE_NATIVE_SESSION')!='1' or not re.fullmatch(r':\d+(?:\.\d+)?',env.get('DISPLAY','')):raise ValueError('Start Macaque with bash run-creative.sh first.')
    # Flatpak handles its own Xauthority forwarding for the current DISPLAY.
    # Do not override XAUTHORITY to a host path inside the sandbox.
    return ['flatpak','run','--socket=x11','--nosocket=wayland','--env=GDK_BACKEND=x11','--env=QT_QPA_PLATFORM=xcb','--env=SDL_VIDEODRIVER=x11','--filesystem='+str(Path(volume).resolve()),app_id]

def emulator_preferences(kind,rom,disk,shared,ram):
    if kind not in ('BasiliskII','SheepShaver'):raise ValueError('Choose BasiliskII or SheepShaver.')
    paths=[Path(p).expanduser().resolve() for p in (rom,disk,shared)]
    if any('\n' in str(p) or '\r' in str(p) for p in paths):raise ValueError('Paths cannot contain line breaks.')
    rom,disk,shared=paths
    if not rom.is_file() or not disk.is_file():raise ValueError('Select an existing ROM and a bootable hard-disk image.')
    if rom==disk:raise ValueError('ROM and disk image must be different files.')
    if not shared.is_dir():raise ValueError('Shared folder is unavailable.')
    if not 8<=int(ram)<=512:raise ValueError('RAM must be between 8 and 512 MB.')
    lines=[f'rom {rom}',f'disk {disk}',f'extfs {shared}',f'ramsize {int(ram)*1024*1024}','screen win/1024/768','bootdrive 0','bootdriver 0','nogui true','nocdrom true','nosound false','frameskip 1']
    if kind=='BasiliskII':lines+=['modelid 14','cpu 4','fpu true']
    else:lines+=['nonet true','jit false']
    return '\n'.join(lines)+'\n'

class AppSupport:
    def __init__(self,d):self.d=d;self.running={};self.logs=[];self.installed={};self.install_process=None
    def session_ready(self):
        if os.environ.get('MACAQUE_NATIVE_SESSION')=='1':return True
        self.d.text_window('App Session required','Close this desktop and run bash run-app-session.sh.\n\nFirst-time setup: bash install-app-support.sh\n\nNative Flatpak and emulator windows run within the outer nested desktop. The regular prototype does not contain external application windows.');return False
    def spawn(self,key,command,env,cwd=None):
        old=self.running.get(key)
        if old and old.poll() is None:self.d.text_window('Already running',key+' is running. Use Alt+Tab inside the session.');return
        directory=self.d.base/'app-support-logs';directory.mkdir(exist_ok=True);name=re.sub(r'[^A-Za-z0-9_.-]','_',key)
        try:
            log=(directory/(name+'.log')).open('ab');self.logs.append(log);process=subprocess.Popen(command,env=env,cwd=cwd,stdout=log,stderr=subprocess.STDOUT);self.running[key]=process
        except OSError as ex:self.d.error(ex);return
        def check():
            if process.poll() is not None and process.returncode:self.d.text_window(key+' exited',f'Exit code: {process.returncode}\nLog: {directory/(name+".log")}\n\nNo host-display fallback was attempted. Compatibility is experimental.')
        QTimer.singleShot(2500,check)
    def launch_flatpak(self,app_id):
        if not self.session_ready():return
        if app_id not in self.installed:self.d.error('Refresh the Flatpak list and select an installed app.');return
        old=self.running.get('Flatpak '+app_id)
        if old and old.poll() is None:self.d.text_window('Already running','Use Alt+Tab inside the session to switch to this app.');return
        try:
            check=subprocess.run(['flatpak','ps','--columns=application'],capture_output=True,text=True,timeout=3)
            if check.returncode:raise OSError(check.stderr or 'Could not check existing Flatpak instances.')
            if app_id in {line.strip() for line in check.stdout.splitlines()}:self.d.text_window('Close the existing instance','Quit this Flatpak on your host desktop before launching it in Macaque.');return
            command=flatpak_command(app_id,self.d.disk.root,os.environ)
        except (ValueError,OSError,subprocess.TimeoutExpired) as ex:self.d.error(ex);return
        # Preserve normal Flatpak locations/configuration; only clear Qt's injected
        # library paths and force X11. Retain the nested session's private bus.
        env=child_environment(os.environ,Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')));self.spawn('Flatpak '+app_id,command,env)
    def launch_classic(self,config):
        if not self.session_ready():return
        kind=config.get('kind','BasiliskII');binary=config.get('binary','').strip() or shutil.which(kind) or shutil.which(kind.lower())
        if not binary or not Path(binary).is_file() or not os.access(binary,os.X_OK):self.d.error('Select an installed, executable emulator. No emulator is bundled.');return
        shared=self.d.disk.root/'Classic Shared';shared.mkdir(exist_ok=True)
        try:prefs=emulator_preferences(kind,config.get('rom',''),config.get('disk',''),shared,config.get('ram',64))
        except (ValueError,OSError) as ex:self.d.error(ex);return
        # One active guest per disk. Shut down its Mac OS before launching another.
        if any(k.startswith('Classic ') and p.poll() is None for k,p in self.running.items()):self.d.text_window('Classic guest is running','Shut down the current guest before starting another.');return
        directory=self.d.base/'classic-vm'/kind;directory.mkdir(parents=True,exist_ok=True);path=directory/'prefs';path.write_text(prefs)
        env=child_environment(os.environ,Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config')))
        self.spawn('Classic '+kind,[str(Path(binary).resolve()),'--config',str(path)],env,str(directory))
    def can_close(self):
        names=[name for name,p in self.running.items() if p.poll() is None]
        if self.install_process and self.install_process.state()!=QProcess.NotRunning:names.append('Flatpak installation')
        if names:QMessageBox.information(self.d,'Apps are still open','Save and quit these apps before closing Macaque:\n\n'+'\n'.join(names));return False
        return True

class FlatpakApps(QWidget):
    app_name='Flatpak Apps'
    def __init__(self,d):
        super().__init__();self.d=d;self.manager=d.app_support;layout=QVBoxLayout(self);layout.addWidget(QLabel('Native Linux · Flatpak Apps'));info=QLabel('Installed Flatpaks are discovered here. Launch in App Session to keep their windows inside the outer Macaque desktop. X11-capable apps only; each launch grants read/write access to Macaque HD.');info.setWordWrap(True);layout.addWidget(info);self.search=QLineEdit();self.search.setPlaceholderText('Filter installed Flatpak apps…');layout.addWidget(self.search);self.items=QListWidget();self.items.setIconSize(QSize(28,28));layout.addWidget(self.items,1);row=QHBoxLayout();layout.addLayout(row)
        self.refresh_button=QPushButton('Refresh');self.refresh_button.clicked.connect(self.refresh);row.addWidget(self.refresh_button);launch=QPushButton('Launch selected');launch.clicked.connect(self.launch);row.addWidget(launch);self.install_button=QPushButton('Install from file…');self.install_button.clicked.connect(self.install);row.addWidget(self.install_button);self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);self.output=QPlainTextEdit();self.output.setReadOnly(True);self.output.setMaximumHeight(110);self.output.document().setMaximumBlockCount(300);layout.addWidget(self.output);self.search.textChanged.connect(self.filter);self.items.itemActivated.connect(lambda _:self.launch());self.query_timeout=QTimer(self);self.query_timeout.setSingleShot(True);self.query_timeout.timeout.connect(self.timeout);self.query=QProcess(self);self.query.setProcessChannelMode(QProcess.MergedChannels);self.query.finished.connect(self.listed);self.query.errorOccurred.connect(lambda *a:self.status.setText(self.query.errorString()));self.refresh()
    def refresh(self):
        if self.query.state()!=QProcess.NotRunning:return
        if not shutil.which('flatpak'):self.status.setText('Flatpak is not installed. Run bash install-app-support.sh from this folder.');return
        self.status.setText('Reading installed apps…');self.query.start('flatpak',['list','--app','--columns=application:f,name:f']);self.query_timeout.start(8000)
    def timeout(self):
        if self.query.state()!=QProcess.NotRunning:self.query.kill();self.status.setText('Flatpak listing timed out; try Refresh.')
    def listed(self,code,status):
        self.query_timeout.stop()
        text=bytes(self.query.readAllStandardOutput()).decode(errors='replace')
        if code:self.status.setText('Could not list Flatpaks. '+text[:400]);return
        self.manager.installed=dict(parse_flatpaks(text));self.filter();self.status.setText(f'{len(self.manager.installed)} installed apps. No app permission overrides are saved permanently.')
    def filter(self,*args):
        self.items.clear();query=self.search.text().casefold()
        for app_id,name in sorted(self.manager.installed.items(),key=lambda p:p[1].casefold()):
            if query in (name+' '+app_id).casefold():item=QListWidgetItem(icon('apps'),name+' · '+app_id);item.setData(Qt.UserRole,app_id);self.items.addItem(item)
        if self.items.count():self.items.setCurrentRow(0)
    def launch(self):
        item=self.items.currentItem()
        if item:self.manager.launch_flatpak(item.data(Qt.UserRole))
    def install(self):
        if not shutil.which('flatpak'):self.status.setText('Run install-app-support.sh first.');return
        old=self.manager.install_process
        if old and old.state()!=QProcess.NotRunning:self.status.setText('An installation is already running.');return
        path,_=QFileDialog.getOpenFileName(self,'Select Flatpak reference or bundle',str(Path.home()/'Downloads'),'Flatpak files (*.flatpakref *.flatpak)')
        if path:self.install_path(path)
    def install_path(self,path):
        if not shutil.which('flatpak'):self.status.setText('Run install-app-support.sh first.');return
        old=self.manager.install_process
        if old and old.state()!=QProcess.NotRunning:self.status.setText('An installation is already running.');return
        path=str(Path(path).expanduser().resolve())
        if not Path(path).is_file() or Path(path).suffix.lower() not in ('.flatpakref','.flatpak'):self.status.setText('Choose an existing .flatpakref or .flatpak file.');return
        # The chosen file is one argv element; no command text is executed.
        process=QProcess(self);self.manager.install_process=process;process.setProcessChannelMode(QProcess.MergedChannels);process.readyReadStandardOutput.connect(lambda:self.output.appendPlainText(bytes(process.readAllStandardOutput()).decode(errors='replace')));process.finished.connect(self.installed);process.errorOccurred.connect(self.install_failed);self.install_button.setEnabled(False);self.status.setText('Installing for your user. This may download apps and runtimes.');process.start('flatpak',['install','--user','--assumeyes','--noninteractive',path])
    def install_failed(self,*args):
        p=self.manager.install_process;self.status.setText(p.errorString() if p else 'Installation failed to start.');self.install_button.setEnabled(True)
        if p and p.state()==QProcess.NotRunning:self.manager.install_process=None
    def installed(self,code,status):self.manager.install_process=None;self.install_button.setEnabled(True);self.status.setText('Installation completed.' if code==0 else 'Installation failed; see output.');self.refresh()
    def can_close(self):
        p=self.manager.install_process
        if p and p.state()!=QProcess.NotRunning:QMessageBox.information(self,'Installation is running','Wait for the Flatpak installation to finish.');return False
        if self.query.state()!=QProcess.NotRunning:self.query.kill();self.query.waitForFinished(1000)
        return True

class ClassicMacApps(QWidget):
    app_name='Classic Mac Apps'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);heading=QLabel('Classic Mac Apps · Emulator Setup');heading.setStyleSheet('font-size:20px;font-weight:bold');layout.addWidget(heading);text=QLabel('Basilisk II: 68k apps, compatible System 7 / Mac OS up to 8.1. SheepShaver: PowerPC apps, compatible Mac OS through 9.0.4. Standard SheepShaver does not run 9.2.2. Supply your emulator, ROM and bootable guest disk; these are not included.');text.setWordWrap(True);layout.addWidget(text);self.kind=QComboBox();self.kind.addItems(['BasiliskII','SheepShaver']);layout.addWidget(self.kind);self.fields={}
        for key,label in [('binary','Emulator executable / AppImage'),('rom','Compatible Mac ROM'),('disk','Bootable Mac hard-disk image')]:
            layout.addWidget(QLabel(label));row=QHBoxLayout();layout.addLayout(row);field=QLineEdit();self.fields[key]=field;row.addWidget(field);b=QPushButton('Browse…');b.clicked.connect(lambda checked=False,k=key:self.browse(k));row.addWidget(b)
        self.ram=QSpinBox();self.ram.setRange(8,512);self.ram.setSuffix(' MB RAM');layout.addWidget(self.ram);row=QHBoxLayout();layout.addLayout(row)
        for label,fn in [('Save setup',self.save),('Start Classic Mac',self.start),('Open shared folder',self.shared)]:b=QPushButton(label);b.clicked.connect(fn);row.addWidget(b)
        self.status=QLabel('Install or launch classic applications inside the guest Mac OS. Individual classic executables are not directly opened by this shell.');self.status.setWordWrap(True);layout.addWidget(self.status);layout.addStretch();config=d.state.get('classic_mac',{});self.kind.setCurrentText(config.get('kind','BasiliskII'));self.ram.setValue(config.get('ram',64))
        for key,field in self.fields.items():field.setText(config.get(key,''))
    def browse(self,key):
        path,_=QFileDialog.getOpenFileName(self,'Choose '+key,str(Path.home()))
        if path:self.fields[key].setText(path)
    def save(self):
        config={'kind':self.kind.currentText(),'ram':self.ram.value(),**{key:field.text().strip() for key,field in self.fields.items()}};self.d.state['classic_mac']=config;self.d.persist();self.status.setText('Setup saved. Shut down guest Mac OS normally; the disk image is writable. Keep a separate backup of it.');return config
    def start(self):self.d.app_support.launch_classic(self.save())
    def shared(self):path=self.d.disk.root/'Classic Shared';path.mkdir(exist_ok=True);self.d.open_finder(path)
