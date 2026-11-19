"""Macaque-themed modal dialogs with in-app-style chrome (no host decorations)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QHBoxLayout,QLabel,QPushButton,QMessageBox,QFileDialog

def decorate(dialog, desktop):
    """Apply Macaque title chrome to a Qt dialog before exec()."""
    dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    dialog.setOption(QFileDialog.DontUseNativeDialog, True) if isinstance(dialog,QFileDialog) else None
    palette=desktop.colors()
    bar=QWidget(dialog);bar.setObjectName('macaqueDialogTitle')
    bar.setFixedHeight(31)
    row=QHBoxLayout(bar);row.setContentsMargins(8,2,8,2);row.setSpacing(5)
    from window_controls import WindowButton
    from decoration_settings import controls
    # WindowButton expects a desktop owner and uses the user's selected button theme.
    close=WindowButton(desktop,'Close',dialog.reject,bar)
    title=QLabel(dialog.windowTitle(),bar);title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet('font-weight:bold;border:0;background:transparent;')
    side=controls(desktop.state)['window_button_side']
    if side=='Left':
        row.addWidget(close);row.addStretch();row.addWidget(title);row.addStretch()
    else:
        row.addStretch();row.addWidget(title);row.addStretch();row.addWidget(close)
    bar.setStyleSheet('QWidget#macaqueDialogTitle {background:'+palette['title']+';border-bottom:1px solid '+palette['stripe']+';color:'+palette['text']+';}')
    layout=dialog.layout()
    if layout is not None:
        margins=layout.contentsMargins()
        layout.setContentsMargins(margins.left(),margins.top()+33,margins.right(),margins.bottom())
    bar.move(0,0)
    bar.resize(max(300,dialog.width()),31)
    dialog.resize(max(440,dialog.width()),dialog.height()+33)
    bar.raise_()
    dialog._macaque_title_bar=bar
    from theme import stylesheet as theme_stylesheet
    dialog.setStyleSheet(theme_stylesheet(desktop.state.get('mode','light')))
    return dialog

def question(desktop,title,message,default=QMessageBox.No):
    box=QMessageBox(QMessageBox.Question,title,message,QMessageBox.Yes|QMessageBox.No,desktop)
    box.setDefaultButton(default)
    decorate(box,desktop)
    return box.exec()

def file_name(desktop,title,directory,filter_text):
    dialog=QFileDialog(desktop,title,directory,filter_text)
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setAcceptMode(QFileDialog.AcceptOpen)
    decorate(dialog,desktop)
    return (dialog.selectedFiles()[0] if dialog.exec()==QFileDialog.Accepted and dialog.selectedFiles() else ''),''
