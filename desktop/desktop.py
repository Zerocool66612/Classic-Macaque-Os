#!/usr/bin/env python3
import os,sys,json,shutil,platform,subprocess,time,random
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QDateTime,QStandardPaths,QSize,QPoint,Signal,QSettings,QUrl,QProcess
from PySide6.QtGui import QColor,QPalette,QPainter,QPixmap,QBrush,QPen,QFont,QAction,QKeySequence,QDesktopServices
from PySide6.QtWidgets import *
from model import Disk,APP_NAMES,CONTROL_PANELS
from visuals import STYLE,icon,app_kind
from theme import colors as theme_colors,stylesheet as theme_stylesheet
from applications import Finder,SimpleText,Sticky,Calculator,Sherlock,Puzzle,Trash,Scrapbook,HELP
from native_strip import NativeStrip
from sound_theme import SoundTheme,SoundPreferences
from classic_search import ClassicSearch
from backup import Backups
from app_support import AppSupport,FlatpakApps,ClassicMacApps
from downloads import Downloads
from browser_app import Browser
from workspaces import WorkspaceFeatures,WorkspaceOverview
from welcome import Welcome
from creative_apps import CreativeApps,CREATIVE_APPS
from extras import Tasks,Clockwork,Paint,ArchiveViewer,Characters,MediaPlayer
from chess_app import Chess
from teapot import Teapot
from wallpapers import Wallpapers,render as render_wallpaper,NAMES as WALLPAPERS
from mouse_tools import DesktopIcon,MousePreferences,paths_from
from system_apps import AppHub,Sound,Network,Storage,Monitor,Display,ImageViewer,EmbeddedDialog
VERSION='0.29'

from menu_compat import Menu as QMenu

class TitleBar(QWidget):
    def __init__(self,window,title):
        super().__init__();self.w=window;self.drag=None;self.setFixedHeight(30);layout=QHBoxLayout(self);layout.setContentsMargins(9,0,7,0);layout.setSpacing(6)
        for color,name,callback in [('#ed6c5d','Close',window.close),('#efc24c','Minimize',window.showMinimized),('#6bbd62','Zoom',window.zoom)]:
            b=QPushButton();b.setToolTip(name);b.setAccessibleName(name);b.setFixedSize(14,14);b.setStyleSheet(f'QPushButton {{background:{color}; border:1px solid #666; border-radius:7px; padding:0;}}');b.clicked.connect(callback);layout.addWidget(b)
        layout.addStretch();self.label=QLabel(title);self.label.setTextFormat(Qt.PlainText);self.label.setObjectName('titleCaption');layout.addWidget(self.label);layout.addStretch()
    def contextMenuEvent(self,event):
        menu=QMenu(self);menu.addAction('Minimize',self.w.showMinimized);menu.addAction('Restore' if self.w.isMaximized() else 'Zoom',self.w.zoom);menu.addAction('Unshade' if self.w.shaded else 'Shade',self.w.shade)
        spaces=menu.addMenu('Move to Workspace')
        for i,name in enumerate(self.w.d.workspace_names()):spaces.addAction(name,lambda checked=False,n=i:self.w.d.move_to_workspace(self.w,n))
        menu.addSeparator();menu.addAction('Close',self.w.close);menu.exec(event.globalPos())
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor(self.w.d.colors()['title']));p.setPen(QColor(self.w.d.colors()['stripe']))
        if self.w.d.area.activeSubWindow()==self.w:
            for y in range(5,27,3):p.drawLine(77,y,self.width()-7,y)
    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:self.drag=e.globalPosition().toPoint()-self.w.pos()
    def mouseMoveEvent(self,e):
        if self.drag is not None and e.buttons()&Qt.LeftButton and not self.w.isMaximized():
            pos=e.globalPosition().toPoint()-self.drag;pos.setY(max(0,pos.y()));pos.setX(max(20-self.w.width(),min(self.w.d.area.viewport().width()-30,pos.x())));self.w.move(pos)
    def mouseReleaseEvent(self,e):self.drag=None
    def mouseDoubleClickEvent(self,e):self.w.zoom() if self.w.d.state.get('title_double')=='Zoom' else self.w.shade()

class Window(QMdiSubWindow):
    def __init__(self,d,title,content,size):
        super().__init__();self.d=d;self.content=content;self.shaded=False;self.saved_size=None
        self.setProperty('workspace',d.workspace);self.setWindowFlags(Qt.SubWindow|Qt.FramelessWindowHint);self.setAttribute(Qt.WA_DeleteOnClose);self.setWindowTitle(title)
        panel=QWidget();panel.setObjectName('classicWindowFrame');layout=QVBoxLayout(panel);layout.setContentsMargins(2,2,2,2);layout.setSpacing(0)
        self.bar=TitleBar(self,title);layout.addWidget(self.bar);layout.addWidget(content,1);self.grip=QSizeGrip(panel);foot=QHBoxLayout();foot.setContentsMargins(0,0,0,0);foot.addStretch();foot.addWidget(self.grip);layout.addLayout(foot);self.setWidget(panel)
        self.setMinimumSize(280,200);d.area.addSubWindow(self);self.resize(*size);self.show()
        if hasattr(content,'attach'):content.attach(self)
    def start_open_animation(self):
        from shiboken6 import isValid
        if isValid(self):animate(self,True)
    def rename(self,title):self.setWindowTitle(title);self.bar.label.setText(title)
    def zoom(self):
        if self.shaded:self.shade()
        self.showNormal() if self.isMaximized() else self.showMaximized()
    def shade(self):
        if self.isMaximized():self.showNormal()
        if self.shaded:
            self.setMaximumHeight(16777215);self.setMinimumHeight(200);self.content.show();self.grip.show();self.resize(self.saved_size);self.shaded=False
        else:
            self.saved_size=self.size();self.content.hide();self.grip.hide();self.setMinimumHeight(34);self.setMaximumHeight(34);self.resize(self.width(),34);self.shaded=True
    def closeEvent(self,e):
        if hasattr(self.content,'can_close') and not self.content.can_close():e.ignore();return
        animate(self,False)
        self.d.play_sound('close');super().closeEvent(e)

from window_motion import animate
from chrome import TopBar,CommandPalette
from modern_desktop import ModernFeatures,Settings,NotificationCenter

class ScreenSaver(QWidget):
    def __init__(self,parent):
        super().__init__(parent);self.setGeometry(parent.rect());self.setFocusPolicy(Qt.StrongFocus);self.stars=[[random.random(),random.random(),random.uniform(.002,.008)] for _ in range(100)];self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(40);self.show();self.raise_();self.setFocus();self.setToolTip('Click or press a key to return. This does not lock the computer.')
    def tick(self):
        for star in self.stars:star[1]=(star[1]+star[2])%1
        self.update()
    def paintEvent(self,e):
        p=QPainter(self);p.fillRect(self.rect(),Qt.black)
        for x,y,speed in self.stars:p.setPen(QPen(QColor('#ddddff'),1+int(speed*250)));p.drawPoint(int(x*self.width()),int(y*self.height()))
        p.setPen(Qt.white);p.drawText(20,self.height()-25,'Macaque Classic · click or press a key to return')
    def keyPressEvent(self,e):self.deleteLater()
    def mousePressEvent(self,e):self.deleteLater()

from installer_support import InstallerSupport,installer_available
from context_actions import ContextActions

class Desktop(InstallerSupport,ContextActions,WorkspaceFeatures,ModernFeatures,QMainWindow):
    disk_changed=Signal()
    preferences_changed=Signal(str,object)
    def __init__(self,base=None):
        super().__init__();self.setWindowTitle('Macaque Classic 0.29 — Macaque Desktop');self.resize(1360,880)
        self.base=Path(base or os.environ.get('MACAQUE_DATA_DIR') or QStandardPaths.writableLocation(QStandardPaths.AppDataLocation));self.base.mkdir(parents=True,exist_ok=True);self.disk=Disk(self.base);self.state_path=self.base/'desktop-state.json'
        if self.disk.migrations and self.state_path.exists() and not (self.base/'desktop-state.before-0.6.json').exists():shutil.copy2(self.state_path,self.base/'desktop-state.before-0.6.json')
        try:self.state=json.loads(self.state_path.read_text())
        except (OSError,ValueError):self.state={}
        self.workspace=max(0,min(3,int(self.state.get('workspace',0))));self.app_support=AppSupport(self);self.state.setdefault('wallpaper','Lagoon');self.sound_theme=SoundTheme(self);self.apply_mouse()
        self.stickies=self.state.get('stickies',{'welcome':'Welcome to Macaque Classic!\n\nDouble-click desktop icons to explore.\nTry the Macaque menu for desktop apps.\n\nYour notes save automatically.'} if not self.state_path.exists() else {});self.scraps=self.state.get('scraps',[]);self.recent=[self.disk.migrated_path(path) for path in self.state.get('recent',[])]
        self.container=QWidget();self.layout=QVBoxLayout(self.container);self.layout.setContentsMargins(0,0,0,0);self.layout.setSpacing(0);self.area=QMdiArea();self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.setCentralWidget(self.container)
        self.area.viewport().setAcceptDrops(True);self.area.viewport().installEventFilter(self);self.selection_band=QRubberBand(QRubberBand.Rectangle,self.area.viewport());self.selection_origin=None
        self.top_bar=TopBar(self);self.layout.addWidget(self.top_bar);self.layout.addWidget(self.area,1);self.icons=[];self.desktop_extras=[];self.file_clipboard=None;self.native_strip=None;self.strip=None;self.quitting=False;self.saver=None
        self.apply_appearance();self.make_icons();self.refresh_desktop();self.area.viewport().setContextMenuPolicy(Qt.CustomContextMenu);self.area.viewport().customContextMenuRequested.connect(self.desktop_context);self.area.subWindowActivated.connect(self.active_changed);self.disk_changed.connect(self.refresh_desktop)
        self.shortcuts();self.clock_timer=QTimer(self);self.clock_timer.timeout.connect(self.clock);self.clock_timer.start(1000);self.clock()
        try:self.native_strip=NativeStrip(self);self.strip=self.native_strip.widget;self.sync_strip_theme()
        except Exception as ex:
            self.strip=QLabel('Control Strip could not load — Help → Diagnostics',self.area.viewport());self.strip.setStyleSheet('background:#ffebbd;color:#111;padding:6px;');self.strip.resize(410,35);self.strip.move(10,600);self.strip.show();self.strip_error=str(ex)
        from removable_drives import RemovableMonitor
        self.removable=RemovableMonitor(self)
        self.top_bar.help.addAction('Diagnostics',self.diagnostics);QTimer.singleShot(0,self.initial)
    def initial(self):
        self.arrange_icons();self.update_icon_visibility()
        if self.state.get('startup_welcome',False):self.launch('Welcome Center')
        if self.state.get('startup_files',True):self.open_finder(self.disk.root)
        if self.state.get('startup_about',False):self.launch('About This Computer').move(max(30,min(720,self.area.viewport().width()-570)),55)
        for i,key in enumerate(list(self.stickies)[:4] if self.state.get('startup_notes',True) else []):self.launch('Macaque Notes',key=key).move(370+i*25,max(100,self.area.viewport().height()-330+i*15))
        for name in self.state.get('startup_apps',[]):
            if name in APP_NAMES and name not in CREATIVE_APPS and name not in ('Settings','Notifications'):self.launch(name)
        if self.strip:self.strip.raise_()
        self.sound_theme.suspended=False;self.play_sound('startup')
    def colors(self):return theme_colors(self.state.get('mode','light'))
    def apply_ui_theme(self):
        c=self.colors();app=QApplication.instance();app.setStyleSheet(self.desktop_stylesheet())
        palette=app.palette()
        for role,key in [(QPalette.Window,'window'),(QPalette.WindowText,'text'),(QPalette.Base,'base'),(QPalette.AlternateBase,'panel'),(QPalette.Text,'text'),(QPalette.Button,'panel'),(QPalette.ButtonText,'text'),(QPalette.ToolTipBase,'panel'),(QPalette.ToolTipText,'text')]:palette.setColor(role,QColor(c[key]))
        palette.setColor(QPalette.Highlight,QColor(self.state.get('accent','#287f70')));palette.setColor(QPalette.HighlightedText,Qt.white);app.setPalette(palette)
        if hasattr(self,'top_bar'):self.top_bar.apply_theme()
        if hasattr(self,'area'):
            for window in self.area.subWindowList():window.bar.update()
        self.sync_strip_theme()
    def sync_strip_theme(self):
        if getattr(self,'native_strip',None) and self.state.get('sync_strip',True):self.native_strip.apply_theme(self.state.get('mode','light'))
    def set_mode(self,mode):
        if mode not in ('light','dark'):raise ValueError('Unknown desktop mode')
        self.state['mode']=mode;self.apply_appearance()
    def toggle_dark(self):self.set_mode('light' if self.state.get('mode','light')=='dark' else 'dark')
    def set_preference(self,key,value):
        if self.state.get(key)==value:return
        self.state[key]=value;self.persist();self.clock();self.top_bar.update_layout();self.sync_strip_theme();self.preferences_changed.emit(key,value)
    def launch_palette(self):return self.launch('Macaque Search')
    def play_sound(self,key):
        if os.environ.get('MACAQUE_SILENT')!='1':return self.sound_theme.play(key)
    def quick_settings(self,menu):
        menu.clear();menu.addAction('Battery & Power…',lambda:self.launch('Battery & Power'));menu.addAction('USB Drives…',lambda:self.launch('USB Drives'));menu.addAction('Software Update…',lambda:self.launch('Software Update'));menu.addSeparator();menu.addAction('Terminal…',self.launch_terminal);menu.addAction('Settings…',self.settings);menu.addAction('Web Browser…',lambda:self.launch('Macaque Web'));workspace=menu.addMenu('Workspaces');self.workspace_menu(workspace);menu.addAction('Downloads…',lambda:self.launch('Downloads'));menu.addAction('App Compatibility…',lambda:self.launch('Classic Mac Apps'));menu.addAction('Flatpak Apps…',lambda:self.launch('Flatpak Apps'));menu.addAction('Classic Sounds…',lambda:self.launch('Classic Sounds'));menu.addSeparator()
        mode=menu.addAction('Dark Mode');mode.setCheckable(True);mode.setChecked(self.state.get('mode','light')=='dark');mode.triggered.connect(self.toggle_dark)
        quiet=menu.addAction('Do Not Disturb');quiet.setCheckable(True);quiet.setChecked(self.state.get('do_not_disturb',False));quiet.toggled.connect(lambda v:self.set_preference('do_not_disturb',v))
        muted=menu.addAction('Mute Desktop Sounds');muted.setCheckable(True);muted.setChecked(not self.state.get('sounds_enabled',True));muted.toggled.connect(lambda v:(self.set_preference('sounds_enabled',not v),self.sound_theme.stop() if v else None))
        menu.addSeparator();menu.addAction('Search Classic…',self.launch_palette);menu.addAction('Notifications…',self.notifications);menu.addAction('Sound Output…',lambda:self.launch('Sound'));menu.addAction('Wi-Fi & Network…',lambda:self.launch('Network'))
        menu.addAction('Show / Restore Desktop',self.show_desktop);menu.addAction('Save Screenshot',self.capture_desktop)
        more=menu.addMenu('More Options')
        more.addAction('Appearance…',self.appearance);more.addAction('Mouse…',lambda:self.launch('Mouse'));more.addAction('Wallpapers…',lambda:self.launch('Wallpapers'));more.addAction('Show Control Strip',lambda:self.native_strip.show() if self.native_strip else self.diagnostics());more.addAction('Full Screen',self.fullscreen)
        self.window_menu(self.top_bar.switch_menu);more.addMenu(self.top_bar.switch_menu).setText('Windows')
        self.special_menu();more.addMenu(self.top_bar.special).setText('Desktop Actions')
        clock=more.addMenu('Clock')
        for title,key,default in [('24-hour Clock','clock_24',False),('Show Day in Clock','clock_date',True),('Show Seconds','clock_seconds',False)]:
            a=clock.addAction(title);a.setCheckable(True);a.setChecked(self.state.get(key,default));a.toggled.connect(lambda v,k=key:self.set_preference(k,v))
    def network_menu(self,menu):
        from PySide6.QtNetwork import QNetworkInterface
        menu.clear();menu.addAction('Wi-Fi & Network…',lambda:self.launch('Network'));menu.addSeparator();menu.addAction('Network interfaces').setEnabled(False);menu.addSeparator();found=False
        for interface in QNetworkInterface.allInterfaces():
            flags=interface.flags()
            if flags & QNetworkInterface.IsLoopBack:continue
            addresses=[entry.ip().toString() for entry in interface.addressEntries()]
            up=bool(flags & QNetworkInterface.IsUp);item=menu.addMenu(interface.humanReadableName()+(' · enabled' if up else ' · disabled'))
            for address in addresses[:5]:item.addAction(address).setEnabled(False)
            if not addresses:item.addAction('No address assigned').setEnabled(False)
            found=True
        if not found:menu.addAction('No interfaces found').setEnabled(False)
        menu.addSeparator();menu.addAction('Link status does not verify Internet access').setEnabled(False)
    def handle_strip_request(self,program,args):
        if not isinstance(program,str) or not isinstance(args,list) or any(not isinstance(a,str) for a in args):return
        if program=='macaque-dialog':
            from shiboken6 import wrapInstance
            dialog=wrapInstance(int(args[0]),QDialog);dialog.setProperty('macaqueEmbedded',True)
            host=EmbeddedDialog(dialog);size=dialog.sizeHint();frame=self.window(dialog.windowTitle() or 'Control Strip',host,(min(1000,max(420,size.width()+20)),min(740,max(300,size.height()+55))))
            def finished(result):
                host.finish();frame.hide();frame.deleteLater()
            dialog.finished.connect(finished);return frame
        if program=='macaque-app':return self.launch(args[0]) if args else None
        if program in ('macaque-folder','xdg-open'):
            target=args[0] if args else str(self.disk.root)
            if target=='applications:/':return self.launch('Applications')
            if target=='trash:/':return self.window('Trash',Trash(self),(530,340))
            path=Path(target).expanduser()
            if path.exists():return self.open_item(path)
            return self.text_window('Folder unavailable','This location does not exist:\n'+str(path))
        if program=='systemsettings':
            module=args[0] if args else ''
            if module in ('kcm_pulseaudio',):return self.launch('Sound')
            if module in ('kcm_kscreen','kcm_brightness'):return self.launch('Display')
            if module in ('kcm_networkmanagement','kcm_bluetooth'):return self.launch('Network')
            if module=='kcm_clock':return self.calendar()
            return self.appearance()
        if program in ('filelight','partitionmanager'):return self.launch('Storage')
        if program in ('plasma-systemmonitor','ksysguard'):return self.launch('System Monitor')
        if program=='nmcli':return self.launch('Network')
        if program=='brightnessctl':return self.launch('Display')
        if program in ('wpctl','pactl'):
            allowed = (program=='wpctl' and len(args)==3 and args[0]=='set-mute' and args[1] in ('@DEFAULT_AUDIO_SINK@','@DEFAULT_AUDIO_SOURCE@') and args[2]=='toggle') or (program=='pactl' and len(args)==3 and args[0] in ('set-sink-mute','set-source-mute') and args[1] in ('@DEFAULT_SINK@','@DEFAULT_SOURCE@') and args[2]=='toggle')
            if allowed:
                try:
                    result=subprocess.run([program,*args],capture_output=True,text=True,timeout=2)
                    if result.returncode:return self.text_window('Sound unavailable',result.stderr or 'The host audio service rejected the request.')
                except (OSError,subprocess.TimeoutExpired) as ex:return self.text_window('Sound unavailable',str(ex))
                return None
        if program=='loginctl':return self.launch('Battery & Power').content.lock()
        return self.text_window('Not available inside Macaque',program+' is not an included Macaque application.\n\nNo host program was launched.')
    def persist(self):
        self.state.update({'stickies':self.stickies,'scraps':self.scraps,'recent':self.recent});Disk.write_json(self.state_path,self.state)
    def apply_mouse(self):
        QApplication.instance().setDoubleClickInterval(self.state.get('double_click_ms',400))
        QApplication.instance().setStartDragDistance(self.state.get('drag_distance',10))
    def transfer_paths(self,paths,target,copy=False):
        # Validate the whole batch before changing any item.
        try:
            target=self.disk.inside(target)
            if target!=self.disk.root:self.disk.editable(target)
            for path in paths:
                path=self.disk.editable(path)
                if path.is_dir() and (target==path or target.is_relative_to(path)):raise ValueError('A folder cannot be placed inside itself.')
            resolved=[Path(p).resolve() for p in paths]
            if any(a!=b and a.is_relative_to(b) for a in resolved for b in resolved):raise ValueError('Select a folder or its contents, rather than both in one drag.')
            for path in paths:(self.disk.copy_to if copy else self.disk.move_to)(path,target)
            self.disk_changed.emit();self.notify('Files copied' if copy else 'Files moved',f'{len(paths)} item(s) → {target.name}',sound=False);self.play_sound('move');return True
        except (OSError,ValueError) as ex:self.error(ex)
    def trash_paths(self,paths):
        try:
            for path in paths:self.disk.editable(path)
            for path in paths:self.disk.trash_item(path)
            self.disk_changed.emit();self.notify('Moved to Trash',f'{len(paths)} item(s). Open Trash to restore them.',sound=False);self.play_sound('trash')
        except (OSError,ValueError) as ex:self.error(ex)
    def new_sticky(self):
        import uuid
        key=uuid.uuid4().hex;self.stickies[key]='';self.persist();return key
    def add_recent(self,path):
        p=str(path);self.recent=[p]+[x for x in self.recent if x!=p];self.recent=self.recent[:12];self.persist()
    def apply_appearance(self):
        self.apply_ui_theme();color=self.state.get('color','#7385b8');color=QColor(color).darker(230).name() if self.state.get('mode','light')=='dark' else color;pattern=self.state.get('pattern','Solid');pm=QPixmap(8,8);pm.fill(QColor(color));p=QPainter(pm);p.setPen(QColor(color).darker(115))
        if pattern=='Pinstripes':
            for y in (0,4):p.drawLine(0,y,7,y)
        elif pattern=='Dither':
            for x,y in [(0,0),(4,2),(2,4),(6,6)]:p.drawPoint(x,y)
        elif pattern=='Grid':p.drawLine(0,0,7,0);p.drawLine(0,0,0,7)
        p.end();self.area.setBackground(QBrush(pm));self.update_wallpaper();self.persist()
    def update_wallpaper(self):
        name=self.state.get('wallpaper')
        if name not in WALLPAPERS:return
        size=self.area.viewport().size()
        if size.width()<1 or size.height()<1:return
        if getattr(self,'_wallpaper_name',None)!=name:
            self._wallpaper=QPixmap.fromImage(render_wallpaper(name));self._wallpaper_name=name
        pm=self._wallpaper.scaled(size,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation)
        pm=pm.copy((pm.width()-size.width())//2,(pm.height()-size.height())//2,size.width(),size.height())
        self.area.setBackground(QBrush(pm))
    def shortcuts(self):
        for shortcut,callback in [('Ctrl+Alt+1',lambda:self.switch_workspace(0)),('Ctrl+Alt+2',lambda:self.switch_workspace(1)),('Ctrl+Alt+3',lambda:self.switch_workspace(2)),('Ctrl+Alt+4',lambda:self.switch_workspace(3)),('Ctrl+Alt+L',lambda:self.launch('Battery & Power').content.lock()),('Ctrl+,',self.settings),('Ctrl+Shift+D',self.show_desktop),('Ctrl+Shift+P',self.capture_desktop),('Ctrl+Shift+Left',lambda:self.snap_window('left')),('Ctrl+Shift+Right',lambda:self.snap_window('right')),('F6',self.launch_palette),('Ctrl+Shift+Space',self.launch_palette),('Ctrl+N',lambda:self.launch('Macaque Text')),('Ctrl+O',self.open_dialog),('Ctrl+S',self.save_active),('Ctrl+Shift+S',lambda:self.save_active(True)),('Ctrl+W',self.close_active),('Ctrl+Q',self.close),('Ctrl+F',self.find),('F11',self.fullscreen),('Ctrl+I',self.info_active)]:
            action=QAction(self);action.setShortcut(QKeySequence(shortcut));action.triggered.connect(callback);self.addAction(action)
    def clock(self):
        seconds=self.state.get('clock_seconds',False)
        fmt=('HH:mm:ss' if seconds else 'HH:mm') if self.state.get('clock_24',False) else ('h:mm:ss AP' if seconds else 'h:mm AP')
        self.top_bar.clock.setText(QDateTime.currentDateTime().toString(('ddd ' if self.state.get('clock_date',True) else '')+fmt));self.top_bar.refresh_status()
    @staticmethod
    def format_bytes(size):
        for unit in ['bytes','KB','MB','GB','TB']:
            if size<1024:return f'{size:.0f} {unit}' if unit=='bytes' else f'{size:.1f} {unit}'
            size/=1024
    @staticmethod
    def file_date(value):return time.strftime('%b %d, %Y',time.localtime(value))
    def free_space(self):return shutil.disk_usage(self.base).free
    def launch_terminal(self):
        from terminal_app import Terminal
        w=self.window('Terminal',Terminal(self),(900,560));w.content.view.setFocus();return w
    def make_icons(self):
        entries=[('Macaque HD','disk',lambda:self.open_finder(self.disk.root)),('Documents','documents',lambda:self.open_finder(self.disk.root/'Documents')),('Applications','apps',lambda:self.open_finder(self.disk.root/'Applications')),('System Folder','system',lambda:self.open_finder(self.disk.root/'System Folder')),('Trash','trash',lambda:self.window('Trash',Trash(self),(530,340)))]
        entries.insert(-1,('Terminal','terminal',self.launch_terminal))
        if installer_available():entries.insert(-1,('Install Macaque Classic','disk',self.launch_installer))
        for title,kind,callback in entries:
            b=DesktopIcon(self,self.area.viewport());b.setProperty('iconKey',title);b.setProperty('dropTarget','trash' if title=='Trash' else str(self.disk.root/('Documents' if title=='Documents' else 'Desktop')) if title=='Documents' else str(self.disk.root) if title=='Macaque HD' else None);b.setText(title);b.setIcon(icon(kind));b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);b.setIconSize(QSize(48,48));b.setFixedSize(128,86);b.setStyleSheet('QToolButton {background:transparent;color:white;border:0;font-weight:bold;padding:3px;} QToolButton:hover {background:#ffffff20;border:1px dotted #eee;} QToolButton:checked {background:#335fa877;border:1px solid #b4d8ff;}');b.setToolTip('Double-click to open');b.installEventFilter(self);b.setProperty('desktopCallback',callback);b.setContextMenuPolicy(Qt.CustomContextMenu);b.customContextMenuRequested.connect(lambda pos,button=b,t=title,fn=callback:self.fixed_icon_menu(button,t,fn,pos));self.icons.append(b);b.show()
    def eventFilter(self,watched,event):
        from PySide6.QtCore import QEvent,QRect
        from shiboken6 import isValid
        if not hasattr(self,'icons') or not isValid(self.area):return False
        if hasattr(self,'area') and watched==self.area.viewport():
            # QMdiArea handles viewport context events itself on some platforms.
            # Route the background gesture directly, without touching child icons.
            if event.type()==QEvent.MouseButtonRelease and event.button()==Qt.RightButton:
                self.selection_band.hide();self.selection_origin=None;self.desktop_context(event.position().toPoint());event.accept();return True
            if event.type()==QEvent.ContextMenu:
                from PySide6.QtGui import QContextMenuEvent
                if event.reason()!=QContextMenuEvent.Mouse:self.desktop_context(event.pos())
                event.accept();return True
            if event.type() in (QEvent.DragEnter,QEvent.DragMove) and paths_from(event.mimeData()):event.acceptProposedAction();return True
            if event.type()==QEvent.Drop and paths_from(event.mimeData()):self.transfer_paths(paths_from(event.mimeData()),self.disk.root/'Desktop',bool(event.modifiers()&Qt.ControlModifier));event.acceptProposedAction();return True
            if event.type()==QEvent.MouseButtonPress and event.button()==Qt.LeftButton:
                self.selection_origin=event.position().toPoint();self.selection_band.setGeometry(QRect(self.selection_origin,QSize()));self.selection_band.show()
                if not event.modifiers()&Qt.ControlModifier:
                    for b in self.icons+self.desktop_extras:b.setChecked(False)
                return True
            if event.type()==QEvent.MouseMove and self.selection_origin is not None:
                rect=QRect(self.selection_origin,event.position().toPoint()).normalized();self.selection_band.setGeometry(rect)
                for b in self.icons+self.desktop_extras:b.setChecked(rect.intersects(b.geometry()))
                return True
            if event.type()==QEvent.MouseButtonRelease and self.selection_origin is not None:self.selection_band.hide();self.selection_origin=None;return True
        if watched in self.icons+self.desktop_extras and event.type()==QEvent.MouseButtonDblClick:
            
            if not self.state.get('single_click',False):watched.property('desktopCallback')()
            else:watched.setProperty('suppressSingle',True)
            return True
        if watched in self.icons+self.desktop_extras and event.type()==QEvent.KeyPress and event.key() in (Qt.Key_Return,Qt.Key_Enter):watched.property('desktopCallback')();return True
        return super().eventFilter(watched,event)
    def arrange_icons(self):
        viewport=self.area.viewport()
        for i,b in enumerate(self.icons):b.move(max(0,viewport.width()-140),max(10,viewport.height()-98) if i==len(self.icons)-1 else 15+i*98)
        for i,b in enumerate(self.desktop_extras):b.move(15+(i//6)*130,15+(i%6)*98)
        positions=self.state.get('icon_positions',{})
        for b in self.icons+self.desktop_extras:
            pos=positions.get(b.property('iconKey'))
            if pos:b.move(max(0,min(viewport.width()-b.width(),pos[0])),max(0,min(viewport.height()-b.height(),pos[1])))
    def resizeEvent(self,e):
        super().resizeEvent(e)
        if hasattr(self,'area'):QTimer.singleShot(0,self.arrange_icons);QTimer.singleShot(0,self.update_wallpaper)
        if self.saver:self.saver.setGeometry(self.area.viewport().rect())
    def refresh_desktop(self):
        count=len(self.disk.trash_items());self.icons[-1].setText(f'Trash ({count})' if count else 'Trash')
        for button in self.desktop_extras:button.removeEventFilter(self);button.hide();button.deleteLater()
        self.desktop_extras=[]
        for path in sorted((self.disk.root/'Desktop').iterdir())[:36]:
            b=DesktopIcon(self,self.area.viewport());b.setProperty('iconKey',str(path.relative_to(self.disk.root)));b.setProperty('filePath',str(path));b.setProperty('dropTarget',str(path) if path.is_dir() else None);b.setText(path.name);b.setIcon(icon('folder' if path.is_dir() else 'note'));b.setIconSize(QSize(48,48));b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);b.setFixedSize(125,86);b.setStyleSheet('QToolButton {background:transparent;color:white;border:0;font-weight:bold;} QToolButton:hover {background:#ffffff20;border:1px dotted white;} QToolButton:checked {background:#335fa877;border:1px solid #b4d8ff;}');b.setProperty('desktopCallback',lambda p=path:self.open_item(p));b.installEventFilter(self);b.setContextMenuPolicy(Qt.CustomContextMenu);b.customContextMenuRequested.connect(lambda pos,p=path,button=b:self.desktop_item_menu(button,p,pos));self.desktop_extras.append(b);b.show()
        if hasattr(self,'removable'):
            for drive in self.removable.disks:
                for volume in drive['volumes']:
                    b=DesktopIcon(self,self.area.viewport());b.setProperty('iconKey','usb:'+volume['device']);b.setText(volume['name']);b.setIcon(icon('disk'));b.setIconSize(QSize(48,48));b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);b.setFixedSize(125,86);b.setStyleSheet('QToolButton {background:transparent;color:white;border:0;font-weight:bold;} QToolButton:hover {background:#ffffff20;border:1px dotted white;}');b.setToolTip('Removable drive · double-click for mount/eject controls');b.setProperty('desktopCallback',lambda:self.launch('USB Drives'));b.installEventFilter(self);self.desktop_extras.append(b);b.show()
        self.arrange_icons()
        self.update_icon_visibility()
        if self.strip:self.strip.raise_()
    def desktop_context(self,pos):
        menu=self.file_context_menu([],self.disk.root/'Desktop');menu.addSeparator();menu.addAction('New Sticky',lambda:self.launch('Macaque Notes'));menu.addAction('Clean Up Desktop',self.clean_up_icons);menu.addAction('Refresh',self.refresh_desktop);menu.addSeparator();menu.addAction('Wallpapers…',lambda:self.launch('Wallpapers'));menu.addAction('Appearance…',self.appearance);menu.addAction('Mouse…',lambda:self.launch('Mouse'));menu.addAction('Settings…',self.settings);menu.exec(self.area.viewport().mapToGlobal(pos))
    def clean_up_icons(self):self.state['icon_positions']={};self.persist();self.arrange_icons()
    def new_desktop_folder(self):
        name,ok=QInputDialog.getText(self,'New Desktop Folder','Name:',text='untitled folder')
        if ok:self.operation(lambda:self.disk.new_folder(self.disk.root/'Desktop',name))
    def desktop_item_menu(self,button,path,pos):
        if not button.isChecked():
            for icon_button in self.desktop_extras:icon_button.setChecked(False)
            button.setChecked(True)
        paths=[Path(b.property('filePath')) for b in self.desktop_extras if b.isChecked()]
        menu=self.file_context_menu(paths or [path],self.disk.root/'Desktop');menu.exec(button.mapToGlobal(pos))
    def active(self):
        w=self.area.activeSubWindow();return w.content if w else None
    def active_changed(self,w):
        name=getattr(w.content,'app_name','Macaque Files') if w else 'Macaque Files';self.top_bar.buttons[1].setText(name);self.top_bar.buttons[1].setIcon(icon(app_kind(name)));self.top_bar.buttons[1].setToolTip((w.windowTitle()+' · ' if w else '')+name);self.top_bar.update_layout()
        for win in self.area.subWindowList():win.bar.update()
    def window(self,title,content,size=(620,420)):
        window=Window(self,title,content,size);count=len(self.area.subWindowList());window.move(35+((count-1)%8)*27,35+((count-1)%7)*27)
        if self.state.get('center_windows',False):window.move(max(0,(self.area.viewport().width()-window.width())//2),max(0,(self.area.viewport().height()-window.height())//2))
        QTimer.singleShot(0,window.start_open_animation)
        self.top_bar.refresh_status();self.play_sound('open')
        if self.strip:self.strip.raise_()
        return window
    def open_finder(self,path):return self.window('Macaque Files',Finder(self,path),(940,540))
    def open_item(self,path):
        path=Path(path)
        if path.name.endswith('.app') and path.stem in APP_NAMES+CONTROL_PANELS:return self.launch(path.stem)
        if path.is_dir():return self.open_finder(path)
        return self.open_document(path)
    def open_document(self,path):
        try:
            path=Path(path)
            if path.suffix.lower() in ('.flatpakref','.flatpak'):
                return self.launch('Flatpak Apps')
            if path.suffix.lower()=='.zip':
                view=ArchiveViewer(self);view.load(path);return self.window(path.name,view,(680,450))
            if path.suffix.lower() in ('.wav','.mp3','.ogg','.flac','.mp4','.webm','.mkv'):
                view=MediaPlayer(self);view.load(path);return self.window(path.name,view,(700,500))
            if path.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.bmp','.gif','.svg'):
                if path.stat().st_size>25*1024*1024:raise ValueError('The image is larger than the 25 MB viewer limit.')
                return self.window(path.name,ImageViewer(self,path),(760,540))
            if path.stat().st_size>3*1024*1024:raise ValueError('Macaque Text opens documents up to 3 MB.')
            view=SimpleText(self,path);self.add_recent(path);return self.window(path.name,view,(660,480))
        except (OSError,UnicodeError,ValueError) as ex:self.error(ex)
    def open_dialog(self):
        path,_=QFileDialog.getOpenFileName(self,'Open Text Document',str(self.disk.root/'Documents'),'Text (*.txt *.md *.log);;All files (*)')
        if path:self.open_document(path)
    def error(self,ex):self.play_sound('error');QMessageBox.warning(self,'Macaque Classic',str(ex))
    def operation(self,fn,sound='save'):
        try:result=fn();self.disk_changed.emit();self.play_sound(sound);return result
        except (OSError,ValueError,KeyError) as ex:self.error(ex)
    def launch(self,name,key=None):
        if name in ('Macaque Web','Workspaces','Welcome Center'):
            cls,size={'Macaque Web':(Browser,(1050,690)),'Workspaces':(WorkspaceOverview,(1060,440)),'Welcome Center':(Welcome,(690,560))}[name]
            for w in self.area.subWindowList():
                if isinstance(w.content,cls):self.activate_window(w);return w
            return self.window(name,cls(self),size)
        if name=='Downloads':
            for w in self.area.subWindowList():
                if isinstance(w.content,Downloads):self.activate_window(w);return w
            return self.window('Downloads',Downloads(self),(750,370))
        if name in ('Flatpak Apps','Classic Mac Apps'):
            size=(720,560) if name=='Flatpak Apps' else (650,600)
            cls=FlatpakApps if name=='Flatpak Apps' else ClassicMacApps
            for w in self.area.subWindowList():
                if isinstance(w.content,cls):self.activate_window(w);return w
            return self.window(name,cls(self),size)
        if name in ('Macaque Search','Backup & Recovery'):
            cls,size=(ClassicSearch,(660,510)) if name=='Macaque Search' else (Backups,(600,400))
            for w in self.area.subWindowList():
                if isinstance(w.content,cls):
                    self.activate_window(w)
                    if name=='Macaque Search':w.content.input.setFocus()
                    return w
            w=self.window(name,cls(self),size)
            if name=='Macaque Search':w.content.input.setFocus()
            return w
        if name=='Classic Sounds':return self.window('Classic Sounds',SoundPreferences(self),(560,570))
        if name=='Settings':return self.settings()
        if name=='Notifications':return self.notifications()
        extra={'Chess':(Chess,(610,660)),'Macaque Paint':(Paint,(850,610)),'Tasks':(Tasks,(460,480)),'Clockwork':(Clockwork,(480,440)),'Media Player':(MediaPlayer,(700,500)),'Archive Viewer':(ArchiveViewer,(650,440)),'Character Map':(Characters,(600,400)),'Teapot Studio':(Teapot,(690,540)),'Wallpapers':(Wallpapers,(740,540)),'Mouse':(MousePreferences,(550,540))}
        if name in extra:
            cls,size=extra[name]
            # One saved Tasks/Chess instance avoids competing autosaves.
            if name in ('Tasks','Chess'):
                for w in self.area.subWindowList():
                    if isinstance(w.content,cls):self.activate_window(w);return w
            return self.window(name,cls(self),size)
        if name in CREATIVE_APPS:
            if not hasattr(self,'creative_apps'):self.creative_apps=CreativeApps(self)
            return self.creative_apps.launch(name)
        if name in ('Battery & Power','USB Drives','Software Update'):
            from power_panel import PowerPanel
            from removable_drives import RemovableDrives
            from update_panel import Updates
            cls={'Battery & Power':PowerPanel,'USB Drives':RemovableDrives,'Software Update':Updates}[name]
            for w in self.area.subWindowList():
                if isinstance(w.content,cls):self.activate_window(w);return w
            return self.window(name,cls(self),(820,590))
        if name=='Terminal':return self.launch_terminal()
        if name=='Applications':return self.window('Macaque Applications',AppHub(self),(730,500))
        if name=='Macaque Files':return self.open_finder(self.disk.root)
        for title,cls in [('Sound',Sound),('Network',Network),('Storage',Storage),('System Monitor',Monitor),('Display',Display)]:
            if name==title:return self.window(title,cls(self),(780,500) if title=='Network' else (590,390))
        if name=='Macaque Text':return self.window('Untitled',SimpleText(self),(650,460))
        if name=='Macaque Notes':
            if key:
                for win in self.area.subWindowList():
                    if isinstance(win.content,Sticky) and win.content.key==key:self.activate_window(win);return win
            return self.window('Macaque Notes',Sticky(self,key),(330,270))
        if name=='Calculator':return self.window(name,Calculator(self),(310,360))
        if name=='Macaque Search':return self.window(name,Sherlock(self),(600,400))
        if name=='Macaque Tiles':return self.window(name,Puzzle(self),(330,350))
        if name=='Macaque Clips':return self.window(name,Scrapbook(self),(530,430))
        if name=='Memory':return self.memory()
        if name=='Desktop Disk':return self.text_window('Desktop Disk',f'Macaque HD lives at:\n{self.disk.root}\n\nAvailable: {self.format_bytes(self.free_space())}')
        if name=='Sound & Devices':return self.launch('Sound')
        if name=='Screen Saver':return self.screensaver()
        if name=='Appearance':return self.appearance()
        if name=='Date & Time':return self.calendar()
        if name=='Help Center':
            browser=QTextBrowser();browser.setHtml(HELP);return self.window('Macaque Help',browser,(720,540))
        if name=='About This Computer':return self.about()
    def system_menu(self):
        menu=self.top_bar.system;menu.clear();menu.addAction('About This Computer',self.about);menu.addAction('Welcome Center…',lambda:self.launch('Welcome Center'));menu.addSeparator()
        apps=menu.addMenu('Applications')
        for name in APP_NAMES:apps.addAction(icon(app_kind(name)),name,lambda checked=False,n=name:self.launch(n))
        menu.addAction('Settings…',self.settings);menu.addAction('Backup & Recovery…',lambda:self.launch('Backup & Recovery'));menu.addAction('Notifications…',self.notifications);menu.addAction('Control Panels…',self.control_panels)
        recent=menu.addMenu('Recent Documents')
        for path in self.recent:
            action=recent.addAction(Path(path).name,lambda checked=False,p=path:self.open_document(p));action.setEnabled(Path(path).exists())
        if not self.recent:recent.addAction('No recent documents').setEnabled(False)
        sticky=menu.addMenu('Macaque Notes');sticky.addAction('New Sticky',lambda:self.launch('Macaque Notes'))
        for key,text in self.stickies.items():sticky.addAction(text[:30].replace('\n',' ') or 'Untitled sticky',lambda checked=False,k=key:self.launch('Macaque Notes',key=k))
        menu.addSeparator();menu.addAction('Quit Desktop',self.close)
    def application_menu(self):
        menu=self.top_bar.appmenu;menu.clear();current=self.active();name=getattr(current,'app_name','Macaque Files');menu.addAction('About '+name,lambda:self.text_window('About '+name,f'{name}\nPart of Macaque Classic {VERSION}\n\nSee Help for keyboard shortcuts and usage.'))
        menu.addAction('Hide Window',lambda:self.area.activeSubWindow().showMinimized() if self.area.activeSubWindow() else None);menu.addAction('Close Window',self.close_active)
    def file_menu(self):
        m=self.top_bar.file;m.clear();content=self.active();m.addAction('New Text Document',lambda:self.launch('Macaque Text'));m.addAction('Open…',self.open_dialog)
        if isinstance(content,Finder):m.addAction('New Folder…',content.new_folder);m.addAction('Get Info',content.info);m.addSeparator();m.addAction('Rename…',content.rename_selected);m.addAction('Duplicate',content.duplicate_selected);m.addAction('Move to Trash',content.trash_selected)
        if isinstance(content,SimpleText):m.addSeparator();m.addAction('Save',content.save);m.addAction('Save As…',lambda:content.save(True))
        if isinstance(content,Finder) and not content.managed:
            for action in m.actions():
                if action.text() in ('New Folder…','Rename…','Duplicate','Move to Trash'):action.setEnabled(False)
        m.addSeparator();m.addAction('Close Window',self.close_active)
    def edit_menu(self):
        m=self.top_bar.edit;m.clear();current=self.active();editor=getattr(current,'editor',None)
        if isinstance(current,Finder):
            copy=m.addAction('Copy Item',lambda:self.copy_items([current.selected()]));copy.setEnabled(current.selected() is not None)
            paste=m.addAction('Paste Item',lambda:self.paste_items(current.path));paste.setEnabled(self.can_paste(current.path))
            m.addSeparator()
        for label,method in [('Undo','undo'),('Redo','redo'),('Cut','cut'),('Copy','copy'),('Paste','paste'),('Select All','selectAll')]:
            action=m.addAction(label,lambda checked=False,name=method,e=editor:getattr(e,name)() if e else None);action.setEnabled(editor is not None)
        m.addSeparator();m.addAction('Find…',self.find)
    def view_menu(self):
        m=self.top_bar.view;m.clear();current=self.active()
        if isinstance(current,Finder):m.addAction('Switch Icon / List View',current.toggle_view);m.addAction('Enclosing Folder',current.go_up)
        m.addAction('Dark Mode' if self.state.get('mode','light')!='dark' else 'Light Mode',self.toggle_dark);m.addAction('Search & Launch…',self.launch_palette);m.addAction('Clean Up Desktop',self.arrange_icons);m.addAction('Appearance…',self.appearance);m.addSeparator();m.addAction('Show Control Strip',lambda:self.native_strip.show() if self.native_strip else self.diagnostics());m.addAction('Full Screen',self.fullscreen)
    def special_menu(self):
        m=self.top_bar.special;m.clear();m.addAction('Empty Trash…',self.empty_trash);m.addAction('Manage Macaque Notes…',self.manage_stickies);m.addSeparator();m.addAction('Screen Saver Preview',self.screensaver);m.addAction('Restart Desktop…',self.restart);m.addAction('Quit Desktop',self.close)
    def window_menu(self,target=None):
        m=target or self.top_bar.windows;m.clear();m.addAction('Cascade Windows',self.area.cascadeSubWindows);m.addAction('Tile Windows',self.area.tileSubWindows);spaces=m.addMenu('Workspaces');self.workspace_menu(spaces);m.addAction('Snap Active Left',lambda:self.snap_window('left'));m.addAction('Snap Active Right',lambda:self.snap_window('right'));m.addAction('Show / Restore Desktop',self.show_desktop);m.addSeparator()
        for window in self.area.subWindowList():
            action=m.addAction(self.workspace_names()[window.property('workspace') or 0]+' / '+window.windowTitle(),lambda checked=False,w=window:self.activate_window(w));action.setCheckable(True);action.setChecked(window==self.area.activeSubWindow());action.setData(window)
    def save_active(self,save_as=False):
        content=self.active()
        if isinstance(content,SimpleText):content.save(save_as)
    def close_active(self):
        w=self.area.activeSubWindow()
        if w:w.close()
    def info_active(self):
        content=self.active()
        if isinstance(content,Finder):content.info()
    def find(self):
        content=self.active()
        if isinstance(content,SimpleText):content.find()
        else:self.launch('Macaque Search')
    def fullscreen(self):
        if os.environ.get('MACAQUE_NATIVE_SESSION')=='1':return self.text_window('Creative Session display','Resize the outer Xephyr window to change the session size. Use Alt+Tab to switch native apps.')
        self.showNormal() if self.isFullScreen() else self.showFullScreen()
    def get_info(self,path):
        try:
            st=path.stat();self.text_window('Get Info — '+path.name,f'{path.name}\n\nKind: {"Folder" if path.is_dir() else "Document"}\nSize: {self.format_bytes(st.st_size)}\nModified: {self.file_date(st.st_mtime)}\n\nLocation:\n{path}')
        except OSError as ex:self.error(ex)
    def text_window(self,title,text,size=(490,340)):
        box=QTextEdit();box.setReadOnly(True);box.setPlainText(text);return self.window(title,box,size)
    def about(self):
        panel=QWidget();layout=QHBoxLayout(panel);picture=QLabel();picture.setPixmap(icon('macaque',100).pixmap(100,100));layout.addWidget(picture);body=QLabel(f'<h2>Macaque Classic 0.29</h2><b>Macaque Desktop</b><p>Native Qt · Linux prototype<br>Classic Control Strip 2.0.6<br>Created with Drew Owen</p><p>Running: {platform.system()} {platform.machine()}<br>Target: Ryzen 7 + Radeon RX 6700 XT</p><p>Macaque Files · Control Panels · Macaque Text<br>Macaque Notes · Macaque Search · classic extras</p>');body.setWordWrap(True);layout.addWidget(body,1);return self.window('About This Computer',panel,(550,330))
    def control_panels(self):
        panel=QWidget();layout=QVBoxLayout(panel);grid=QGridLayout();layout.addLayout(grid)
        actions=[('Appearance','appearance',self.appearance),('Date & Time','clock',self.calendar),('Sound','computer',lambda:self.launch('Sound')),('Memory','computer',self.memory),('Desktop Disk','disk',lambda:self.text_window('Desktop Disk',f'Macaque HD is stored at:\n{self.disk.root}\n\nAvailable on host filesystem: {self.format_bytes(self.free_space())}')),('Screen Saver','computer',self.screensaver)]
        for i,(name,kind,fn) in enumerate(actions):
            b=QToolButton();b.setText(name);b.setIcon(icon(kind));b.setIconSize(QSize(48,48));b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);b.setMinimumSize(140,95);b.clicked.connect(fn);grid.addWidget(b,i//3,i%3)
        return self.window('Control Panels',panel,(500,300))
    def appearance(self):
        tabs=QTabWidget();desktop=QWidget();layout=QVBoxLayout(desktop);layout.addWidget(QLabel('Desktop mode'))
        mode=QComboBox();mode.addItems(['Light','Dark']);mode.setCurrentText(self.state.get('mode','light').title());mode.currentTextChanged.connect(lambda value:self.set_mode(value.lower()));layout.addWidget(mode)
        sync=QCheckBox('Match Control Strip to desktop mode');sync.setChecked(self.state.get('sync_strip',True));sync.toggled.connect(lambda value:self.set_preference('sync_strip',value));layout.addWidget(sync)
        compact=QCheckBox('Compact top bar');compact.setChecked(self.state.get('compact_bar',True));compact.toggled.connect(lambda value:self.set_preference('compact_bar',value));layout.addWidget(compact)
        layout.addWidget(QLabel('Accent color'));accents=QHBoxLayout();layout.addLayout(accents)
        for name,accent in [('Macaque Teal','#287f70'),('Ocean','#356cbd'),('Violet','#8657ba'),('Amber','#a36c15')]:
            button=QPushButton(name);button.clicked.connect(lambda checked=False,a=accent:self.change_appearance('accent',a));accents.addWidget(button)
        layout.addWidget(QLabel('Desktop colors'))
        colors=QHBoxLayout();layout.addLayout(colors)
        for name,color in [('Classic','#7385b8'),('Lagoon','#3c9195'),('Orchid','#817298'),('Graphite','#626873'),('Sage','#7b927c')]:
            b=QPushButton(name);b.clicked.connect(lambda checked=False,c=color:self.change_appearance('color',c));colors.addWidget(b)
        pattern=QComboBox();pattern.addItems(['Solid','Pinstripes','Dither','Grid']);pattern.setCurrentText(self.state.get('pattern','Solid'));pattern.currentTextChanged.connect(lambda value:self.change_appearance('pattern',value));layout.addWidget(QLabel('Desktop pattern'));layout.addWidget(pattern)
        wallpapers=QPushButton('Wallpaper Gallery…');wallpapers.clicked.connect(lambda:self.launch('Wallpapers'));layout.addWidget(wallpapers)
        mouse=QPushButton('Mouse Options…');mouse.clicked.connect(lambda:self.launch('Mouse'));layout.addWidget(mouse)
        layout.addWidget(QLabel('Window style: Macaque Classic with traffic-light controls\nControl Strip themes are customized in the strip itself.'));layout.addStretch();tabs.addTab(desktop,'Appearance')
        return self.window('Appearance',tabs,(650,520))
    def change_appearance(self,key,value):
        if key in ('color','pattern'):self.state['wallpaper']=''
        self.state[key]=value;self.apply_appearance()
    def calendar(self):
        panel=QWidget();layout=QVBoxLayout(panel);label=QLabel(QDateTime.currentDateTime().toString('dddd, MMMM d yyyy · h:mm AP'));layout.addWidget(label);cal=QCalendarWidget();layout.addWidget(cal);layout.addWidget(QLabel('Uses the host clock. Change the system time in your Linux settings.'));return self.window('Date & Time',panel,(480,370))
    def memory(self):
        text='Memory information is unavailable on this host.'
        try:
            lines=Path('/proc/meminfo').read_text().splitlines();wanted=[line for line in lines if line.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))];text='\n'.join(wanted)+'\n\nLinux manages application memory automatically.'
        except OSError:pass
        return self.text_window('Memory',text)
    def empty_trash(self):
        count=len(self.disk.trash_items())
        if not count:return QMessageBox.information(self,'Trash','The Trash is empty.')
        if QMessageBox.question(self,'Empty Trash?',f'Permanently remove {count} item(s) from the managed Trash? This cannot be undone.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.operation(self.disk.empty_trash,'empty')
    def manage_stickies(self):
        dialog=QDialog(self);dialog.setWindowTitle('Manage Macaque Notes');layout=QVBoxLayout(dialog);listing=QListWidget();layout.addWidget(listing)
        keys=list(self.stickies)
        for key in keys:listing.addItem(self.stickies[key][:60] or 'Untitled sticky')
        delete=QPushButton('Delete Selected Sticky…');layout.addWidget(delete)
        def remove():
            row=listing.currentRow()
            if row<0:return
            if QMessageBox.question(dialog,'Delete Sticky?','Permanently delete this sticky?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
            key=keys[row]
            for win in self.area.subWindowList():
                if isinstance(win.content,Sticky) and win.content.key==key:win.close()
            self.stickies.pop(key,None);self.persist();listing.takeItem(row);keys.pop(row)
        delete.clicked.connect(remove);dialog.exec()
    def screensaver(self):
        
        if self.saver:return
        self.saver=ScreenSaver(self.area.viewport());self.saver.destroyed.connect(lambda:setattr(self,'saver',None))
    def open_data(self):return self.open_finder(self.base)
    def diagnostics(self):self.text_window('Diagnostics',f'Macaque Classic {VERSION}\nPython {platform.python_version()}\nData: {self.base}\n\nControl Strip: '+getattr(self,'strip_error','native C++ widget loaded'))
    def restart(self):
        if self.installer_busy():return self.text_window('Installer running','Finish or cancel installation before restarting the desktop.')
        if os.environ.get('MACAQUE_NATIVE_SESSION')=='1':return self.text_window('Restart Creative Session','Save and quit your creative apps, close Macaque, then run bash run-creative.sh again.')
        if QMessageBox.question(self,'Restart Desktop?','Close and reopen Macaque Classic?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
        for window in self.area.subWindowList():
            if hasattr(window.content,'can_close') and not window.content.can_close():return
        self.persist();started,_=QProcess.startDetached(sys.executable,[str(Path(__file__).resolve())])
        if started:self.quitting=True;self.close()
    def closeEvent(self,event):
        if self.installer_busy():
            self.text_window('Installer running','Finish or cancel the installation wizard before ending the desktop session.');event.ignore();return
        if not self.quitting:
            for window in self.area.subWindowList():
                if hasattr(window.content,'can_close') and not window.content.can_close():event.ignore();return
        if not self.app_support.can_close():event.ignore();return
        if hasattr(self,'creative_apps') and not self.creative_apps.can_close():event.ignore();return
        self.persist();event.accept()

if __name__=='__main__':
    from PySide6.QtCore import QProcess
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts,True)
    QApplication.setAttribute(Qt.AA_DontUseNativeDialogs,True)
    app=QApplication(sys.argv);app.setApplicationName('MacaqueClassic');app.setOrganizationName('MacaqueOS');app.setStyle('Fusion');app.setStyleSheet(STYLE)
    palette=app.palette();palette.setColor(QPalette.Window,QColor('#d5d4d0'));palette.setColor(QPalette.WindowText,QColor('#202020'));palette.setColor(QPalette.Base,QColor('#fffefb'));palette.setColor(QPalette.Text,QColor('#202020'));palette.setColor(QPalette.Button,QColor('#d5d4d0'));palette.setColor(QPalette.ButtonText,QColor('#202020'));app.setPalette(palette)
    desktop=Desktop()
    if '--dark' in sys.argv:desktop.set_mode('dark')
    if '--light' in sys.argv:desktop.set_mode('light')
    if os.environ.get('MACAQUE_NATIVE_SESSION')=='1':
        desktop.setWindowFlags(Qt.Window|Qt.FramelessWindowHint|Qt.WindowStaysOnBottomHint)
        desktop.setGeometry(app.primaryScreen().availableGeometry())
    desktop.show()
    if '--screenshot' in sys.argv:
        def capture():
            desktop.launch('Applications').move(35,105);sound=desktop.launch('Sound');sound.move(805,455);sound.resize(500,300);desktop.grab().save(str(Path(__file__).parent/('preview-dark.png' if desktop.state.get('mode')=='dark' else 'preview-light.png')));desktop.quitting=True;app.quit()
        QTimer.singleShot(300,capture)
    sys.exit(app.exec())
