import os,tempfile,sys,json
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
with tempfile.TemporaryDirectory() as tmp:
    os.environ['XDG_CONFIG_HOME']=str(Path(tmp)/'config')
    from PySide6.QtWidgets import QApplication,QFileDialog,QMessageBox,QMenu
    from PySide6.QtCore import Qt,QPoint,QTimer,QEvent,QCoreApplication
    from PySide6.QtTest import QTest
    import desktop
    from model import Disk,calculate
    from visuals import STYLE
    from applications import Finder,SimpleText,Sticky,Calculator,Puzzle,Sherlock,Trash
    import traceback
    errors=[]
    def hook(kind,value,tb):
        errors.append(str(value));traceback.print_exception(kind,value,tb)
    sys.excepthook=hook
    app=QApplication([]);app.setStyle('Fusion');app.setStyleSheet(STYLE);d=desktop.Desktop(Path(tmp)/'data');d.show();QTest.qWait(60)
    assert d.native_strip is not None,getattr(d,'strip_error','')
    assert d.top_bar.isVisible() and d.top_bar.testAttribute(Qt.WA_StyledBackground)
    root=d.disk.root
    # Real managed-disk workflow, protected system items and path boundaries.
    folder=d.disk.new_folder(root,'Work');text=folder/'Draft.txt';text.write_text('first draft')
    copy=d.disk.duplicate(text);assert copy.read_text()=='first draft'
    renamed=d.disk.rename(copy,'Second.txt');key=d.disk.trash_item(renamed);assert not renamed.exists()
    restored=d.disk.restore(key);assert restored.read_text()=='first draft'
    copy_elsewhere=d.disk.copy_to(restored,root/'Documents');assert copy_elsewhere.read_text()=='first draft'
    for operation in [lambda:d.disk.trash_item(root/'Applications'),lambda:d.disk.rename(text,'../escape'),lambda:d.disk.copy_to(folder,folder),lambda:d.disk.trash_item(Path(tmp)/'outside')]:
        try:operation();raise AssertionError('Expected managed-disk guard')
        except ValueError:pass
    # Desktop items appear and open through their double-click callbacks.
    on_desktop=d.disk.new_folder(root/'Desktop','My Folder');d.disk_changed.emit();assert len(d.desktop_extras)==1
    before=len(d.area.subWindowList());QTest.mouseDClick(d.desktop_extras[0],Qt.LeftButton);assert len(d.area.subWindowList())==before+1
    finder=d.active();assert isinstance(finder,Finder) and finder.path==on_desktop
    finder.go_up();assert finder.path==root/'Desktop';finder.toggle_view();assert finder.mode=='list'
    # Editor Save As, modified-state cancellation, and persistence.
    win=d.launch('Macaque Text');note=win.content;note.editor.setPlainText('Patient Zero notes\nClassic desktop project')
    saved=root/'Documents'/'Project.txt'
    with patch.object(QFileDialog,'getSaveFileName',return_value=(str(saved),'')):assert note.save()
    assert saved.read_text().startswith('Patient Zero') and not note.editor.document().isModified()
    note.editor.insertPlainText('Updated ')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Cancel):assert not win.close()
    assert win.isVisible()
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Save):assert win.close()
    assert saved.read_text().startswith('Updated ')
    sticky=d.launch('Macaque Notes');sticky.content.editor.setPlainText('Persistent yellow note');sticky.content.persist();sticky_key=sticky.content.key;sticky.close()
    d.change_appearance('color','#3c9195');d.change_appearance('pattern','Pinstripes');d.persist()
    state=json.loads(d.state_path.read_text());assert state['stickies'][sticky_key]=='Persistent yellow note' and state['pattern']=='Pinstripes'
    # Calculator allows math while refusing code execution.
    assert calculate('sqrt(81)+2**3')==17
    for expr in ['__import__("os")','(1).__class__','2**100000','[1,2]']:
        try:calculate(expr);raise AssertionError('Unsafe calculator expression accepted')
        except ValueError:pass
    calc=d.launch('Calculator').content;calc.input.setText('7*8');calc.equals();assert calc.input.text()=='56'
    # Search real saved notes; verify puzzle only moves adjacent tiles.
    search=d.launch('Macaque Search').content;search.input.setText('Project');search.search();assert search.results.count()==1
    puzzle=d.launch('Macaque Tiles').content;old=puzzle.tiles.copy();empty=old.index(0);adj=next(i for i in range(16) if puzzle.adjacent(i,empty));puzzle.move(adj);assert puzzle.tiles[empty]==old[adj] and puzzle.moves==1
    # Global application launcher actions must run without signal-argument errors.
    d.system_menu();apps=next(a.menu() for a in d.top_bar.system.actions() if a.text()=='Applications')
    apps.actions()[2].trigger();assert isinstance(d.active(),Calculator)
    w=d.area.activeSubWindow();height=w.height();w.shade();assert w.shaded and not w.content.isVisible();w.shade();assert not w.shaded and w.height()==height
    w.showMinimized();d.window_menu();next(a for a in d.top_bar.windows.actions() if a.data() is w).trigger();assert not w.isMinimized()
    # All the other app screens construct successfully.
    for name in ['Macaque Clips','Appearance','Date & Time','Help Center','About This Computer']:assert d.launch(name)
    assert d.control_panels();assert d.memory()
    # Emptying trash never touches restored documents.
    d.disk.trash_item(copy_elsewhere);d.disk.empty_trash();assert restored.exists() and not d.disk.trash_items()
    # Do not resurrect a deleted seeded welcome document after restart.
    welcome=root/'Documents'/'Welcome to Macaque.txt';d.disk.trash_item(welcome);Disk(d.base);assert not welcome.exists()
    # Exercise actual C++ strip collapse and expansion.
    strip=d.strip;original=strip.width();QTest.mouseClick(strip,Qt.LeftButton,pos=QPoint(10,15));assert strip.width()==24
    QTest.mouseClick(strip,Qt.LeftButton,pos=QPoint(10,15));assert strip.width()==original
    d.quitting=True;d.close();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
    assert not errors,errors
print('PASS: native strip; desktop/menu actions; file create/copy/rename/trash/restore; text save and cancel; notes/preferences persistence; calculator validation; search; puzzle; WindowShade; minimize/restore; app construction')
