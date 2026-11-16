"""Bundled MIT-licensed classic chrome font, with readable system fallbacks."""
from pathlib import Path
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
FONT_DIR=Path(__file__).parent/'fonts/chicago-kare'

def family(state):
    app=QApplication.instance()
    if app is None:return 'DejaVu Sans'
    loaded=app.property('macaqueClassicFont')
    if loaded is None:
        font_id=QFontDatabase.addApplicationFont(str(FONT_DIR/'ChicagoKare-Regular.ttf'))
        families=QFontDatabase.applicationFontFamilies(font_id) if font_id>=0 else []
        loaded=families[0] if families else 'DejaVu Sans';app.setProperty('macaqueClassicFont',loaded)
    return loaded if state.get('interface_font','Classic')=='Classic' else 'DejaVu Sans'

def chrome_stylesheet(state):
    name=family(state)
    weight='normal' if name!='DejaVu Sans' else 'bold'
    size=state.get('text_size',13)+(3 if name!='DejaVu Sans' else 0)
    return f'''\nQMenu,QLabel#titleCaption,QToolButton#desktopFileIcon {{font-size:{size}px;font-family:"{name}","DejaVu Sans";}}
QLabel#titleCaption {{font-weight:{weight};}}
'''

def license_text():return (FONT_DIR/'LICENSE').read_text()
