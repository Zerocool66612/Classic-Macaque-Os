"""Macaque light and dark palettes, applied to all included applications."""
LIGHT={'window':'#d9dcd9','panel':'#e6e9e6','base':'#fafcf9','text':'#17241f','muted':'#5f7068','border':'#75847c','edge':'#ffffff','title':'#d2d8d2','stripe':'#a8b5ab','sticky':'#fff0ae','sticky_text':'#493e20','display':'#e0ecd9'}
DARK={'window':'#292f33','panel':'#343c41','base':'#1c2327','text':'#e7efea','muted':'#a4b5ad','border':'#526269','edge':'#596a70','title':'#323d42','stripe':'#495b61','sticky':'#4b452b','sticky_text':'#f7ebba','display':'#253a35'}
def colors(mode):return dict(DARK if mode=='dark' else LIGHT)
def stylesheet(mode,accent='#287f70'):
 c=colors(mode)
 return f'''
 QWidget {{ font-family:"DejaVu Sans";font-size:13px;color:{c['text']}; }}
 QDialog,QMessageBox,QWidget#classicWindowFrame {{background:{c['window']};}}
 QWidget#classicWindowFrame {{border:1px solid {c['border']};}}
 QLabel#titleCaption {{font-weight:bold;background:{c['title']};color:{c['text']};padding:1px 10px;}}
 QPushButton {{background:{c['panel']};color:{c['text']};border-top:2px solid {c['edge']};border-left:2px solid {c['edge']};border-right:2px solid {c['border']};border-bottom:2px solid {c['border']};padding:5px 10px;}}
 QPushButton:pressed {{background:{c['title']};border:2px inset {c['border']};}}
 QPushButton:disabled {{color:{c['muted']};}}
 QToolButton {{background:{c['panel']};color:{c['text']};padding:5px;border:1px solid {c['border']};}}
 QLineEdit,QTextEdit,QPlainTextEdit,QListWidget,QTreeWidget,QComboBox,QSpinBox {{background:{c['base']};color:{c['text']};border:1px solid {c['border']};selection-background-color:{accent};selection-color:#fff;}}
 QTextEdit#stickyEditor {{background:{c['sticky']};color:{c['sticky_text']};border:0;}}
 QLineEdit#calculatorDisplay {{font-size:22px;background:{c['display']};color:{c['text']};padding:8px;}}
 QHeaderView::section {{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};padding:4px;}}
 QMenu {{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};padding:4px;}}
 QMenu::item {{padding:6px 26px 6px 13px;}} QMenu::item:selected {{background:{accent};color:#fff;}} QMenu::item:disabled {{color:{c['muted']};}}
 QMenu::separator {{height:1px;background:{c['border']};margin:4px;}}
 QTabWidget::pane {{border:1px solid {c['border']};background:{c['window']};}}
 QTabBar::tab {{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};padding:7px 12px;}}
 QTabBar::tab:selected {{background:{c['title']};}}
 QScrollBar {{background:{c['panel']};}} QScrollBar::handle {{background:{c['border']};min-height:18px;min-width:18px;}}
 QToolTip {{background:{c['panel']};color:{c['text']};border:1px solid {c['border']};padding:4px;}}
 QCalendarWidget QWidget {{background:{c['panel']};color:{c['text']};}}
 QCalendarWidget QAbstractItemView {{background:{c['base']};color:{c['text']};selection-background-color:{accent};selection-color:#fff;}}
 QCheckBox,QRadioButton,QLabel {{background:transparent;}}
 '''
