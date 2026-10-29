"""Make the explicit embedding adapter; leave Drew's supplied source unchanged."""
from pathlib import Path
root=Path(__file__).parent
s=(root/'upstream-main.cpp').read_text()
def replace_function(signature,body):
    global s
    start=s.index(signature); opening=s.index('{',start+len(signature)); depth=1; i=opening+1
    # These replaced functions contain no brace characters inside string literals.
    while depth:
        depth += (s[i]=='{')-(s[i]=='}'); i+=1
    s=s[:opening+1]+'\n'+body+'\n    '+s[i-1:]
s=s.replace('#include <LayerShellQt/Window>','#include <QEvent>')
s=s.replace('ControlStrip() {','ControlStrip(QWidget *host = nullptr) : QWidget(host) {')
s=s.replace('setWindowFlags(Qt::FramelessWindowHint | Qt::Tool);','setWindowFlags(host ? Qt::Widget : (Qt::FramelessWindowHint | Qt::Tool));\n        if (host) host->installEventFilter(this);')
replace_function('void configureLayerShell()', '        applyPosition();')
replace_function('int maximumOffset() const', '        return qMax(0, (parentWidget() ? parentWidget()->width() : 1920) - width());')
replace_function('int maximumBottomOffset() const', '        return qMax(0, (parentWidget() ? parentWidget()->height() : 1080) - height());')
replace_function('void applyPosition()', '''        if (!parentWidget()) return;
        leftOffset = qBound(0, leftOffset, maximumOffset());
        bottomOffset = qBound(0, bottomOffset, maximumBottomOffset());
        move(leftOffset, qMax(0,parentWidget()->height()-height()-bottomOffset));
        raise();''')
s=s.replace('LayerShellQt::Window *layerWindow = nullptr;', '')
s=s.replace('"ClassicControlStrip"','"ClassicControlStripDesktop"')
replace_function('void addSessionActions(QMenu &menu)', '''        menu.addSeparator();
        menu.addAction("Restart Control Strip", this, [this] { setProperty("restartRequested",true); });
        menu.addAction("Hide Control Strip", this, [this] { hide(); });''')
replace_function('void setAutostart(bool enabled)', '        Q_UNUSED(enabled); // Embedded strip follows the prototype; never edit host autostart.')
replace_function('bool autostartEnabled() const', '        return false;')
s=s.replace('startup->setChecked(true);','startup->setChecked(false);')
s=s.replace('layout->addWidget(startup);','startup->setEnabled(false); startup->setToolTip("Embedded strip starts with Classic Desktop"); layout->addWidget(startup);')
s=s.replace('form->addRow("Startup:",startup);','startup->setChecked(false); startup->setEnabled(false); form->addRow("Startup:",startup);')
s=s.replace('form->addRow("Display:",monitor);','monitor->setEnabled(false); monitor->setToolTip("Embedded strip follows the prototype window"); form->addRow("Display:",monitor);')
s=s.replace('const int screenWidth = screen ? screen->geometry().width() : 1920;', 'const int screenWidth = parentWidget() ? parentWidget()->width() : (screen ? screen->geometry().width() : 1920);')
s=s.replace('setFixedSize(expanded ? activeWidth() : 24, stripHeightPx);\n        } else', 'setFixedSize(expanded ? activeWidth() : 24, stripHeightPx);\n            applyPosition();\n        } else')
s=s.replace('protected:\n    void paintEvent', '''protected:
    bool eventFilter(QObject *watched, QEvent *event) override {
        if (watched == parentWidget() && event->type() == QEvent::Resize) applyPosition();
        return QWidget::eventFilter(watched,event);
    }
    void paintEvent''',1)
# Normalize stale 2.0.3 labels in the supplied 2.0.6 source.
s=s.replace('2.0.3','2.0.6').replace('Version 2.0 · MacaqueOS Edition','Version 2.0.6 · MacaqueOS Edition')
s=s[:s.index('int main(int argc,char **argv)')]+'''extern "C" QWidget *classic_strip_create(QWidget *parent) {
    auto *strip = new ControlStrip(parent);
    strip->configureLayerShell();
    strip->show();
    return strip;
}
extern "C" const char *classic_strip_qt_version() { return QT_VERSION_STR; }
'''
# Macaque branding and a small bridge for shared desktop appearance/audio controls.
s=s.replace('enum class Theme { Classic = 0, Light = 1, Dark = 2 };','enum class Theme { Classic = 0, Light = 1, Dark = 2 };\n    void setDesktopTheme(int value) { setTheme(static_cast<Theme>(qBound(0,value,2))); }\n    int desktopTheme() const { return int(theme); }')
s=s.replace('AppleTalk-style Network Controls','Network Links').replace('AppleTalk itself is not available on modern Linux','Host network connection information').replace('"AppleTalk"','"Network Links"')
s=s.replace('A classic Macintosh-inspired control bar','A native Macaque control bar').replace('An independent homage, not affiliated with Apple.','An independent Macaque desktop component.')
s=s.replace('Attach to left screen edge (Mac OS 9)','Attach to left screen edge').replace('Macintosh pinstripes','Macaque pinstripes').replace('Macintosh Light','Macaque Light').replace('classic Mac OS 9 Control Strip','Macaque Control Strip')
s=s.replace('Classic App Viewer','Macaque App Viewer')
s += '\nextern "C" void classic_strip_set_theme(QWidget *strip, int mode) { static_cast<ControlStrip*>(strip)->setDesktopTheme(mode); }\nextern "C" int classic_strip_theme(QWidget *strip) { return static_cast<ControlStrip*>(strip)->desktopTheme(); }\nextern "C" int classic_strip_read_volume() { return readVolume(); }\nextern "C" void classic_strip_write_volume(int value) { writeVolume(value); }\n'
# Route every UI application request into Macaque rather than spawning host GUIs.
s=s.replace('#include <QEvent>','#include <QEvent>\n#include <QQueue>')
helper='''QQueue<QByteArray> macaqueRequests;
bool requestProgram(const QString &program, const QStringList &args = {}) {
    QJsonArray list; for (const auto &arg : args) list.append(arg);
    QJsonObject event; event["program"]=program; event["args"]=list;
    if (macaqueRequests.size()<100) macaqueRequests.enqueue(QJsonDocument(event).toJson(QJsonDocument::Compact));
    return true;
}
'''
s=s.replace('bool hasCommand(const QString &cmd)',helper+'\nbool hasCommand(const QString &cmd)')
replace_function('void launch(const QString &program, const QStringList &args = {})','    requestProgram(program,args);')
s=s.replace('QProcess::startDetached(', 'requestProgram(')
# Audio backends are background commands, not host application launches.
replace_function('void writeVolume(int value)', '''    value=qBound(0,value,100);
    if(hasCommand("wpctl")) QProcess::startDetached("wpctl",{"set-volume","@DEFAULT_AUDIO_SINK@",QString::number(value)+"%"});
    else if(hasCommand("pactl")) QProcess::startDetached("pactl",{"set-sink-volume","@DEFAULT_SINK@",QString::number(value)+"%"});''')
replace_function('QVector<DesktopApp> installedApps() const', '''    return {
        {"macaque:files","Macaque Files","System","Macaque Files","folder",""},
        {"macaque:text","Macaque Text","Office","Macaque Text","text-editor",""},
        {"macaque:notes","Macaque Notes","Office","Macaque Notes","text-editor",""},
        {"macaque:calc","Calculator","Utility","Calculator","accessories-calculator",""},
        {"macaque:search","Macaque Search","Utility","Macaque Search","system-search",""},
        {"macaque:tiles","Macaque Tiles","Game","Macaque Tiles","applications-games",""},
        {"macaque:clips","Macaque Clips","Office","Macaque Clips","edit-paste",""},
        {"macaque:appearance","Appearance","Settings","Appearance","preferences-desktop-theme",""},
        {"macaque:network","Network","Settings","Network","network-workgroup",""},
        {"macaque:sound","Sound","Settings","Sound","audio-volume-high",""},
        {"macaque:display","Display","Settings","Display","video-display",""},
        {"macaque:monitor","System Monitor","System","System Monitor","utilities-system-monitor",""},
        {"macaque:storage","Storage","System","Storage","drive-harddisk",""},
        {"macaque:calendar","Date & Time","Utility","Date & Time","office-calendar",""},
        {"macaque:help","Help Center","Utility","Help Center","help-browser",""}
    };''')
replace_function('void launchDesktopApp(const DesktopApp &app)', '''    requestProgram("macaque-app",{app.exec});
    QSettings settings("MacaqueOS","ClassicControlStripDesktop");
    auto recent=settings.value("appViewerRecent").toStringList();recent.removeAll(app.id);recent.prepend(app.id);
    while(recent.size()>10)recent.removeLast();settings.setValue("appViewerRecent",recent);''')
replace_function('void showAppViewer()', '    requestProgram("macaque-app",{"Applications"});')
s=s.replace('QDesktopServices::openUrl(QUrl::fromLocalFile(folder));','requestProgram("macaque-folder",{folder});')
s+='''\nextern "C" const char *classic_strip_take_request() {
    static QByteArray current;
    if(macaqueRequests.isEmpty())return nullptr;
    current=macaqueRequests.dequeue();return current.constData();
}
'''

# Run the native strip's own settings dialogs as embedded content while its
# original synchronous accept/reject code remains alive on the C++ stack.
s=s.replace('#include <QQueue>','#include <QQueue>\n#include <QEventLoop>')
s=s.replace('bool hasCommand(const QString &cmd)', '''int execInternal(QDialog &dialog) {
    QEventLoop loop;
    QObject::connect(&dialog,&QDialog::finished,&loop,&QEventLoop::quit);
    requestProgram("macaque-dialog",{QString::number(quintptr(&dialog))});
    QTimer::singleShot(5000,&dialog,[&dialog]{if(!dialog.property("macaqueEmbedded").toBool())dialog.reject();});
    loop.exec();
    return dialog.result();
}
bool hasCommand(const QString &cmd)''')
s=s.replace('dialog.exec()','execInternal(dialog)').replace('box.exec()','execInternal(box)')

# A persistent Terminal cell, separate from the application launcher.
s=s.replace('constexpr int moduleCount = 12;', 'constexpr int moduleCount = 13;')
s=s.replace('"App Viewer"};', '"App Viewer", "Terminal"};')
s=s.replace('(id < 8 || id == 11)', '(id < 8 || id == 11 || id == 12)')
s=s.replace('    case 11: { // retro application grid', '    case 12: {\n        p.setBrush(QColor("#172127")); p.setPen(QColor("#dde8ee")); p.drawRect(1,2,23,19);\n        p.drawLine(5,7,10,11); p.drawLine(10,11,5,15); p.drawLine(13,15,20,15); break;\n    }\n    case 11: { // retro application grid')
s=s.replace('        if (index==11) {', '        if (index==12) { requestProgram("macaque-app",{"Terminal"}); return; }\n        if (index==11) {')
(root/'embedded-strip.cpp').write_text(s)
