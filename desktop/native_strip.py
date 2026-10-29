"""Load the real C++ ControlStrip into the existing PySide6 QApplication."""
import ctypes,shutil,subprocess,re,json
from pathlib import Path
from PySide6.QtCore import QTimer, QSettings, qVersion
from PySide6.QtWidgets import QWidget
from shiboken6 import getCppPointer, wrapInstance

class NativeStrip:
    def __init__(self, desktop):
        self.desktop=desktop
        # Separate preferences prevent prototype edits affecting the standalone strip.
        target=QSettings('MacaqueOS','ClassicControlStripDesktop')
        source=QSettings('MacaqueOS','ClassicControlStrip')
        if not target.contains('embeddingInitialized'):
            for key in source.allKeys(): target.setValue(key,source.value(key))
            target.setValue('embeddingInitialized',True); target.sync()
        self.lib=ctypes.CDLL(str(Path(__file__).parent/'native/libclassic-strip-embedded.so'))
        self.lib.classic_strip_qt_version.restype=ctypes.c_char_p
        compiled=self.lib.classic_strip_qt_version().decode()
        parts=lambda v:tuple(int(x) for x in v.split('.')[:3])
        if parts(qVersion()) < parts(compiled):
            raise RuntimeError(f'Qt runtime {qVersion()} is older than compiled Qt {compiled}. Update PySide6 or rebuild with an older Qt.')
        self.lib.classic_strip_create.argtypes=[ctypes.c_void_p]
        self.lib.classic_strip_create.restype=ctypes.c_void_p
        self.lib.classic_strip_set_theme.argtypes=[ctypes.c_void_p,ctypes.c_int];self.lib.classic_strip_set_theme.restype=None
        self.lib.classic_strip_theme.argtypes=[ctypes.c_void_p];self.lib.classic_strip_theme.restype=ctypes.c_int
        self.lib.classic_strip_read_volume.restype=ctypes.c_int
        self.lib.classic_strip_write_volume.argtypes=[ctypes.c_int];self.lib.classic_strip_write_volume.restype=None
        self.lib.classic_strip_take_request.argtypes=[];self.lib.classic_strip_take_request.restype=ctypes.c_char_p
        self.widget=None; self.create()
        self.timer=QTimer(desktop); self.timer.timeout.connect(self.check_restart); self.timer.start(150)
    def create(self):
        pointer=self.lib.classic_strip_create(getCppPointer(self.desktop.area.viewport())[0])
        if not pointer:raise RuntimeError('Native strip creation failed')
        self.widget=wrapInstance(pointer,QWidget)
        if self.desktop.state.get("sync_strip",True):self.apply_theme(self.desktop.state.get("mode","light"))
    def show(self):self.widget.show();self.widget.raise_()
    def check_restart(self):
        self.dispatch_requests()
        if self.widget.property('restartRequested'):
            self.widget.hide(); self.widget.deleteLater(); self.create(); self.desktop.strip=self.widget

    def apply_theme(self,mode):self.lib.classic_strip_set_theme(getCppPointer(self.widget)[0],2 if mode=='dark' else 0)
    def theme_id(self):return self.lib.classic_strip_theme(getCppPointer(self.widget)[0])
    @staticmethod
    def has_audio_backend():return bool(shutil.which('wpctl') or shutil.which('pactl'))
    def read_volume(self):
        command=['wpctl','get-volume','@DEFAULT_AUDIO_SINK@'] if shutil.which('wpctl') else ['pactl','get-sink-volume','@DEFAULT_SINK@']
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=2)
            if result.returncode:return None
            match=re.search(r'Volume:\s*([0-9.]+)',result.stdout) if command[0]=='wpctl' else re.search(r'(\d+)%',result.stdout)
            if not match:return None
            return max(0,min(100,round(float(match[1])*(100 if command[0]=='wpctl' else 1))))
        except (OSError,ValueError,subprocess.TimeoutExpired):return None
    def write_volume(self,value):self.lib.classic_strip_write_volume(max(0,min(100,int(value))))

    def dispatch_requests(self):
        for _ in range(30):
            raw=self.lib.classic_strip_take_request()
            if not raw:break
            try:
                event=json.loads(raw.decode('utf-8'))
                self.desktop.handle_strip_request(event.get('program',''),event.get('args',[]))
            except (ValueError,TypeError,UnicodeError) as error:self.desktop.error(error)
