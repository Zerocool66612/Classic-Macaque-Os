"""Offscreen smoke test for Macaque-themed file and confirmation dialogs."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QWidget,QMessageBox,QFileDialog
from PySide6.QtCore import Qt
from classic_dialogs import decorate
app=QApplication.instance() or QApplication([])
class Desktop(QWidget):
    state={'window_button_side':'Left'}
    def colors(self):return {'title':'#dedede','stripe':'#555555','text':'#222222'}
    def desktop_stylesheet(self):return 'QWidget {color:#222222;}'
d=Desktop()
for dialog in [QMessageBox(QMessageBox.Question,'Confirm','Proceed?',QMessageBox.Yes|QMessageBox.No,d),QFileDialog(d,'Select a package')]:
    decorate(dialog,d)
    assert dialog.windowFlags() & Qt.FramelessWindowHint
    assert dialog._macaque_title_bar.isVisible() is False # shown with parent
    assert dialog._macaque_title_bar.height()==31
    dialog.close()
print('PASS: themed Qt dialogs')
