"""Embedded Qt WebEngine browser. Never disables Chromium's sandbox."""
import os
from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QTimer
from PySide6.QtWidgets import *
from downloads import download_name
HOME='https://www.gimp.org/downloads/'

from menu_compat import Menu as QMenu

def browser_url(text):
    text=text.strip()
    if not text:raise ValueError('Enter a website address.')
    if '://' not in text:text='https://'+text
    url=QUrl(text)
    if not url.isValid() or url.scheme() not in ('https','http') or not url.host() or url.userInfo():raise ValueError('Use an HTTP or HTTPS website address without embedded credentials.')
    return url

class Browser(QWidget):
    app_name='Macaque Web'
    def __init__(self,d):
        super().__init__();self.d=d;self.profile=None;self.window=None;self.available=False;self.pages=[];self.downloads=[];layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row)
        for text,method in [('Back','back'),('Forward','forward'),('Reload','reload')]:b=QPushButton(text);b.clicked.connect(lambda checked=False,m=method:self.navigate_action(m));row.addWidget(b)
        self.address=QLineEdit();self.address.setPlaceholderText('Website address…');self.address.returnPressed.connect(self.go);row.addWidget(self.address,1);go=QPushButton('Go');go.clicked.connect(self.go);row.addWidget(go);new=QPushButton('+');new.setToolTip('New tab');new.clicked.connect(lambda:self.new_tab());row.addWidget(new)
        self.tabs=QTabWidget();self.tabs.setTabsClosable(True);self.tabs.tabCloseRequested.connect(self.close_tab);self.tabs.currentChanged.connect(self.current_changed);layout.addWidget(self.tabs,1);self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status);footer=QHBoxLayout();layout.addLayout(footer)
        for text,url in [('GIMP',HOME),('Flathub','https://flathub.org/'),('Qt documentation','https://doc.qt.io/')]:b=QPushButton(text);b.clicked.connect(lambda checked=False,u=url:self.load(u));footer.addWidget(b)
        bookmarks=QPushButton('Bookmarks');bookmarks.clicked.connect(self.bookmarks);footer.addWidget(bookmarks);add=QPushButton('Bookmark page');add.clicked.connect(self.bookmark);footer.addWidget(add);download=QPushButton('Downloads');download.clicked.connect(lambda:d.launch('Downloads'));footer.addWidget(download)
        # Refuse insecure execution configurations instead of silently falling back.
        if hasattr(os,'geteuid') and os.geteuid()==0:self.status.setText('Web browsing requires a regular user account. Chromium sandboxing stays enabled.');return
        if os.environ.get('QTWEBENGINE_DISABLE_SANDBOX') or '--no-sandbox' in os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS',''):self.status.setText('Remove the sandbox-disabling WebEngine environment options before browsing.');return
        try:
            from PySide6.QtWebEngineCore import QWebEngineProfile,QWebEnginePage,QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView
            self.View=QWebEngineView;self.Page=QWebEnginePage
            self.profile=QWebEngineProfile(d);self.profile.downloadRequested.connect(self.request_download);self.available=True;self.new_tab();self.status.setText('Ready · browsing sessions are temporary; saved bookmarks and downloads persist.')
        except (ImportError,RuntimeError) as ex:self.status.setText('WebEngine is unavailable: '+str(ex))
    def attach(self,window):self.window=window
    def new_tab(self,url=None):
        if not self.available:return
        from PySide6.QtWebEngineCore import QWebEngineSettings
        browser=self
        class Page(self.Page):
            def acceptNavigationRequest(page,url,kind,main):
                if url.scheme() in ('https','http','data') or url.toString()=='about:blank':return True
                browser.status.setText('This browser opens HTTP/HTTPS pages only.');return False
            def createWindow(page,kind):return None # Site popups cannot escape the desktop.
        view=self.View();page=Page(self.profile,view);view.setPage(page);page.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled,False);page.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows,False)
        if hasattr(page,'permissionRequested'):page.permissionRequested.connect(lambda permission:permission.deny())
        else:page.featurePermissionRequested.connect(lambda origin,feature,p=page:p.setFeaturePermission(origin,feature,self.Page.PermissionDeniedByUser))
        page.certificateError.connect(lambda error:error.rejectCertificate());view.urlChanged.connect(lambda value,v=view:self.url_changed(v,value));view.titleChanged.connect(lambda title,v=view:self.title_changed(v,title));view.loadFinished.connect(lambda ok,v=view:self.loaded(v,ok));self.tabs.addTab(view,'New tab');self.tabs.setCurrentWidget(view);self.pages.append(page)
        if url:view.load(browser_url(url))
        else:view.setHtml('<html><body style="font-family:sans-serif;background:#183d40;color:#ecf4e8;padding:40px"><h1>Macaque Web</h1><p>Browse inside your Classic desktop.</p><p>Enter an address above, or choose GIMP or Flathub below.</p></body></html>',QUrl('about:blank'))
        return view
    def load(self,text):
        try:url=browser_url(text)
        except ValueError as ex:self.status.setText(str(ex));return
        if not self.available:return
        if not self.tabs.count():self.new_tab()
        self.tabs.currentWidget().load(url)
    def go(self):self.load(self.address.text())
    def navigate_action(self,method):
        if self.tabs.currentWidget():getattr(self.tabs.currentWidget(),method)()
    def url_changed(self,view,url):
        if view is self.tabs.currentWidget():self.address.setText(url.toString())
    def title_changed(self,view,title):
        index=self.tabs.indexOf(view)
        if index>=0:self.tabs.setTabText(index,(title or 'Web')[:24])
    def loaded(self,view,ok):
        if view is self.tabs.currentWidget():self.status.setText('Loaded. Downloads require a Save action; permissions and popups are disabled.' if ok else 'Page could not load. Check the address, network and TLS certificate.')
    def current_changed(self,index):
        view=self.tabs.widget(index)
        if view:self.address.setText(view.url().toString())
    def close_tab(self,index):
        view=self.tabs.widget(index)
        if view:view.stop();self.tabs.removeTab(index);page=view.page();self.pages.remove(page);page.deleteLater();view.deleteLater()
    def request_download(self,request):
        folder=self.d.disk.root/'Downloads';folder.mkdir(exist_ok=True)
        # Use explicit Save selection; do not auto-install website downloads.
        target,_=QFileDialog.getSaveFileName(self,'Save Web Download',str(folder/download_name(QUrl(request.url()))),'All files (*)')
        if not target:request.cancel();return
        request.setDownloadDirectory(str(Path(target).parent));request.setDownloadFileName(Path(target).name);self.downloads.append(request);request.isFinishedChanged.connect(lambda r=request:self.download_finished(r));request.accept();self.status.setText('Downloading: '+Path(target).name)
    def download_finished(self,request):
        from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
        if request.state()==QWebEngineDownloadRequest.DownloadCompleted:self.d.disk_changed.emit();self.d.play_sound('save');self.status.setText('Download saved. Open Downloads to browse or install it.')
        else:self.status.setText('Download stopped: '+request.interruptReasonString())
        if request in self.downloads:self.downloads.remove(request)
    def bookmark(self):
        view=self.tabs.currentWidget()
        if not view or view.url().scheme() not in ('http','https'):return
        item={'title':view.title() or view.url().host(),'url':view.url().toString()};items=self.d.state.setdefault('web_bookmarks',[])
        if not any(old['url']==item['url'] for old in items):items.append(item);self.d.state['web_bookmarks']=items[-100:];self.d.persist();self.status.setText('Bookmark saved.')
    def bookmarks(self):
        menu=QMenu(self)
        for item in self.d.state.get('web_bookmarks',[]):menu.addAction(item['title'],lambda checked=False,url=item['url']:self.load(url))
        if not menu.actions():menu.addAction('No saved bookmarks').setEnabled(False)
        menu.exec(self.mapToGlobal(self.rect().center()))
    def can_close(self):
        for request in list(self.downloads):request.cancel()
        while self.tabs.count():self.close_tab(0)
        return True
