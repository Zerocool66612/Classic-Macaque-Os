"""Explicit, live-media-only launcher. Disk operations belong to Calamares."""
import os,subprocess
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer

def installer_available():
    try:
        return (os.environ.get('MACAQUE_NATIVE_SESSION')=='1' and Path('/etc/macaque-live').is_file() and 'boot=live' in Path('/proc/cmdline').read_text().split() and Path('/run/live/medium/live/filesystem.squashfs').is_file() and Path('/usr/bin/calamares').is_file())
    except OSError:return False

class InstallerSupport:
    def installer_busy(self):
        p=getattr(self,'installer_process',None)
        return p is not None and p.poll() is None
    def launch_installer(self):
        if not installer_available():return self.text_window('Installer unavailable','Boot the Macaque installer ISO first.')
        from install_preparation import InstallPreparation
        for w in self.area.subWindowList():
            if isinstance(w.content,InstallPreparation):self.activate_window(w);return w
        return self.window('Install Preparation',InstallPreparation(self),(760,530))
    def launch_installer_wizard(self):
        if not installer_available():return self.text_window('Installer unavailable','Boot the Macaque installer ISO to install the system. This option is unavailable in the normal desktop prototype.')
        if self.installer_busy():return self.text_window('Installer running','Use Alt+Tab to switch to the installer. Finish or cancel there before ending this session.')
        answer=QMessageBox.question(self,'Install Macaque Classic','Open the disk installation wizard?\n\nYou can review and cancel before applying changes. Installation can erase data on the disk you select.\n\nFor this preview, test with an empty virtual disk first.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if answer!=QMessageBox.Yes:return
        env=dict(os.environ)
        for key in ['QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','LD_LIBRARY_PATH','PYTHONPATH']:env.pop(key,None)
        command=['/usr/bin/sudo','-n','--','/usr/local/libexec/macaque-wayland-installer',os.environ.get('WAYLAND_DISPLAY','')] if os.environ.get('MACAQUE_WAYLAND_SESSION')=='1' else ['/usr/bin/sudo','-n','--','/usr/bin/calamares']
        try:self.installer_process=subprocess.Popen(command,env=env)
        except OSError as ex:self.error(ex);return
        def check():
            if self.installer_process.poll() not in (None,0):self.text_window('Installer failed to start','See ~/.local/state/macaque/session.log for the error. No alternative disk commands were run.')
        QTimer.singleShot(1500,check)
