"""Explicit, live-media-only launcher. Disk operations belong to Calamares."""
import os,subprocess
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer
from shiboken6 import isValid

def installer_available():
    try:
        return (os.environ.get('MACAQUE_NATIVE_SESSION')=='1' and Path('/etc/macaque-live').is_file() and 'boot=live' in Path('/proc/cmdline').read_text().split() and Path('/run/live/medium/live/filesystem.squashfs').is_file() and Path('/usr/bin/calamares').is_file())
    except OSError:return False

class InstallerSupport:
    def installer_busy(self):
        p=getattr(self,'installer_process',None)
        screen=getattr(self,'installer_screen',None)
        return (p is not None and p.poll() is None) or (screen is not None and isValid(screen) and screen.content.busy)
    def launch_installer(self):
        if not installer_available():return self.text_window('Installer unavailable','Boot the Macaque installer ISO first.')
        from install_preparation import InstallScreen
        screen=getattr(self,'installer_screen',None)
        if screen is None or not isValid(screen):
            screen=InstallScreen(self);self.installer_screen=screen
        elif not screen.content.busy:screen.content.refresh()
        screen.setGeometry(self.screen().geometry());screen.showFullScreen();screen.raise_();screen.activateWindow();return screen
    def launch_installer_wizard(self):
        if not installer_available():return self.text_window('Installer unavailable','Boot the Macaque installer ISO to install the system. This option is unavailable in the normal desktop prototype.')
        if self.installer_busy():return self.text_window('Installer running','Use Alt+Tab to switch to the installer. Finish or cancel there before ending this session.')
        screen=getattr(self,'installer_screen',None)
        parent=screen if screen is not None and isValid(screen) and screen.isVisible() else self
        answer=QMessageBox.question(parent,'Install Macaque Classic','Open the disk installation wizard?\n\nYou can review and cancel before applying changes. Installation can erase data on the disk you select.\n\nFor this preview, test with an empty virtual disk first.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if answer!=QMessageBox.Yes:return
        env=dict(os.environ)
        for key in ['QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','LD_LIBRARY_PATH','PYTHONPATH']:env.pop(key,None)
        # All live installations use the validated Wayland launcher, including
        # desktops restored from older preferences without the session marker.
        command=['/usr/bin/sudo','-n','--','/usr/local/libexec/macaque-wayland-installer',os.environ.get('WAYLAND_DISPLAY','')]
        try:self.installer_process=subprocess.Popen(command,env=env)
        except OSError as ex:self.error(ex);return
        if screen is not None and isValid(screen):screen.hide()
        self.installer_watch=QTimer(self)
        def check():
            code=self.installer_process.poll()
            if code is None:return
            self.installer_watch.stop()
            if code!=0:
                status=self.launch('Installer Status')
                QMessageBox.warning(self,'Installer stopped unexpectedly',
                    'The installer exited before completion (code '+str(code)+'). No successful installation is confirmed.\n\n'
                    'Installer Status has opened with the recorded error log. '
                    'Please copy or photograph the final error lines before retrying.')
        self.installer_watch.timeout.connect(check);self.installer_watch.start(1000)
