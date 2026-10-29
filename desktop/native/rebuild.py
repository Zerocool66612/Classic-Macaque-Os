"""Optional local rebuild: needs g++, pkg-config and Qt6 Widgets development headers."""
from pathlib import Path
import subprocess,sys,shlex
import PySide6
root=Path(__file__).parent
subprocess.run([sys.executable,str(root/'prepare.py')],check=True)
try:
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','Qt6Widgets'],text=True))
except (OSError,subprocess.CalledProcessError):
    raise SystemExit('Install g++, pkg-config, and qt6-base-dev first. On Ubuntu: sudo apt install g++ pkg-config qt6-base-dev')
qtlib=Path(PySide6.__file__).parent/'Qt/lib'
subprocess.run(['g++','-std=c++17','-shared','-fPIC','-O2',*flags,str(root/'embedded-strip.cpp'),'-L',str(qtlib),'-l:libQt6Widgets.so.6','-l:libQt6Gui.so.6','-l:libQt6Core.so.6','-o',str(root/'libclassic-strip-embedded.so')],check=True)
print('Native strip rebuilt. Run desktop.py with this same Python environment.')
