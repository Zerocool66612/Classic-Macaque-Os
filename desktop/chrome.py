from PySide6.QtCore import Qt,QSize,QTimer
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget,QToolButton,QMenu,QHBoxLayout,QLabel,QDialog,QVBoxLayout,QLineEdit,QListWidget,QListWidgetItem,QSizePolicy
from visuals import icon,app_kind
from window_motion_icon import white_monkey
from menu_compat import Menu as QMenu

class TopBar(QWidget):
    def __init__(self,d):
        super().__init__();self.d=d;self.setObjectName('topBar');self.setAttribute(Qt.WA_StyledBackground,True);self.setFixedHeight(32);self.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);self.row=QHBoxLayout(self);self.row.setContentsMargins(3,0,3,0);self.row.setSpacing(0);self.buttons=[]
        self.system=self.menu('Macaque',white_monkey());self.system.aboutToShow.connect(d.system_menu);self.buttons[0].setToolTip('About This Computer and system menu');self.buttons[0].setText('');self.buttons[0].setToolButtonStyle(Qt.ToolButtonIconOnly);self.buttons[0].setFixedWidth(30);self.buttons[0].setAccessibleName('About This Computer and system menu')
        self.appmenu=self.menu('Macaque Files',icon('folder'));self.appmenu.aboutToShow.connect(d.application_menu);self.buttons[1].setMaximumWidth(140);self.buttons[1].setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Preferred)
        for name,title,callback in [('file','File',d.file_menu),('edit','Edit',d.edit_menu),('view','View',d.view_menu),('special','Special',d.special_menu),('windows','Window',d.window_menu)]:
            menu=self.menu(title);setattr(self,name,menu);menu.aboutToShow.connect(callback)
        self.help=self.menu('Help');self.help.addAction('Macaque Help',lambda:d.launch('Help Center'));self.help.addAction('Show Data Folder',d.open_data)
        self.apps=self.menu('Apps');self.apps.aboutToShow.connect(self.applications_menu)
        self.more=QToolButton();self.more.setText('•••');self.more.setToolTip('More menus and controls');self.more.setPopupMode(QToolButton.InstantPopup);self.more_menu=QMenu(self.more);self.more.setMenu(self.more_menu);self.row.addWidget(self.more)
        self.pins=[]
        for name in ['Tasks','Clockwork','Chess']:
            b=QToolButton();b.setIcon(icon(app_kind(name),24));b.setIconSize(QSize(18,18));b.setToolTip('Open '+name);b.clicked.connect(lambda checked=False,n=name:d.launch(n));self.row.addWidget(b);self.pins.append(b)
        self.row.addStretch(1);self.version=QLabel('v0.24');self.row.addWidget(self.version);self.controls={}
        self.search=self.control('search','⌕','Search apps and actions · F6',d.launch_palette);self.search.setIcon(icon('search',22));self.search.setIconSize(QSize(17,17));self.search.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.network=self.control('network','◎','Network information');self.network_menu=self.popup(self.network,lambda menu:d.network_menu(menu))
        self.sound=self.control('sound','♪','Sound output');self.sound.clicked.connect(lambda:d.launch('Sound'))
        self.notifications=self.control('notifications','♧','Notifications');self.notifications.clicked.connect(d.notifications)
        self.theme=self.control('theme','☾','Light / dark mode',d.toggle_dark)
        self.switch=self.control('switch','▣ 0','Running Macaque windows');self.switch_menu=self.popup(self.switch,lambda menu:d.window_menu(menu))
        self.capture=self.control('capture','▧','Save Macaque screenshot · Ctrl+Shift+P',d.capture_desktop)
        self.desktop=self.control('desktop','▱','Show / restore desktop · Ctrl+Shift+D',d.show_desktop)
        self.settings=self.control('settings','⚙','Macaque Settings · Ctrl+,',d.settings)
        self.session=self.control('session','⏻','Macaque session controls');self.session_popup=self.popup(self.session,lambda menu:d.session_menu(menu))
        self.quick=QToolButton();self.quick.setText('Controls');self.quick.setToolTip('Sound, appearance, notifications and desktop controls');self.row.addWidget(self.quick);self.quick_menu=self.popup(self.quick,lambda menu:d.quick_settings(menu))
        self.battery=QToolButton();self.battery.setAccessibleName('Laptop battery status');self.row.addWidget(self.battery);self.battery.clicked.connect(lambda:d.text_window('Battery status',self.battery.toolTip()));self.battery_timer=QTimer(self);self.battery_timer.timeout.connect(self.refresh_battery);self.battery_timer.start(10000);self.refresh_battery()
        self.clock=QToolButton();self.clock.setToolTip('Calendar and timers');self.row.addWidget(self.clock);self.calendar_menu=self.popup(self.clock,lambda menu:d.clock_menu(menu))
        for key,kind in [('network','network'),('sound','sound'),('notifications','bell'),('capture','capture'),('desktop','display'),('settings','gear'),('session','power')]:
            self.controls[key].setIcon(icon(kind,22));self.controls[key].setIconSize(QSize(17,17));self.controls[key].setText('')
        self.apply_theme();QTimer.singleShot(0,self.update_layout)
    def control(self,key,text,tip,callback=None):
        b=QToolButton();b.setText(text);b.setToolTip(tip);b.setAccessibleName(tip);b.setMinimumWidth(25);self.row.addWidget(b);self.controls[key]=b
        if callback:b.clicked.connect(callback)
        return b
    def popup(self,button,callback):
        menu=QMenu(self);menu.aboutToShow.connect(lambda:callback(menu));button.setPopupMode(QToolButton.InstantPopup);button.setMenu(menu);return menu
    def menu(self,title,image=None):
        b=QToolButton();b.setText(title)
        if image:b.setIcon(image);b.setIconSize(QSize(17,17));b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        b.setPopupMode(QToolButton.InstantPopup);menu=QMenu(title,self);b.setMenu(menu);b.setAccessibleName(title+' menu');self.row.addWidget(b);self.buttons.append(b);return menu
    def applications_menu(self):
        from model import APP_NAMES
        self.apps.clear();self.apps.addAction('All Applications…',lambda:self.d.launch('Applications'));self.apps.addSeparator()
        for name in APP_NAMES:self.apps.addAction(icon(app_kind(name)),name,lambda checked=False,n=name:self.d.launch(n))
    def apply_theme(self):
        c=self.d.colors();accent=self.d.state.get('accent','#287f70');pad=4 if self.d.state.get('compact_bar',True) else 7;self.setStyleSheet(f"QWidget#topBar {{background:{c['panel']};border-bottom:1px solid {c['border']};}} QToolButton {{background:transparent;color:{c['text']};border:0;border-radius:2px;padding:3px {pad}px;font-size:12px;}} QToolButton:hover,QToolButton:pressed {{background:{accent};color:#fff;}} QToolButton::menu-indicator {{image:none;}} QLabel {{color:{c['muted']};background:transparent;font-size:10px;padding:0 3px;}}")
        self.theme.setText('☀' if self.d.state.get('mode','light')=='dark' else '☾');self.theme.setToolTip('Switch appearance');self.update()
    def refresh_battery(self):
        from laptop_support import batteries,battery_summary
        text,tip=battery_summary(batteries());self.battery.setText(text);self.battery.setToolTip(tip);self.battery.setVisible(bool(text));self.update_layout()
    def refresh_status(self):
        count=self.d.state.get('unread_notifications',0);quiet=self.d.state.get('do_not_disturb',False);self.notifications.setIcon(icon('quiet' if quiet else 'bell',22));self.notifications.setToolButtonStyle(Qt.ToolButtonTextBesideIcon);self.notifications.setText(str(count) if count else '');self.notifications.setToolTip(('Do Not Disturb · ' if quiet else '')+f'{count} unread Macaque notifications')
        self.switch.setText('▣ '+str(len(self.d.area.subWindowList())));self.update_layout()
    def update_layout(self):
        if not hasattr(self,'clock'):return
        dense=self.d.state.get('compact_bar',True)
        if getattr(self,'_dense',None)!=dense:
            self._dense=dense;self.setFixedHeight(32 if dense else 38);self.buttons[1].setMaximumWidth(140 if dense else 180);self.apply_theme()
        # One controls menu replaces the entire status icon row. Keep the old
        # objects alive for their menu routes, without drawing them on the bar.
        for b in self.pins:b.hide()
        for b in self.controls.values():b.hide()
        self.version.hide()
        hidden=[5,8] # Special actions live in Controls; apps live in Macaque.
        available=self.width()-self.quick.sizeHint().width()-self.clock.sizeHint().width()-(self.battery.sizeHint().width() if self.battery.isVisible() else 0)-45
        used=sum(b.sizeHint().width() for i,b in enumerate(self.buttons) if i not in hidden)
        for index in [7,6,4,3,2,1]:
            if used<=available:break
            used-=self.buttons[index].sizeHint().width();hidden.append(index)
        for i,b in enumerate(self.buttons):b.setVisible(i not in hidden)
        overflow=[i for i in hidden if i not in (5,8)]
        self.more.setVisible(bool(overflow))
        signature=tuple(overflow)
        if getattr(self,'layout_signature',None)==signature:return
        self.layout_signature=signature;self.more_menu.clear()
        for i in sorted(overflow):self.more_menu.addMenu(self.buttons[i].menu())
    def resizeEvent(self,e):super().resizeEvent(e);self.update_layout()

class CommandPalette(QDialog):
    def __init__(self,d):
        super().__init__(d);self.d=d;self.setWindowTitle('Macaque Search & Launch');self.resize(580,430);layout=QVBoxLayout(self)
        heading=QLabel('Search & Launch');heading.setStyleSheet('font-size:20px;font-weight:bold;');layout.addWidget(heading)
        self.input=QLineEdit();self.input.setPlaceholderText('Apps, open windows, folders, or desktop actions…');self.input.setMinimumHeight(36);layout.addWidget(self.input);self.results=QListWidget();self.results.setIconSize(QSize(24,24));layout.addWidget(self.results,1);layout.addWidget(QLabel('Enter to open · Escape to cancel · F6 anywhere'))
        self.items=[]
        from model import APP_NAMES
        for name in APP_NAMES:self.items.append((name,'Application',app_kind(name),lambda n=name:d.launch(n)))
        self.items += [('Macaque HD','Folder','disk',lambda:d.open_finder(d.disk.root)),('Documents','Folder','documents',lambda:d.open_finder(d.disk.root/'Documents')),('Control Panels','Desktop action','appearance',d.control_panels),('Toggle Dark Mode','Desktop action','appearance',d.toggle_dark),('Save Screenshot','Desktop action','display',d.capture_desktop),('Show Desktop','Desktop action','computer',d.show_desktop),('New Note','Desktop action','sticky',lambda:d.launch('Macaque Notes')),('Show Control Strip','Desktop action','computer',lambda:d.native_strip.show() if d.native_strip else d.diagnostics())]
        for window in d.area.subWindowList():self.items.append((window.windowTitle(),'Open window','computer',lambda w=window:d.activate_window(w)))
        self.input.textChanged.connect(self.filter);self.input.returnPressed.connect(self.activate);self.results.itemDoubleClicked.connect(lambda _:self.activate());self.filter();self.input.setFocus()
    def filter(self):
        query=self.input.text().casefold().strip();self.results.clear()
        for index,(name,kind,image,callback) in enumerate(self.items):
            if not query or query in (name+' '+kind).casefold():
                item=QListWidgetItem(icon(image),name+'   ·   '+kind);item.setData(Qt.UserRole,index);self.results.addItem(item)
        if self.results.count():self.results.setCurrentRow(0)
    def activate(self):
        item=self.results.currentItem()
        if item:
            callback=self.items[item.data(Qt.UserRole)][3];self.accept();callback()
