"""Headless regression: bottom-edge drawer survives a simulated restart."""
import os,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['MACAQUE_SILENT']='1'
from PySide6.QtWidgets import QApplication,QMainWindow,QMdiArea,QWidget
from desktop_tabs import DesktopTabs
from pathlib import Path
app=QApplication.instance() or QApplication([])
class Fake(QWidget):
    def __init__(self,base):
        super().__init__()
        self.state={};self.path=Path(base)/'state.json'
        self.area=QMdiArea();self.workspace=0;self.strip=None
    def persist(self):
        import json
        self.path.write_text(json.dumps(self.state))
    def colors(self):return {'title':'#eeeeee','text':'#111111','stripe':'#555555'}
with tempfile.TemporaryDirectory() as base:
    d=Fake(base);tabs=DesktopTabs(d)
    class Window(QWidget):
        content=None
    # Test serializable application tabs without requiring full desktop startup.
    w=Window();w.setWindowTitle('Calculator');w.content=QWidget();w.setProperty('workspace',0)
    tabs.records[w]={'open':False}
    tabs.bar.addTab('Calculator');tabs.bar.setTabData(0,w)
    # The descriptor deliberately rejects unknown content and preserves known titles.
    tabs.save()
    assert d.state['bottom_drawer_tabs']==[{'kind':'app','value':'Calculator','workspace':0}]
    tabs.shutdown()
print('PASS: bottom drawer app serialization and shutdown persistence')
