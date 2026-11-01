#!/usr/bin/env python3
"""Run project checks with the same Python/PySide6 environment as the desktop."""
import os,subprocess,sys,compileall
from pathlib import Path
root=Path(__file__).resolve().parent
env=dict(os.environ,QT_QPA_PLATFORM='offscreen',MACAQUE_SILENT='1')
checks=['test_desktop.py','test_update.py','test_internal.py','test_expansion.py','test_creative.py','test_modern.py','test_sounds.py','test_search_backup.py','test_app_support.py','test_downloads.py','test_big_update.py','test_publish.py','test_motion.py','test_context.py','test_installer.py','test_menu_compat.py','test_terminal_swap_ui.py','test_terminal_pty.py','test_laptop.py','test_system_services.py','test_system_panels.py','test_wayland.py']
if not compileall.compile_dir(root,quiet=1):sys.exit(1)
for name in checks:
 print('\nChecking '+name,flush=True)
 result=subprocess.run([sys.executable,str(root/name)],cwd=root,env=env,timeout=90)
 if result.returncode:sys.exit(result.returncode)
print('\nAll project checks passed. See STATUS.md for unverified hardware/integration features.')
