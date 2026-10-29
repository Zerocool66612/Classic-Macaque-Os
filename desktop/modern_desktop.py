"""Macaque-local desktop preferences, activity and window controls."""
import time,os
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,Slot
from PySide6.QtWidgets import *
from model import APP_NAMES
from creative_apps import CREATIVE_APPS

class NotificationCenter(QWidget):
    app_name='Notifications'
    def __init__(self,d):
        super().__init__();self.d=d;layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row);row.addWidget(QLabel('Macaque activity'));self.focus=QCheckBox('Do Not Disturb');self.focus.setChecked(d.state.get('do_not_disturb',False));self.focus.toggled.connect(lambda v:d.set_preference('do_not_disturb',v));d.preferences_changed.connect(self.sync_preference);row.addWidget(self.focus);self.items=QListWidget();self.items.setWordWrap(True);layout.addWidget(self.items);b=QPushButton('Clear activity');b.clicked.connect(self.clear);layout.addWidget(b);layout.addWidget(QLabel('Activity from this desktop only. Do Not Disturb hides Macaque banners.'));self.refresh()
    @Slot(str,object)
    def sync_preference(self,key,value):
        if key=='do_not_disturb':self.focus.setChecked(value)
    def refresh(self):
        self.items.clear()
        for item in reversed(self.d.state.get('notifications',[])):self.items.addItem(time.strftime('%b %d  %H:%M',time.localtime(item['time']))+' · '+item['title']+'\n'+item['message'])
        if not self.items.count():self.items.addItem('You are all caught up.')
    def clear(self):self.d.state['notifications']=[];self.d.state['unread_notifications']=0;self.d.persist();self.refresh();self.d.top_bar.refresh_status()

class Settings(QWidget):
    app_name='Settings'
    def __init__(self,d):
        super().__init__();self.d=d;self.checks={};d.preferences_changed.connect(self.sync_preference);layout=QVBoxLayout(self);heading=QLabel('Macaque Settings');heading.setStyleSheet('font-size:22px;font-weight:bold');layout.addWidget(heading);tabs=QTabWidget();layout.addWidget(tabs)
        general=QWidget();form=QVBoxLayout(general)
        self.check(form,'Start with Macaque HD open','startup_files',True);self.check(form,'Show Welcome Center at startup','startup_welcome',False);self.check(form,'Show About at startup','startup_about',False);self.check(form,'Reopen sticky notes at startup','startup_notes',True);self.check(form,'Center new windows','center_windows',False);self.check(form,'Show desktop file icons','desktop_icons',True);self.check(form,'Do Not Disturb','do_not_disturb',False)
        form.addWidget(QLabel('Interface density'));density=QComboBox();density.addItems(['Compact','Comfortable']);density.setCurrentText(d.state.get('ui_density','Compact'));density.currentTextChanged.connect(lambda v:self.save('ui_density',v));form.addWidget(density);form.addWidget(QLabel('Interface text size'));size=QSpinBox();size.setRange(11,17);size.setSuffix(' px');size.setValue(d.state.get('text_size',13));size.valueChanged.connect(lambda v:self.save('text_size',v));form.addWidget(size);form.addStretch();tabs.addTab(general,'General')
        motion=QWidget();form=QVBoxLayout(motion)
        form.addWidget(QLabel('Window animations'))
        from window_motion import EFFECTS
        self.motion_choices={}
        for label,key in [('Opening windows','open_effect'),('Closing windows','close_effect')]:
            form.addWidget(QLabel(label));choice=QComboBox();choice.addItems(EFFECTS);choice.setCurrentText(d.state.get(key,'Soft Zoom'));choice.currentTextChanged.connect(lambda value,k=key:self.save(k,value));form.addWidget(choice);self.motion_choices[key]=choice
        form.addWidget(QLabel('Animation speed'));speed=QComboBox();speed.addItems(['Quick','Normal','Relaxed']);speed.setCurrentText(d.state.get('animation_speed','Normal'));speed.currentTextChanged.connect(lambda value:self.save('animation_speed',value));form.addWidget(speed)
        self.check(form,'Reduce motion (disable window animations)','reduce_motion',False)
        preview=QPushButton('Preview animation');preview.clicked.connect(lambda:d.text_window('Animation Preview','Close this window to preview your closing effect.'));form.addWidget(preview)
        note=QLabel('Applies to built-in Macaque windows. Native Linux and emulated applications use their own window effects.');note.setWordWrap(True);form.addWidget(note);form.addStretch();tabs.addTab(motion,'Animations')
        bar=QWidget();form=QVBoxLayout(bar);form.addWidget(QLabel('Top bar controls · overflow keeps hidden controls available'))
        info=QLabel('A quiet menu bar: Macaque, active app, File, Edit, View, Window, Help, Controls and clock. Extra features are inside Controls.');info.setWordWrap(True);form.addWidget(info)
        sounds=QPushButton('Classic Sounds…');sounds.clicked.connect(lambda:d.launch('Classic Sounds'));form.addWidget(sounds)
        self.check(form,'Show seconds in clock','clock_seconds',False);self.check(form,'24-hour clock','clock_24',False)
        self.check(form,'Compact top bar','compact_bar',True);form.addStretch();tabs.addTab(bar,'Top Bar')
        startup=QWidget();form=QVBoxLayout(startup);form.addWidget(QLabel('Open these built-in apps when Macaque starts:'));self.startup=QListWidget();form.addWidget(self.startup)
        for name in APP_NAMES:
            if name in CREATIVE_APPS or name in ('Settings','Notifications'):continue
            item=QListWidgetItem(name);item.setFlags(item.flags()|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Checked if name in d.state.get('startup_apps',[]) else Qt.Unchecked);self.startup.addItem(item)
        self.startup.itemChanged.connect(self.save_startup);tabs.addTab(startup,'Startup Apps')
        shortcuts=QWidget();form=QVBoxLayout(shortcuts)
        for title,app in [('Appearance and wallpapers','Appearance'),('Mouse and dragging','Mouse'),('Classic Mac compatibility','Classic Mac Apps'),('Flatpak applications','Flatpak Apps'),('Backup and recovery','Backup & Recovery'),('Classic desktop sounds','Classic Sounds'),('Sound output','Sound'),('Network information','Network'),('Storage information','Storage'),('System monitor','System Monitor')]:b=QPushButton(title);b.clicked.connect(lambda checked=False,n=app:d.launch(n));form.addWidget(b)
        text=QLabel('F6  Search Classic\nCtrl+Shift+D  Show / restore desktop\nCtrl+Shift+Left / Right  Snap active window\nCtrl+Shift+P  Save desktop screenshot\nCtrl+,  Settings\n\nThese settings affect Macaque. Host accounts, firewall, updates, Wi-Fi configuration and power management remain in Linux settings.');text.setWordWrap(True);form.addWidget(text);form.addStretch();tabs.addTab(shortcuts,'Controls')
    def check(self,layout,title,key,default):
        check=QCheckBox(title);check.setChecked(self.d.state.get(key,default));check.toggled.connect(lambda v,k=key:self.save(k,v));self.checks[key]=check;layout.addWidget(check)
    @Slot(str,object)
    def sync_preference(self,key,value):
        if key in self.checks:self.checks[key].setChecked(value)
    def save(self,key,value):
        self.d.set_preference(key,value)
        if key in ('ui_density','text_size'):self.d.apply_ui_theme()
        if key=='desktop_icons':self.d.update_icon_visibility()
    def bar_item(self,key,value):self.d.state.setdefault('bar_items',{})[key]=value;self.d.persist();self.d.top_bar.update_layout()
    def save_startup(self,*args):self.d.state['startup_apps']=[self.startup.item(i).text() for i in range(self.startup.count()) if self.startup.item(i).checkState()==Qt.Checked];self.d.persist()

class ModernFeatures:
    def desktop_stylesheet(self):
        from theme import stylesheet
        css=stylesheet(self.state.get('mode','light'),self.state.get('accent','#287f70')).replace('font-size:13px',f"font-size:{self.state.get('text_size',13)}px")
        if self.state.get('ui_density','Compact')=='Compact':css=css.replace('padding:5px 10px','padding:3px 7px').replace('padding:6px 26px 6px 13px','padding:4px 22px 4px 10px').replace('padding:7px 12px','padding:4px 8px')
        return css
    def update_icon_visibility(self):
        for b in self.icons+self.desktop_extras:b.setVisible(self.state.get('desktop_icons',True))
    def notify(self,title,message,sound=True):
        if sound:self.play_sound('notification')
        items=self.state.setdefault('notifications',[]);items.append({'time':time.time(),'title':str(title),'message':str(message)});self.state['notifications']=items[-100:];self.state['unread_notifications']=min(100,self.state.get('unread_notifications',0)+1);self.persist();self.top_bar.refresh_status()
        for window in self.area.subWindowList():
            if isinstance(window.content,NotificationCenter):window.content.refresh()
        if not self.state.get('do_not_disturb',False):
            if getattr(self,'toast',None):self.toast.hide();self.toast.deleteLater()
            toast=QLabel(str(title)+'\n'+str(message),self.area.viewport());toast.setWordWrap(True);toast.setStyleSheet('background:#283f3c;color:#f2fff7;border:1px solid #6ba695;border-radius:6px;padding:10px;');toast.setFixedWidth(min(350,self.area.viewport().width()-20));toast.adjustSize();toast.move(max(10,self.area.viewport().width()-toast.width()-15),12);toast.show();toast.raise_();self.toast=toast;QTimer.singleShot(4500,toast.hide)
    def notifications(self):
        self.state['unread_notifications']=0;self.persist();self.top_bar.refresh_status()
        for window in self.area.subWindowList():
            if isinstance(window.content,NotificationCenter):window.content.refresh();self.activate_window(window);return window
        return self.window('Notifications',NotificationCenter(self),(530,460))
    def settings(self):
        for window in self.area.subWindowList():
            if isinstance(window.content,Settings):self.activate_window(window);return window
        return self.window('Settings',Settings(self),(610,660))
    def show_desktop(self):
        from shiboken6 import isValid
        groups=getattr(self,'desktop_window_groups',{});hidden=groups.get(self.workspace,[])
        if hidden:
            for window in hidden:
                if isValid(window) and window.property('workspace')==self.workspace:window.showNormal()
            groups[self.workspace]=[]
        else:
            groups[self.workspace]=[w for w in self.area.subWindowList() if w.property('workspace')==self.workspace and not w.isMinimized()]
            for window in groups[self.workspace]:window.showMinimized()
        self.desktop_window_groups=groups
    def snap_window(self,side):
        w=self.area.activeSubWindow()
        if not w:return
        if w.shaded:w.shade()
        w.showNormal();rect=self.area.viewport().rect();half=rect.width()//2;w.setGeometry(0 if side=='left' else half,0,half,rect.height())
    def capture_desktop(self):
        def save():
            target=self.disk.root/'Pictures';target.mkdir(exist_ok=True);path=self.disk.unused(target/('Macaque '+time.strftime('%Y-%m-%d %H-%M-%S')+'.png'))
            try:
                if not self.grab().save(str(path),'PNG'):raise OSError('The screenshot could not be saved.')
                self.disk_changed.emit();self.notify('Screenshot saved','Pictures / '+path.name,sound=False);self.play_sound('save')
            except OSError as ex:self.error(ex)
        QTimer.singleShot(180,save)
    def session_menu(self,menu):
        menu.clear();menu.addAction('Macaque desktop session').setEnabled(False);menu.addAction('Show / Restore Desktop',self.show_desktop);menu.addAction('Screen Saver Preview',self.screensaver);menu.addSeparator();menu.addAction('Restart Macaque…',self.restart);menu.addAction('Quit Macaque',self.close)
    def clock_menu(self,menu):
        from PySide6.QtWidgets import QCalendarWidget,QWidgetAction
        menu.clear();calendar=QCalendarWidget();calendar.setMaximumWidth(350);action=QWidgetAction(menu);action.setDefaultWidget(calendar);menu.addAction(action);menu.addAction('Date & Time',lambda:self.launch('Date & Time'));menu.addAction('Stopwatch / Countdown',lambda:self.launch('Clockwork'))
