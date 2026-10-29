import os,tempfile,json,sys,traceback
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp);os.environ['XDG_CONFIG_HOME']=str(tmp/'config')
    from PySide6.QtWidgets import QApplication,QMenu
    from PySide6.QtCore import QEvent,QCoreApplication
    from PySide6.QtTest import QTest
    from PySide6.QtGui import QPalette
    import desktop
    from model import Disk,APP_NAMES
    from chrome import CommandPalette
    from applications import SimpleText
    errors=[]
    def hook(kind,value,tb):errors.append(str(value));traceback.print_exception(kind,value,tb)
    sys.excepthook=hook
    base=tmp/'previous';old=base/'Macintosh HD'
    for folder in [old/'Documents',old/'Desktop',old/'Applications'/'SimpleText.app',old/'System Folder'/'Control Panels',base/'Trash']:folder.mkdir(parents=True,exist_ok=True)
    original=old/'Documents'/'Existing.txt';original.write_bytes(b'Existing document, unchanged.\n')
    (base/'.initialized').touch();(base/'Trash'/'saved-trash').write_text('recover me')
    (base/'trash.json').write_text(json.dumps({'saved-trash':{'name':'Restored.txt','original':'Documents/Restored.txt'}}))
    (base/'desktop-state.json').write_text(json.dumps({'stickies':{'mine':'Keep my note'},'scraps':['Keep my clip'],'recent':[str(original)],'mode':'dark','clock_24':True}))
    app=QApplication([]);app.setStyle('Fusion');d=desktop.Desktop(base);d.show();QTest.qWait(70)
    assert d.native_strip is not None,getattr(d,'strip_error','')
    assert d.disk.root.name=='Macaque HD' and not old.exists()
    assert (d.disk.root/'Documents/Existing.txt').read_bytes()==b'Existing document, unchanged.\n'
    assert d.recent==[str(d.disk.root/'Documents/Existing.txt')]
    assert (base/'desktop-state.before-0.6.json').exists()
    assert Disk(base).migrated_path(original)==str(d.disk.root/'Documents/Existing.txt')
    assert d.stickies['mine']=='Keep my note' and d.scraps==['Keep my clip']
    assert (d.disk.root/'Applications/Macaque Text.app').is_dir() and not(d.disk.root/'Applications/SimpleText.app').exists()
    assert d.disk.restore('saved-trash').read_text()=='recover me'
    assert d.native_strip.theme_id()==2
    assert app.palette().color(QPalette.Base).lightness()<app.palette().color(QPalette.Text).lightness()
    d.set_mode('light');assert d.native_strip.theme_id()==0
    d.set_preference('sync_strip',False);d.set_mode('dark');assert d.native_strip.theme_id()==0
    d.set_preference('sync_strip',True);assert d.native_strip.theme_id()==2
    d.quick_settings(d.top_bar.quick_menu)
    action=next(a for a in d.top_bar.quick_menu.actions() if a.text()=='Dark Mode');action.trigger();assert d.state['mode']=='light'
    more=next(a.menu() for a in d.top_bar.quick_menu.actions() if a.text()=='More Options');clock_menu=next(a.menu() for a in more.actions() if a.text()=='Clock');clock=next(a for a in clock_menu.actions() if a.text()=='24-hour Clock');clock.trigger();assert not d.state['clock_24']
    d.set_mode('dark');d.persist();saved=json.loads(d.state_path.read_text());assert saved['mode']=='dark' and saved['recent']==d.recent
    assert 'Finder' not in APP_NAMES and 'SimpleText' not in APP_NAMES and 'Sherlock' not in APP_NAMES
    palette=CommandPalette(d);palette.input.setText('Macaque Text');assert palette.results.count()==1;palette.activate();assert isinstance(d.active(),SimpleText)
    assert d.top_bar.buttons[0].text()=='' and not d.top_bar.buttons[0].icon().isNull()
    d.resize(500,650);QTest.qWait(30);d.top_bar.update_layout();assert d.top_bar.more.isVisible()
    assert d.top_bar.clock.geometry().right()<=d.top_bar.width()
    count=len(d.top_bar.more_menu.actions());d.top_bar.update_layout();assert len(d.top_bar.more_menu.actions())==count
    d.resize(1500,900);QTest.qWait(30);d.top_bar.update_layout();assert not d.top_bar.more.isVisible()
    d.network_menu(d.top_bar.network_menu);assert len(d.top_bar.network_menu.actions())>=3
    # Existing destination plus an old disk: recover the old tree without overwriting.
    collision=tmp/'collision';(collision/'Macaque HD/Documents').mkdir(parents=True);(collision/'Macaque HD/Documents/current.txt').write_text('current')
    (collision/'Macintosh HD/Documents').mkdir(parents=True);(collision/'Macintosh HD/Documents/older.txt').write_text('older')
    disk=Disk(collision)
    assert (disk.root/'Documents/current.txt').read_text()=='current'
    assert (disk.root/'Recovered previous disk/Documents/older.txt').read_text()=='older'
    assert Disk(collision).root==disk.root
    d.quitting=True;d.close();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
    assert not errors,errors
print('PASS: existing-data migration; app-name migration; recent paths and Trash; light/dark persistence; native strip theme sync; quick settings; command launcher; narrow/wide top bar; host network menu; collision recovery')
