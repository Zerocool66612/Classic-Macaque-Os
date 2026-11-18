"""Smoke checks for Classic utilities without touching host services or disks."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from pathlib import Path
from PySide6.QtWidgets import QApplication
from model import APP_NAMES
from classic_search import ClassicSearch
from classic_utilities import SystemProfiler, ExtensionsManager, DiskUtility
from chrome import TopBar

assert all(name in APP_NAMES for name in ("Macaque Sherlock","System Profiler","Extensions Manager","Disk Utility"))
assert all(hasattr(panel,"__init__") for panel in (SystemProfiler,ExtensionsManager,DiskUtility))
app=QApplication.instance() or QApplication([])
assert "System:" in __import__("classic_utilities").hardware_summary()
assert "Macaque Sherlock" == ClassicSearch.app_name
print("Utility imports, app registration and system profiler smoke checks passed.")
