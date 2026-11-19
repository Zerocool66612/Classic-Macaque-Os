"""Read-only Classic system utilities. No privileged writes or shell commands."""
import os
import platform
import shutil
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QStorageInfo
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QLabel,QTextEdit,QPushButton,
    QTreeWidget,QTreeWidgetItem,QTabWidget,QHBoxLayout,QMessageBox,QComboBox,QCheckBox)

def safe_command(argv, timeout=3):
    if not shutil.which(argv[0]):
        return "Not available"
    try:
        result=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,check=False)
        return (result.stdout or result.stderr).strip()[:6000] or "No information"
    except (OSError,subprocess.TimeoutExpired):
        return "Unavailable"

def local_hardware():
    """Read current machine hardware, never a developer's target specifications."""
    cpu='Unknown processor'
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.lower().startswith(('model name','hardware','processor')) and ':' in line:
                candidate=line.split(':',1)[1].strip()
                if candidate and not candidate.isdigit():
                    cpu=candidate
                    break
    except OSError:
        pass
    if cpu=='Unknown processor':
        cpu=platform.processor() or cpu
    memory='Unavailable'
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'):
                memory=f"{int(line.split()[1])/1048576:.1f} GiB"
                break
    except (OSError,ValueError,IndexError):
        pass
    graphics='Unavailable'
    result=safe_command(['lspci','-nn'])
    if result not in ('Not available','Unavailable','No information'):
        devices=[]
        for line in result.splitlines():
            if any(tag in line.lower() for tag in ('vga compatible controller','3d controller','display controller')):
                devices.append(line.split(': ',1)[-1].strip())
        if devices:graphics='; '.join(devices)
    return {'processor':cpu,'memory':memory,'graphics':graphics,
            'architecture':platform.machine() or 'Unknown',
            'system':platform.system()+' '+platform.release()}

def hardware_summary():
    lines=["Macaque Classic System Profiler","",f"System: {platform.system()} {platform.release()}",
           f"Architecture: {platform.machine()}",f"Processor: {platform.processor() or 'Unknown'}",
           f"CPU threads: {os.cpu_count() or 'Unknown'}"]
    try:
        mem=next((line for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemTotal:")),None)
        if mem:lines.append("Memory: "+mem.split(":",1)[1].strip())
    except OSError:pass
    for title,argv in [("Graphics",["lspci","-nn"]),("Network",["nmcli","-t","-f","DEVICE,TYPE,STATE","device","status"])]:
        result=safe_command(argv)
        if title=="Graphics" and result!="Not available":
            result="\n".join(line for line in result.splitlines() if any(x in line.lower() for x in ("vga","display","3d controller"))) or "Unknown"
        lines.extend(["",title+":",result])
    return "\n".join(lines)

class SystemProfiler(QWidget):
    app_name="System Profiler"
    def __init__(self,d):
        super().__init__();layout=QVBoxLayout(self)
        layout.addWidget(QLabel("System Profiler · hardware and operating system information"))
        self.output=QTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output)
        b=QPushButton("Refresh");b.clicked.connect(self.refresh);layout.addWidget(b);self.refresh()
    def refresh(self):self.output.setPlainText(hardware_summary())

class ExtensionsManager(QWidget):
    app_name="Extensions Manager"
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self)
        layout.addWidget(QLabel("Classic desktop components · changes take effect immediately."))
        layout.addWidget(QLabel("System services are not disabled here; this protects boot and login."))
        for title,key,default in [
            ("Desktop sounds","sounds_enabled",True),
            ("Control Strip follows desktop theme","sync_strip",True),
            ("Low battery warnings","low_battery_warnings",True),
            ("Compact menu bar","compact_bar",True)]:
            check=QCheckBox(title);check.setChecked(bool(d.state.get(key,default)))
            check.toggled.connect(lambda checked,k=key:d.set_preference(k,checked))
            layout.addWidget(check)
        b=QPushButton("Open Recovery & Diagnostics");b.clicked.connect(lambda:d.launch("Recovery & Diagnostics"))
        layout.addWidget(b);layout.addStretch()

class DiskUtility(QWidget):
    app_name="Disk Utility"
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self)
        layout.addWidget(QLabel("Disk Utility · mounted volumes (read-only)"))
        self.tree=QTreeWidget();self.tree.setHeaderLabels(["Mount point","Filesystem","Capacity","Free"])
        layout.addWidget(self.tree)
        buttons=QHBoxLayout();layout.addLayout(buttons)
        for name,fn in [("Refresh",self.refresh),("Open Macaque HD",lambda:d.open_finder(d.disk.root))]:
            b=QPushButton(name);b.clicked.connect(fn);buttons.addWidget(b)
        layout.addWidget(QLabel("Partition formatting and filesystem repair are deliberately disabled until tested."))
        self.refresh()
    def refresh(self):
        self.tree.clear()
        for volume in QStorageInfo.mountedVolumes():
            if not volume.isValid() or not volume.isReady():continue
            fmt=lambda n:f"{n/(1024**3):.1f} GiB"
            self.tree.addTopLevelItem(QTreeWidgetItem([volume.rootPath(),
                bytes(volume.fileSystemType()).decode("utf-8","replace"),
                fmt(volume.bytesTotal()),fmt(volume.bytesAvailable())]))
        self.tree.resizeColumnToContents(0)
