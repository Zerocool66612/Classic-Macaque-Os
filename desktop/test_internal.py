import os,tempfile,sys,traceback
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp);os.environ['XDG_CONFIG_HOME']=str(tmp/'config')
    from PySide6.QtWidgets import QApplication,QMenu
    from PySide6.QtCore import Qt,QTimer,QPoint,QCoreApplication,QEvent,QProcess
    from PySide6.QtGui import QDesktopServices,QPixmap,QColor
    from PySide6.QtTest import QTest
    import desktop
    from system_apps import AppHub,Sound,Network,Storage,Monitor,Display,ImageViewer,EmbeddedDialog
    from applications import Finder
    errors=[]
    def hook(kind,value,tb):errors.append(str(value));traceback.print_exception(kind,value,tb)
    sys.excepthook=hook
    app=QApplication([]);app.setStyle('Fusion');d=desktop.Desktop(tmp/'data');d.show();QTest.qWait(60)
    assert d.native_strip is not None,getattr(d,'strip_error','')
    def click_menu(index,text):
        def choose():
            menu=app.activePopupWidget()
            try:
                assert isinstance(menu,QMenu)
                next(a for a in menu.actions() if a.text()==text).trigger()
            except Exception as ex:errors.append(str(ex))
            finally:
                if menu:menu.close()
        QTimer.singleShot(25,choose);QTest.mouseClick(d.strip,Qt.LeftButton,pos=QPoint(24+43*index+18,15));QTest.qWait(230)
    with patch.object(QDesktopServices,'openUrl',side_effect=AssertionError('Host openUrl called')),patch.object(QProcess,'startDetached',side_effect=AssertionError('Host application launch called')):
        click_menu(2,'Home Folder');assert isinstance(d.active(),Finder) and d.active().path==Path.home() and not d.active().managed
        click_menu(0,'Display Settings');assert isinstance(d.active(),Display)
        click_menu(8,'Open App Viewer…');assert isinstance(d.active(),AppHub)
        for module,kind in [('kcm_pulseaudio',Sound),('kcm_kscreen',Display),('kcm_networkmanagement',Network)]:
            d.handle_strip_request('systemsettings',[module]);assert isinstance(d.active(),kind)
        d.handle_strip_request('filelight',[]);assert isinstance(d.active(),Storage)
        d.handle_strip_request('plasma-systemmonitor',[]);assert isinstance(d.active(),Monitor)
        d.handle_strip_request('xdg-open',['applications:/']);assert isinstance(d.active(),AppHub)
        d.open_data();assert isinstance(d.active(),Finder) and d.active().path==d.base
        previous=len(d.area.subWindowList());d.handle_strip_request('firefox',['https://example.com']);assert len(d.area.subWindowList())==previous+1 and 'No host program was launched' in d.active().toPlainText()
        image=tmp/'picture.png';pix=QPixmap(24,24);pix.fill(QColor('teal'));assert pix.save(str(image));d.open_document(image);assert isinstance(d.active(),ImageViewer)
        # Open actual native Preferences through its nested Customize menu.
        embedded=[]
        def close_embedded(attempt=0):
            hosts=[w for w in d.area.subWindowList() if isinstance(w.content,EmbeddedDialog)]
            if hosts:
                host=hosts[-1].content;embedded.append(True);assert not host.dialog.isWindow();assert host.dialog.parentWidget()==host;host.dialog.accept() if close_mode=='accept' else hosts[-1].close() if close_mode=='frame' else host.dialog.reject();return
            if attempt<35:QTimer.singleShot(50,lambda:close_embedded(attempt+1))
            else:errors.append('Embedded dialog never arrived')
        def customize():
            menu=app.activePopupWidget()
            try:
                def preferences():
                    nested=app.activePopupWidget()
                    try:
                        next(a for a in nested.actions() if a.text()=='Control Strip Preferences…').trigger();QTimer.singleShot(50,close_embedded)
                    except Exception as ex:errors.append(str(ex))
                    finally:nested.close()
                QTimer.singleShot(25,preferences);next(a for a in menu.actions() if a.text()=='Customize…').trigger()
            except Exception as ex:errors.append(str(ex))
            finally:menu.close()
        for close_mode in ('reject','accept','frame'):
            QTimer.singleShot(25,customize);QTest.mouseClick(d.strip,Qt.LeftButton,pos=QPoint(42,15));QTest.qWait(700)
        assert len(embedded)==3,errors
    # Only background audio commands may remain as detached native processes.
    code=(Path(__file__).parent/'native/embedded-strip.cpp').read_text()
    launches=[line for line in code.splitlines() if 'QProcess::startDetached' in line]
    assert len(launches)==2 and all('"wpctl"' in line or '"pactl"' in line for line in launches)
    assert 'QDesktopServices::openUrl' not in code
    assert 'QDirIterator it' not in code[code.index('QVector<DesktopApp> installedApps()'):code.index('void launchDesktopApp')]
    assert not errors,errors
    d.quitting=True;d.close();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
print('PASS: actual native strip folder/display/App Viewer clicks route internally; internal settings/apps and image viewer; no host GUI fallback; native preferences embedded with accept/reject lifecycle')
