"""Restore the user's last Control Strip volume once PipeWire is available."""
import shutil
import subprocess
import time
from PySide6.QtCore import QSettings

def saved_volume():
    value=QSettings('MacaqueOS','ClassicControlStripDesktop').value('savedSystemVolume',None)
    try:
        if value is None:return None
        number=int(value)
        return number if 0<=number<=100 else None
    except (TypeError,ValueError):
        return None

def restore(tries=20,delay=0.5):
    volume=saved_volume()
    if volume is None:return False
    if shutil.which('wpctl'):
        command=['wpctl','set-volume','@DEFAULT_AUDIO_SINK@',str(volume)+'%']
    elif shutil.which('pactl'):
        command=['pactl','set-sink-volume','@DEFAULT_SINK@',str(volume)+'%']
    else:return False
    for attempt in range(tries):
        try:
            result=subprocess.run(command,timeout=3,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if result.returncode==0:return True
        except (OSError,subprocess.TimeoutExpired):
            pass
        if attempt+1<tries:time.sleep(delay)
    return False

if __name__=='__main__':
    restore()
