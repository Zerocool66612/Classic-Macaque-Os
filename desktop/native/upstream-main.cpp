#include <QApplication>
#include <cmath>
#include <QLockFile>
#include <QThread>
#include <QCoreApplication>
#include <QWidget>
#include <QPainter>
#include <QMouseEvent>
#include <QScreen>
#include <QMenu>
#include <QWindow>
#include <QGuiApplication>
#include <QDebug>
#include <QMargins>
#include <QPolygon>
#include <QProcess>
#include <QSlider>
#include <QLabel>
#include <QVBoxLayout>
#include <QWidgetAction>
#include <QStandardPaths>
#include <QTimer>
#include <QRegularExpression>
#include <QDir>
#include <QSettings>
#include <QCursor>
#include <QStyleFactory>
#include <QDateTime>
#include <QFile>
#include <QMessageBox>
#include <QContextMenuEvent>
#include <LayerShellQt/Window>
#include <QInputDialog>
#include <QActionGroup>
#include <QStorageInfo>
#include <QFileInfo>
#include <QTextStream>
#include <QVector>
#include <QCheckBox>
#include <QComboBox>
#include <QDialog>
#include <QDialogButtonBox>
#include <QHBoxLayout>
#include <QDesktopServices>
#include <QUrl>
#include <QSaveFile>
#include <QBuffer>
#include <QProgressBar>
#include <QMap>
#include <QColor>
#include <QImageReader>
#include <QPixmap>
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonDocument>
#include <QColorDialog>
#include <QFileDialog>
#include <QPushButton>
#include <QToolButton>
#include <QGridLayout>
#include <QScrollArea>
#include <QGroupBox>
#include <QFrame>
#include <QListWidget>
#include <QListWidgetItem>
#include <QSpinBox>
#include <QFormLayout>
#include <QFileDialog>
#include <QCryptographicHash>
#include <QWizard>
#include <QWizardPage>
#include <QRadioButton>
#include <QDirIterator>
#include <algorithm>
#include <QLineEdit>
#include <QTabWidget>
#include <QSet>
#include <QIcon>

namespace {
constexpr int stripHeight = 34;
constexpr int moduleWidth = 42;
constexpr int moduleStep = 43;
constexpr int moduleCount = 12;
constexpr int stripWidth = 24 + moduleStep * moduleCount + 2;
const QStringList moduleNames = {"Display", "Clock", "Folders", "Lock", "Appearance", "Sound", "Network", "Storage", "CD / DVD", "Memory", "AppleTalk", "App Viewer"};
QString readText(const QString &path) { QFile f(path); return f.open(QIODevice::ReadOnly) ? QString::fromUtf8(f.readAll()).trimmed() : QString(); }



// Crisp 1-pixel Platinum borders, deliberately without antialiasing.
void bevel(QPainter &p, const QRect &r, bool inset = false) {
    p.setPen(inset ? QColor(96,96,96) : QColor(255,255,255));
    p.drawLine(r.left(),r.bottom()-1,r.left(),r.top());
    p.drawLine(r.left(),r.top(),r.right()-1,r.top());
    p.setPen(inset ? QColor(248,248,248) : QColor(92,92,92));
    p.drawLine(r.left(),r.bottom(),r.right(),r.bottom());
    p.drawLine(r.right(),r.top(),r.right(),r.bottom());
}

// All module art is painted as unfiltered pixels, not themed system icons.
void icon(QPainter &p, int type, int x, int y) {
    p.save(); p.translate(x,y);
    const QColor ink(28,28,28), shade(109,109,109), shine(255,255,255);
    p.setPen(ink);
    switch(type) {
    case 0: { // 1990s compact Macintosh: case, screen, vents and stand
        p.setBrush(QColor(224,215,194)); p.drawRect(2,0,19,17);
        p.setBrush(QColor(46,80,116)); p.drawRect(5,3,13,10);
        p.setPen(QColor(148,197,222)); p.drawLine(6,4,16,4);
        p.setPen(shade); p.drawLine(4,15,19,15);
        p.setPen(ink); p.setBrush(QColor(192,186,173)); p.drawRect(8,18,7,2);
        p.drawLine(6,21,17,21); break;
    }
    case 1: { // clock with hand-drawn ticks
        p.setBrush(QColor(253,253,248)); p.drawEllipse(2,1,19,19);
        p.drawPoint(11,3); p.drawPoint(11,17); p.drawPoint(4,10); p.drawPoint(18,10);
        p.drawLine(11,10,11,5); p.drawLine(11,10,16,13);
        p.setBrush(ink); p.drawRect(10,9,2,2); break;
    }
    case 2: { // classic tabbed folder with shaded lip
        p.setBrush(QColor(223,179,73)); p.drawRect(2,6,20,13);
        p.setBrush(QColor(246,215,117)); p.drawRect(3,4,9,4);
        p.setBrush(QColor(255,227,141)); p.drawRect(3,8,18,9);
        p.setPen(QColor(154,109,41)); p.drawLine(4,9,20,9);
        p.setPen(shine); p.drawLine(4,10,4,16); break;
    }
    case 3: { // security padlock
        p.setBrush(Qt::NoBrush); p.setPen(QPen(ink,2));
        p.drawArc(6,1,12,16,0,180*16);
        p.setPen(ink); p.setBrush(QColor(198,198,198)); p.drawRect(4,9,16,12);
        p.setPen(shine); p.drawLine(5,10,18,10);
        p.setPen(ink); p.setBrush(ink); p.drawRect(11,13,2,5); break;
    }
    case 4: { // colorful original-era control-panel palette
        p.setBrush(QColor(254,244,214)); p.drawEllipse(2,1,19,19);
        p.setPen(Qt::NoPen);
        p.setBrush(QColor(198,53,48)); p.drawRect(7,4,4,4);
        p.setBrush(QColor(45,85,170)); p.drawRect(14,7,4,4);
        p.setBrush(QColor(53,136,76)); p.drawRect(5,11,4,4);
        p.setBrush(QColor(229,164,47)); p.drawRect(12,14,4,4);
        p.setPen(ink); p.setBrush(QColor(218,218,218)); p.drawEllipse(10,8,4,4); break;
    }
    case 5: { // square-wave-era speaker
        p.setBrush(QColor(113,113,113)); p.drawRect(1,8,6,7);
        p.drawPolygon(QPolygon({QPoint(6,8),QPoint(14,3),QPoint(14,19),QPoint(6,15)}));
        p.setBrush(Qt::NoBrush); p.drawArc(11,5,9,12,-72*16,144*16);
        p.drawArc(10,2,14,18,-72*16,144*16); break;
    }
    case 6: { // pixel globe with longitudinal highlight
        p.setBrush(QColor(65,119,187)); p.drawEllipse(2,1,19,19);
        p.setPen(QColor(170,211,244)); p.drawArc(6,2,10,17,75*16,200*16);
        p.setPen(Qt::NoPen); p.setBrush(QColor(94,162,84));
        p.drawPolygon(QPolygon({QPoint(6,3),QPoint(12,3),QPoint(12,8),QPoint(8,11),QPoint(4,8)}));
        p.drawPolygon(QPolygon({QPoint(13,11),QPoint(20,10),QPoint(18,16),QPoint(13,19),QPoint(11,15)})); break;
    }
    case 7: { // metallic hard disk with status LED
        p.setBrush(QColor(195,195,195)); p.drawRect(2,4,20,15);
        p.setPen(shine); p.drawLine(3,5,20,5);
        p.setPen(shade); p.drawLine(3,9,21,9); p.drawLine(3,17,20,17);
        p.setPen(ink); p.setBrush(QColor(55,159,68)); p.drawRect(17,13,2,2);
        p.drawLine(5,12,12,12);
        p.setPen(QColor(92,92,92)); p.drawLine(5,15,14,15); break;
    }
    case 8: { // compact disc in jewel-case style
        p.setBrush(QColor(244,244,247)); p.drawEllipse(2,1,21,21);
        p.setBrush(QColor(128,179,208)); p.drawEllipse(6,5,13,13);
        p.setBrush(QColor(240,240,240)); p.drawEllipse(10,9,5,5);
        p.setPen(shine); p.drawLine(6,5,16,15);
        p.setPen(QColor(109,109,109)); p.drawPoint(12,11);
        p.setPen(QColor(208,171,218)); p.drawLine(5,14,10,18); break;
    }
    case 9: { // RAM chip with visible pins
        p.setBrush(QColor(50,123,68)); p.drawRect(2,5,21,13);
        p.setBrush(QColor(30,30,30)); p.drawRect(6,7,12,9);
        p.setPen(QColor(220,188,91));
        for (int i=4;i<22;i+=4) { p.drawLine(i,3,i,5); p.drawLine(i,18,i,21); }
        break;
    }
    case 11: { // retro application grid
        p.setPen(QColor(48,48,48));
        for (int row=0; row<2; ++row) for (int col=0; col<2; ++col) {
            p.setBrush(QColor((col ? 77 : 211), (row ? 153 : 199), (col ? 193 : 102)));
            p.drawRect(2+col*11,2+row*11,9,9);
        }
        break;
    }
    case 10: { // classic connected network nodes
        p.setPen(QPen(ink,2)); p.drawLine(12,5,5,16); p.drawLine(12,5,20,16);
        p.drawLine(5,16,20,16);
        p.setPen(ink); p.setBrush(QColor(233,220,170));
        p.drawRect(8,1,8,7); p.drawRect(1,14,8,7); p.drawRect(16,14,8,7);
        break;
    }
    }
    p.restore();
}

const char *platinumMenuStyle = R"(
 QMenu { background:#d6d6d6; color:#111111; border:1px solid #3b3b3b;
         padding:3px; font-family:'DejaVu Sans',sans-serif; font-size:11px; }
 QMenu::item { padding:3px 20px 3px 17px; margin:1px; }
 QMenu::item:selected { background:#333399; color:white; }
 QMenu::item:disabled { color:#777777; }
 QMenu::separator { height:1px; background:#999999; margin:4px 7px; }
 QSlider::groove:horizontal { height:5px; background:#aaaaaa; border:1px solid #555555; }
 QSlider::handle:horizontal { background:#eeeeee; border:1px solid #444444;
                               width:12px; margin:-5px 0; }
)";

bool hasCommand(const QString &cmd) { return !QStandardPaths::findExecutable(cmd).isEmpty(); }
void launch(const QString &program, const QStringList &args = {}) { if (hasCommand(program)) QProcess::startDetached(program, args); }
void toggleMute() {
    if (hasCommand("wpctl")) launch("wpctl", {"set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"});
    else if (hasCommand("pactl")) launch("pactl", {"set-sink-mute", "@DEFAULT_SINK@", "toggle"});
}

int readVolume() {
    QProcess p;
    if (hasCommand("wpctl")) {
        p.start("wpctl", {"get-volume", "@DEFAULT_AUDIO_SINK@"});
        if (p.waitForFinished(1500) && p.exitCode()==0) {
            const QString s = QString::fromUtf8(p.readAllStandardOutput());
            QRegularExpression rx("Volume:\\s*([0-9.]+)");
            auto m = rx.match(s);
            if (m.hasMatch()) return qBound(0, qRound(m.captured(1).toDouble()*100), 100);
        }
    }
    if (hasCommand("pactl")) {
        p.start("pactl", {"get-sink-volume", "@DEFAULT_SINK@"});
        if (p.waitForFinished(1500) && p.exitCode()==0) {
            QRegularExpression rx("(\\d+)%");
            auto m = rx.match(QString::fromUtf8(p.readAllStandardOutput()));
            if (m.hasMatch()) return qBound(0,m.captured(1).toInt(),100);
        }
    }
    return 50;
}
void writeVolume(int value) {
    value=qBound(0,value,100);
    if (hasCommand("wpctl")) QProcess::startDetached("wpctl", {"set-volume", "@DEFAULT_AUDIO_SINK@", QString::number(value)+"%"});
    else if (hasCommand("pactl")) QProcess::startDetached("pactl", {"set-sink-volume", "@DEFAULT_SINK@", QString::number(value)+"%"});
}
}

class ControlStrip : public QWidget {
public:
    enum class Theme { Classic = 0, Light = 1, Dark = 2 };
    ControlStrip() {
        setWindowFlags(Qt::FramelessWindowHint | Qt::Tool);
        setAttribute(Qt::WA_TranslucentBackground);
        setMouseTracking(true);
        setFixedSize(stripWidth, stripHeightPx);
        setToolTip("Classic Control Strip 2.0.3 — drag handle in any direction; right-click for position controls");
        QSettings settings("MacaqueOS", "ClassicControlStrip");
        theme = static_cast<Theme>(qBound(0, settings.value("appearanceTheme", 0).toInt(), 2));
        accent = QColor(settings.value("accentColor", "#333399").toString());
        if (!accent.isValid()) accent = QColor("#333399");
        const QStringList savedIcons = settings.value("customIconPaths").toStringList();
        for (int id=0; id<qMin(moduleCount, savedIcons.size()); ++id) {
            if (!savedIcons.at(id).isEmpty() && QFileInfo::exists(savedIcons.at(id)))
                customIconPaths[id] = savedIcons.at(id);
        }
        leftOffset = qMax(0, settings.value("leftOffset", 0).toInt());
        bottomOffset = qMax(0, settings.value("bottomOffset", 0).toInt());
        dockedToLeft = settings.value("dockedToLeft", false).toBool();
        if (dockedToLeft) { freeLeftOffset = leftOffset; freeBottomOffset = bottomOffset; leftOffset = 0; bottomOffset = 0; }
        const QVariantList saved = settings.value("moduleOrder").toList();
        for (const QVariant &item : saved) {
            int id = item.toInt();
            if (id >= 0 && id < moduleCount && !order.contains(id)) order.append(id);
        }
        for (int id=0; id<moduleCount; ++id) if (!order.contains(id)) order.append(id);
        for (int id=0; id<moduleCount; ++id) visible[id] = settings.value(QString("module%1Visible").arg(id), (id < 8 || id == 11)).toBool();
        stripHeightPx = qBound(28, settings.value("creatorHeight",34).toInt(), 56);
        moduleStepPx = qBound(43, settings.value("creatorSpacing",43).toInt(), 66);
        customSurface = QColor(settings.value("creatorSurface","").toString());
        customModuleSurface = QColor(settings.value("creatorModuleSurface","").toString());
        customBorder = QColor(settings.value("creatorBorder","").toString());
        backgroundPattern = qBound(0,settings.value("creatorPattern",0).toInt(),4);
        backgroundTexturePath = settings.value("creatorTexture","").toString();
        updateSize();
    }

    // Keep the tested v0.5 Wayland setup unchanged.
    void maybeShowFirstRun() {
        QSettings settings("MacaqueOS","ClassicControlStrip");
        if (settings.value("firstRunCompleted",false).toBool()) return;
        if (hasPreviousAppearanceSettings()) {
            settings.setValue("firstRunCompleted",true); // Upgrade: preserve existing look.
            return;
        }
        QTimer::singleShot(200,this,[this]{showFirstRunWizard();});
    }
    void configureLayerShell() {
        QWindow *w = windowHandle();
        if (!w) { qWarning() << "No QWindow handle"; return; }
        QScreen *target = nullptr;
        const QString preferred = QSettings("MacaqueOS", "ClassicControlStrip")
                                    .value("preferredMonitor").toString();
        for (auto *screen : QGuiApplication::screens()) {
            if (!preferred.isEmpty() && screen->name() == preferred) {
                target = screen; break;
            }
        }
        // Preserve the original DP-2 default when no monitor was selected.
        if (!target && preferred.isEmpty())
            for (auto *screen : QGuiApplication::screens())
                if (screen->name() == QStringLiteral("DP-2")) {
                    target = screen; break;
                }
        if (!target) target = QGuiApplication::primaryScreen();
        if (target) w->setScreen(target);
        auto *layer = LayerShellQt::Window::get(w);
        if (!layer) { qWarning() << "LayerShellQt unavailable"; return; }
        layer->setLayer(LayerShellQt::Window::LayerTop);
        LayerShellQt::Window::Anchors anchors;
        anchors.setFlag(LayerShellQt::Window::AnchorLeft);
        anchors.setFlag(LayerShellQt::Window::AnchorBottom);
        layer->setAnchors(anchors);
        layerWindow = layer;
        leftOffset = qBound(0, leftOffset, maximumOffset());
        bottomOffset = qBound(0, bottomOffset, maximumBottomOffset());
        applyPosition();
        layer->setExclusiveZone(0);
        layer->setKeyboardInteractivity(LayerShellQt::Window::KeyboardInteractivityNone);
        qInfo() << "Control Strip configured for" << (target ? target->name() : QStringLiteral("unknown"));
    }
protected:
    void paintEvent(QPaintEvent *) override {
        QPainter p(this);
        p.setRenderHint(QPainter::Antialiasing, false);
        const bool dark = theme == Theme::Dark;
        const bool light = theme == Theme::Light;
        const QColor surface = dark ? QColor(54,57,65) : (light ? QColor(239,239,239) : QColor(204,204,204));
        const QColor moduleSurface = dark ? QColor(66,70,80) : (light ? QColor(247,247,247) : QColor(207,207,207));
        const QColor highlight = dark ? QColor(124,130,143) : QColor(255,255,255);
        const QColor shadow = dark ? QColor(18,20,26) : QColor(80,80,80);
        const QColor ink = dark ? QColor(238,238,242) : QColor(24,24,24);
        const QColor paintedSurface = customSurface.isValid() ? customSurface : surface;
        const QColor paintedModule = customModuleSurface.isValid() ? customModuleSurface : moduleSurface;
        const QColor paintedBorder = customBorder.isValid() ? customBorder : shadow;
        // Compact Platinum bar: two-tone raised frame, hairline shadow and lip.
        p.fillRect(rect(), paintedSurface);
        if (backgroundPattern == 4 && !backgroundTexturePath.isEmpty()) {
            QPixmap texture(backgroundTexturePath);
            if (!texture.isNull()) p.drawTiledPixmap(rect(),texture);
        } else if (backgroundPattern >= 1 && backgroundPattern <= 3) {
            QColor patternInk = paintedSurface.lightness() < 125
                ? QColor(255,255,255,28) : QColor(0,0,0,28);
            p.setPen(patternInk);
            for (int y=3; y<height()-3; ++y)
                for (int x=3; x<width()-3; ++x) {
                    bool on = backgroundPattern == 1 ? ((x+y)%4==0)
                        : backgroundPattern == 2 ? ((x/3+y/3)%2==0)
                        : (y%4==0);
                    if (on) p.drawPoint(x,y);
                }
        }
        // A fine dithered Platinum texture along the upper edge.
        p.setPen(dark ? QColor(73,77,88) : (light ? QColor(221,221,221) : QColor(189,189,189)));
        for (int tx=4; tx<width()-3; tx+=2) p.drawPoint(tx,1);
        p.setPen(highlight);
        p.drawLine(0,0,width()-2,0); p.drawLine(0,0,0,height()-2);
        p.setPen(paintedBorder);
        p.drawLine(width()-1,0,width()-1,height()-1);
        p.drawLine(0,height()-1,width()-1,height()-1);
        p.setPen(dark ? QColor(106,110,124) : QColor(236,236,236)); p.drawLine(2,2,width()-3,2);
        p.setPen(dark ? QColor(25,26,31) : QColor(120,120,120)); p.drawLine(1,height()-2,width()-2,height()-2);
        p.setPen(dark ? QColor(33,35,41) : QColor(148,148,148)); p.drawLine(2,height()-3,width()-3,height()-3);

        // A recessed, textured grip with the original directional wedge.
        const QRect handle(3,3,18,stripHeightPx-7);
        p.fillRect(handle,dark ? QColor(43,46,54) : (light ? QColor(223,223,223) : QColor(185,185,185)));
        if (dark) {
            p.setPen(paintedBorder); p.drawLine(handle.topLeft(),handle.topRight());
            p.drawLine(handle.topLeft(),handle.bottomLeft());
            p.setPen(highlight); p.drawLine(handle.bottomLeft(),handle.bottomRight());
            p.drawLine(handle.topRight(),handle.bottomRight());
        } else bevel(p,handle,true);
        for (int gx=6; gx<=10; gx+=4) {
            p.setPen(dark ? QColor(20,21,25) : QColor(98,98,98)); p.drawLine(gx,7,gx,stripHeightPx-9);
            p.setPen(highlight); p.drawLine(gx+1,7,gx+1,stripHeightPx-9);
        }
        p.setPen(ink); p.setBrush(ink);
        if (expanded) p.drawPolygon(QPolygon({QPoint(13,12),QPoint(18,17),QPoint(13,22)}));
        else p.drawPolygon(QPolygon({QPoint(18,12),QPoint(13,17),QPoint(18,22)}));
        if (dragging && (qAbs(previewOffset-dragStartOffset)>=4 || qAbs(previewBottomOffset-dragStartBottomOffset)>=4)) {
            p.setPen(QPen(QColor(48,48,48),1,Qt::DashLine));
            p.drawRect(rect().adjusted(2,2,-3,-3));
        }
        if (!expanded) return;
        const QVector<int> modules=activeModules();
        for (int i=0; i<modules.size(); ++i) {
            const int x=24+i*moduleStepPx;
            QRect cell(x,3,moduleWidth,stripHeightPx-7);
            p.fillRect(cell,paintedModule);
            p.setPen(highlight); p.drawLine(cell.left()+2,cell.top()+2,cell.right()-2,cell.top()+2);
            // Double-edged raised module with darker separator, like OS 9.
            p.setPen(highlight);
            p.drawLine(cell.left(),cell.bottom()-1,cell.left(),cell.top());
            p.drawLine(cell.left(),cell.top(),cell.right()-1,cell.top());
            p.setPen(paintedBorder);
            p.drawLine(cell.right(),cell.top(),cell.right(),cell.bottom());
            p.drawLine(cell.left(),cell.bottom(),cell.right(),cell.bottom());
            p.setPen(dark ? QColor(33,35,40) : QColor(166,166,166));
            p.drawLine(cell.right()-1,cell.top()+2,cell.right()-1,cell.bottom()-2);
            const int moduleId = modules.at(i);
            const QString customPath = customIconPaths.value(moduleId);
            QPixmap pix(customPath);
            if (!pix.isNull()) {
                p.setRenderHint(QPainter::SmoothPixmapTransform, false);
                p.drawPixmap(QRect(x+7,6,24,22), pix, pix.rect());
            } else {
                icon(p,moduleId,x+7,6);
            }
            // Dedicated tiny downward menu triangle.
            p.setPen(ink); p.setBrush(ink);
            p.drawPolygon(QPolygon({QPoint(x+34,stripHeightPx-10),QPoint(x+39,stripHeightPx-10),QPoint(x+36,stripHeightPx-7)}));
        }
    }
    void mouseMoveEvent(QMouseEvent *e) override {
        if (!dragging) {
            const int x = int(e->position().x());
            const int slot = (x - 24) / moduleStepPx;
            const QVector<int> active = activeModules();
            if (x < 24) setToolTip("Control Strip handle — drag to move, right-click for preferences");
            else if (expanded && slot >= 0 && slot < active.size())
                setToolTip(moduleNames.at(active.at(slot)) + " — click for controls");
            else setToolTip("Classic Control Strip 2.0.3");
            return;
        }
        if (!dragging) return;
        // Global pointer coordinates can be restricted by some Wayland compositors.
        // We update only a preview; the actual layer-shell surface stays still.
        QPoint delta = e->globalPosition().toPoint() - dragStartGlobal;
        previewOffset = qBound(0, dragStartOffset + delta.x(), maximumOffset());
        previewBottomOffset = qBound(0, dragStartBottomOffset - delta.y(), maximumBottomOffset());
        update();
    }
    void mouseReleaseEvent(QMouseEvent *e) override {
        if (e->button() != Qt::LeftButton || !dragging) return;
        dragging = false;
        // No explicit pointer grab to release.
        if (qAbs(previewOffset - dragStartOffset) < 4 && qAbs(previewBottomOffset - dragStartBottomOffset) < 4) {
            expanded = !expanded;
            setFixedSize(expanded ? activeWidth() : 24, stripHeightPx);
        } else {
            leftOffset = previewOffset;
            bottomOffset = previewBottomOffset;
            applyPosition();
            savePosition();
        }
        update();
    }
    void contextMenuEvent(QContextMenuEvent *e) override {
        if (e->pos().x() < 24) showPositionMenu(e->globalPos());
    }
    void mousePressEvent(QMouseEvent *e) override {
        if (e->button()!=Qt::LeftButton) return;
        int x=int(e->position().x());
        if (x<23) {
            dragging = true;
            dragStartGlobal = e->globalPosition().toPoint();
            dragStartOffset = leftOffset;
            dragStartBottomOffset = bottomOffset;
            previewOffset = leftOffset;
            previewBottomOffset = bottomOffset;
            // Do not grabMouse(): unsupported for non-popup layer-shell windows on Wayland.
            return;
        }
        if (!expanded) return;
        int index=(x-24)/moduleStepPx;
        const QVector<int> active = activeModules();
        if (index<0 || index>=active.size()) return;
        index = active.at(index);
        QMenu menu(this);
        menu.setStyleSheet(themeMenuStyle());
        if (index==11) {
            showAppQuickLauncher(e->globalPosition().toPoint());
            return;
        } else if (index==5) {
            menu.addAction("Sound Volume")->setEnabled(false);
            menu.addAction("Mute / Unmute", [] { toggleMute(); });
            menu.addAction("Sound Settings", [] { launch("systemsettings", {"kcm_pulseaudio"}); });
            if (hasCommand("pactl")) {
                QProcess proc;
                proc.start("pactl", {"list", "short", "sinks"});
                if (proc.waitForFinished(1500) && proc.exitCode()==0) {
                    QMenu *outputs = menu.addMenu("Sound Output");
                    const QStringList lines = QString::fromUtf8(proc.readAllStandardOutput()).split('\n', Qt::SkipEmptyParts);
                    for (const QString &line : lines) {
                        const QStringList fields = line.split('\t');
                        if (fields.size() < 2) continue;
                        const QString sink = fields.at(1);
                        outputs->addAction(sink, [sink] { launch("pactl", {"set-default-sink", sink}); });
                    }
                }
            }
            if (hasCommand("wpctl")) {
                menu.addAction("Microphone: Mute / Unmute", [] {
                    launch("wpctl", {"set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"});
                });
            } else if (hasCommand("pactl")) {
                menu.addAction("Microphone: Mute / Unmute", [] {
                    launch("pactl", {"set-source-mute", "@DEFAULT_SOURCE@", "toggle"});
                });
            }
            menu.addSeparator();
            auto *panel=new QWidget(&menu);
            auto *layout=new QVBoxLayout(panel);
            layout->setContentsMargins(8,5,8,5);
            auto *label=new QLabel(panel);
            auto *slider=new QSlider(Qt::Horizontal,panel);
            slider->setRange(0,100); slider->setValue(readVolume()); slider->setMinimumWidth(180);
            label->setText(QString("Volume: %1%").arg(slider->value()));
            layout->addWidget(label); layout->addWidget(slider);
            QObject::connect(slider,&QSlider::valueChanged,panel,[label](int value) {
                label->setText(QString("Volume: %1%").arg(value));
                writeVolume(value);
            });
            auto *action=new QWidgetAction(&menu);
            action->setDefaultWidget(panel); menu.addAction(action);
            if (!hasCommand("wpctl") && !hasCommand("pactl")) {
                menu.addAction("Install wireplumber or pulseaudio-utils")->setEnabled(false);
            }
        } else if (index==2) {
            menu.addAction("Home Folder",[] { QProcess::startDetached("xdg-open", {QDir::homePath()}); });
            menu.addAction("Downloads",[] { QProcess::startDetached("xdg-open", {QStandardPaths::writableLocation(QStandardPaths::DownloadLocation)}); });
            menu.addAction("Applications",[] { QProcess::startDetached("xdg-open", {"applications:/"}); });
            menu.addAction("Documents", [] { launch("xdg-open", {QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation)}); });
            menu.addAction("Pictures", [] { launch("xdg-open", {QStandardPaths::writableLocation(QStandardPaths::PicturesLocation)}); });
            menu.addAction("Trash", [] { launch("xdg-open", {"trash:/"}); });
        } else if (index==1) {
            menu.addAction(QDateTime::currentDateTime().toString("dddd, MMMM d yyyy"))->setEnabled(false);
            menu.addAction(QDateTime::currentDateTime().toString("h:mm AP"))->setEnabled(false);
            menu.addSeparator();
            menu.addAction("Lock Screen", [] { QProcess::startDetached("loginctl", {"lock-session"}); });
        } else if (index==3) {
            menu.addAction("Lock Screen", [] { QProcess::startDetached("loginctl", {"lock-session"}); });
        } else if (index==6) {
            if (hasCommand("nmcli")) {
                QProcess proc;
                proc.start("nmcli", {"-t", "-f", "STATE,CONNECTIVITY", "general"});
                if (proc.waitForFinished(1200)) {
                    QString state=QString::fromUtf8(proc.readAllStandardOutput()).trimmed();
                    menu.addAction(state.isEmpty() ? "Network status unavailable" : state)->setEnabled(false);
                }
                QMenu *wifi = menu.addMenu("Wi-Fi Radio");
                wifi->addAction("Enable Wi-Fi", [] { launch("nmcli", {"radio", "wifi", "on"}); });
                wifi->addAction("Disable Wi-Fi", [] { launch("nmcli", {"radio", "wifi", "off"}); });
                menu.addAction("Open Network Settings", [] { QProcess::startDetached("systemsettings", {"kcm_networkmanagement"}); });
            } else menu.addAction("Install NetworkManager CLI for status")->setEnabled(false);
        } else if (index==7) {
            menu.addAction("Open Home Folder", [] { QProcess::startDetached("xdg-open", {QDir::homePath()}); });
            QStorageInfo disk(QDir::homePath());
            if (disk.isValid() && disk.isReady()) menu.addAction(QString("Free space: %1 GB").arg(disk.bytesAvailable()/1000000000.0,0,'f',1))->setEnabled(false);
            menu.addSeparator();
            menu.addAction("Open Disk Usage Analyzer", [] { launch("filelight"); });
            menu.addAction("Disks and Devices", [] { launch("partitionmanager"); });
        } else if (index==0) {
            QScreen *screen = windowHandle() ? windowHandle()->screen() : nullptr;
            if (screen) menu.addAction(QString("%1: %2 × %3 @ %4 Hz").arg(screen->name()).arg(screen->size().width()).arg(screen->size().height()).arg(qRound(screen->refreshRate())))->setEnabled(false);
            menu.addSeparator();
            if (screen) {
                QMenu *modes = menu.addMenu("Available Display Modes");
                for (const QScreen *s : QGuiApplication::screens()) {
                    modes->addAction(QString("%1: %2 × %3, %4 Hz").arg(s->name()).arg(s->size().width()).arg(s->size().height()).arg(qRound(s->refreshRate())))->setEnabled(false);
                }
                modes->addAction("Change Resolution…", [] { launch("systemsettings", {"kcm_kscreen"}); });
            }
            menu.addAction("Display Settings", [] { launch("systemsettings", {"kcm_kscreen"}); });
            if (hasCommand("brightnessctl")) {
                QMenu *brightness = menu.addMenu("Screen Brightness");
                brightness->addAction("Brighter (+10%)", [] { launch("brightnessctl", {"set", "+10%"}); });
                brightness->addAction("Dimmer (-10%)", [] { launch("brightnessctl", {"set", "10%-"}); });
            }
            menu.addAction("Brightness Settings", [] { launch("systemsettings", {"kcm_brightness"}); });
        } else if (index==8) {
            menu.addAction("CD / DVD Drives")->setEnabled(false);
            QDir devices("/dev");
            const QStringList optical = devices.entryList({"sr[0-9]*", "cdrom", "dvd"}, QDir::System | QDir::Files | QDir::NoSymLinks);
            if (optical.isEmpty()) menu.addAction("No optical drive detected")->setEnabled(false);
            for (const QString &drive : optical) {
                const QString path = "/dev/" + drive;
                QMenu *sub = menu.addMenu(path);
                if (hasCommand("eject")) sub->addAction("Eject Disc", [path] { launch("eject", {path}); });
                else sub->addAction("Install eject utility")->setEnabled(false);
            }
            menu.addSeparator();
            menu.addAction("Open Disks and Devices", [] { launch("partitionmanager"); });
        } else if (index==9) {
            QFile mem("/proc/meminfo");
            qint64 total=0, available=0;
            if (mem.open(QIODevice::ReadOnly)) {
                while (!mem.atEnd()) {
                    const QString line = QString::fromUtf8(mem.readLine());
                    const QStringList parts = line.simplified().split(' ');
                    if (parts.size()<2) continue;
                    if (parts[0]=="MemTotal:") total=parts[1].toLongLong();
                    if (parts[0]=="MemAvailable:") available=parts[1].toLongLong();
                }
            }
            if (total>0) {
                menu.addAction(QString("Installed RAM: %1 GiB").arg(total/1048576.0,0,'f',1))->setEnabled(false);
                menu.addAction(QString("Available RAM: %1 GiB").arg(available/1048576.0,0,'f',1))->setEnabled(false);
            } else menu.addAction("Memory status unavailable")->setEnabled(false);
            QFile cpu("/proc/loadavg");
            if (cpu.open(QIODevice::ReadOnly)) {
                const QStringList loads = QString::fromUtf8(cpu.readAll()).simplified().split(' ');
                if (!loads.isEmpty())
                    menu.addAction(QString("CPU load (1 min): %1").arg(loads.first()))->setEnabled(false);
            }
            if (total > 0) {
                auto *panel = new QWidget(&menu);
                auto *layout = new QVBoxLayout(panel);
                layout->setContentsMargins(8,4,8,4);
                auto *label = new QLabel(QString("RAM in use: %1%").arg(qRound(100.0*(total-available)/total)),panel);
                auto *bar = new QProgressBar(panel);
                bar->setRange(0,100);
                bar->setValue(qRound(100.0*(total-available)/total));
                bar->setTextVisible(false);
                bar->setMinimumWidth(170);
                layout->addWidget(label); layout->addWidget(bar);
                auto *action = new QWidgetAction(&menu);
                action->setDefaultWidget(panel); menu.addAction(action);
            }
            menu.addSeparator();
            menu.addAction("System Monitor", [] { launch("plasma-systemmonitor"); });
        } else if (index==10) {
            menu.addAction("AppleTalk-style Network Controls")->setEnabled(false);
            menu.addAction("AppleTalk itself is not available on modern Linux")->setEnabled(false);
            menu.addSeparator();
            if (hasCommand("nmcli")) {
                QProcess proc;
                proc.start("nmcli", {"-t", "-f", "DEVICE,TYPE,STATE", "device"});
                if (proc.waitForFinished(1200)) {
                    for (const QString &line : QString::fromUtf8(proc.readAllStandardOutput()).split('\n',Qt::SkipEmptyParts))
                        menu.addAction(line)->setEnabled(false);
                }
            }
            menu.addAction("Network Connections…", [] { launch("systemsettings", {"kcm_networkmanagement"}); });
        } else if (index==4) {
            addThemeMenu(menu);
            menu.addSeparator();
            menu.addAction("Colors", [] { launch("systemsettings", {"kcm_colors"}); });
            menu.addAction("Global Theme", [] { launch("systemsettings", {"kcm_lookandfeel"}); });
            menu.addAction("Icons", [] { launch("systemsettings", {"kcm_icons"}); });
            menu.addAction("Fonts", [] { launch("systemsettings", {"kcm_fonts"}); });
        } else {
            static const char *names[]={"Display","Sleep","Folders","Lock","Colors","Volume","Network","Storage"};
            menu.addAction(QString::fromLatin1(names[index]))->setEnabled(false);
            menu.addSeparator();
            menu.addAction("Controls coming in later versions")->setEnabled(false);
        }
        menu.addSeparator();
        menu.addAction("Customize…", [this] { showCustomizeMenu(QCursor::pos()); });
        addSessionActions(menu);
        menu.exec(e->globalPosition().toPoint());
    }
private:
    QVector<int> activeModules() const {
        QVector<int> ids;
        for (int id : order) if (visible[id]) ids.append(id);
        return ids;
    }
    int activeWidth() const { return 26 + moduleStepPx * activeModules().size(); }
    void updateSize() {
        setFixedSize(expanded ? activeWidth() : 24, stripHeightPx);
        leftOffset = qBound(0, leftOffset, maximumOffset());
        applyPosition();
        update();
    }
    void saveModules() {
        QSettings settings("MacaqueOS", "ClassicControlStrip");
        QVariantList ids;
        for (int id : order) ids.append(id);
        settings.setValue("moduleOrder", ids);
        for (int id=0; id<moduleCount; ++id) settings.setValue(QString("module%1Visible").arg(id), visible[id]);
    }
    struct DesktopApp { QString id, name, category, exec, iconName, desktopFile; };

    QVector<DesktopApp> installedApps() const {
        QVector<DesktopApp> apps;
        QSet<QString> seen;
        QStringList dirs = QStandardPaths::standardLocations(QStandardPaths::ApplicationsLocation);
        dirs << QDir::homePath()+"/.local/share/applications" << "/usr/share/applications" << "/usr/local/share/applications";
        for (const QString &base : dirs) {
            QDir dir(base);
            if (!dir.exists()) continue;
            QDirIterator it(base, {"*.desktop"}, QDir::Files, QDirIterator::Subdirectories);
            while (it.hasNext()) {
                const QString file = it.next();
                const QString id = QDir(base).relativeFilePath(file).replace('/','-');
                if (seen.contains(id)) continue;
                seen.insert(id);
                QSettings entry(file,QSettings::IniFormat);
                entry.beginGroup("Desktop Entry");
                if (entry.value("Type").toString()!="Application" || entry.value("Hidden",false).toBool() || entry.value("NoDisplay",false).toBool()) continue;
                const QString name=entry.value("Name").toString();
                const QString exec=entry.value("Exec").toString();
                const QString tryExec=entry.value("TryExec").toString();
                if (name.isEmpty() || exec.isEmpty() || (!tryExec.isEmpty() && !hasCommand(tryExec))) continue;
                const QString categories=entry.value("Categories").toString();
                QString category="Other";
                for (const QString &c : {"Game","Network","Graphics","AudioVideo","Office","Development","Settings","System","Utility","Education"})
                    if (categories.contains(c,Qt::CaseInsensitive)) { category=c; break; }
                apps.append({id,name,category,exec,entry.value("Icon").toString(),file});
            }
        }
        std::sort(apps.begin(),apps.end(),[](const DesktopApp &a,const DesktopApp &b){return a.name.localeAwareCompare(b.name)<0;});
        return apps;
    }

    void launchDesktopApp(const DesktopApp &app) {
        // Expand only standard desktop-entry Exec placeholders; never invoke a shell.
        QString command=app.exec;
        command.replace("%%", "\x01");
        command.replace(QRegularExpression("%[fFuUdDnNickvm]"), "");
        command.replace("\x01", "%");
        QStringList parts=QProcess::splitCommand(command);
        if (parts.isEmpty()) return;
        const QString program=parts.takeFirst();
        if (!QProcess::startDetached(program,parts))
            QMessageBox::warning(this,"App Viewer","Could not launch " + app.name);
        else {
            QSettings settings("MacaqueOS","ClassicControlStrip");
            QStringList recent=settings.value("appViewerRecent").toStringList();
            recent.removeAll(app.id); recent.prepend(app.id);
            while (recent.size()>10) recent.removeLast();
            settings.setValue("appViewerRecent",recent);
        }
    }

    void showAppQuickLauncher(const QPoint &point) {
        const auto apps=installedApps();
        QMenu menu(this); menu.setStyleSheet(themeMenuStyle());
        QSettings settings("MacaqueOS","ClassicControlStrip");
        const QStringList favorites=settings.value("appViewerFavorites").toStringList();
        const QStringList recent=settings.value("appViewerRecent").toStringList();
        auto appendGroup=[&](const QString &title,const QStringList &ids) {
            if (ids.isEmpty()) return;
            menu.addSection(title);
            for (const QString &id : ids) {
                for (const auto &app : apps) if (app.id==id) {
                    menu.addAction(QIcon::fromTheme(app.iconName),app.name,[this,app]{launchDesktopApp(app);});
                    break;
                }
            }
        };
        appendGroup("Favorites",favorites);
        appendGroup("Recently Opened",recent);
        if (favorites.isEmpty() && recent.isEmpty()) menu.addAction("No favorites yet")->setEnabled(false);
        menu.addSeparator();
        menu.addAction("Open App Viewer…",[this]{QTimer::singleShot(0,this,[this]{showAppViewer();});});
        menu.exec(point);
    }

    void showAppViewer() {
        const QVector<DesktopApp> apps=installedApps();
        QDialog dialog(this);
        dialog.setWindowTitle("Application Viewer — Classic Control Strip");
        dialog.resize(740,540);
        // Follow the same saved theme, custom colors and accent as the Control Strip.
        // Derive high-contrast foregrounds from each surface for light AND dark presets.
        const bool darkTheme = theme == Theme::Dark;
        const QColor base = customSurface.isValid() ? customSurface :
            (darkTheme ? QColor("#363941") : theme == Theme::Light ? QColor("#efefef") : QColor("#cccccc"));
        const QColor tile = customModuleSurface.isValid() ? customModuleSurface :
            (darkTheme ? QColor("#424650") : theme == Theme::Light ? QColor("#f7f7f7") : QColor("#e5e5e5"));
        const QColor border = customBorder.isValid() ? customBorder :
            (darkTheme ? QColor("#777c87") : QColor("#777777"));
        const auto foreground = [](const QColor &c) {
            // WCAG relative luminance chooses legible black/white text.
            auto linear=[](double v) { v/=255.0; return v<=0.04045 ? v/12.92 : std::pow((v+0.055)/1.055,2.4); };
            double luminance=0.2126*linear(c.red())+0.7152*linear(c.green())+0.0722*linear(c.blue());
            return luminance > 0.179 ? QStringLiteral("#171717") : QStringLiteral("#ffffff");
        };
        const QString baseInk = foreground(base);
        const QString tileInk = foreground(tile);
        const QColor field = base.lightness() < 128 ? QColor("#252932") : QColor("#ffffff");
        const QString fieldInk = foreground(field);
        const QColor panelColor = base.lightness() < 128 ? base.lighter(112) : base.lighter(108);
        const QString panelInk = foreground(panelColor);
        const QColor highlight = accent.isValid() ? accent : QColor("#333399");
        const QString highlightInk = foreground(highlight);
        const QColor hover = tile.lightness() < 128 ? tile.lighter(120) : tile.darker(106);
        const QString style = QString(
            "QDialog { background:%1; color:%2; }"
            "QLabel { color:%2; background:transparent; }"
            "QLineEdit, QComboBox { background:%3; color:%4; padding:4px; border:1px solid %5; selection-background-color:%6; selection-color:%7; }"
            "QComboBox QAbstractItemView { background:%3; color:%4; selection-background-color:%6; selection-color:%7; }"
            "QScrollArea { background:%8; border:2px inset %5; }"
            "QWidget#appViewerPanel { background:%8; color:%9; }"
            "QToolButton { color:%10; background:%11; border:2px outset %5; padding:5px; font-weight:500; }"
            "QToolButton:hover { color:%10; background:%12; }"
            "QToolButton:focus { background:%6; color:%7; border:2px inset %5; }"
            "QPushButton { color:%10; background:%11; border:2px outset %5; padding:5px; }"
            "QMenu { background:%1; color:%2; selection-background-color:%6; selection-color:%7; }"
        ).arg(base.name(),baseInk,field.name(),fieldInk,border.name(),highlight.name(),
              highlightInk,panelColor.name(),panelInk,tileInk,tile.name(),hover.name());
        dialog.setStyleSheet(style);
        auto *layout=new QVBoxLayout(&dialog);
        auto *header=new QLabel("▦  Application Viewer",&dialog);
        QFont font=header->font(); font.setBold(true); font.setPointSize(font.pointSize()+2); header->setFont(font);
        layout->addWidget(header);
        auto *tools=new QHBoxLayout();
        auto *search=new QLineEdit(&dialog); search->setPlaceholderText("Find an application…");
        auto *category=new QComboBox(&dialog);
        category->addItems({"All Applications","Favorites","Recently Opened","Games","Internet","Graphics","Multimedia","Office","Development","Settings","System","Utilities","Other"});
        tools->addWidget(search,1); tools->addWidget(category); layout->addLayout(tools);
        auto *scroll=new QScrollArea(&dialog); scroll->setWidgetResizable(true);
        auto *panel=new QWidget(scroll); panel->setObjectName("appViewerPanel"); auto *grid=new QGridLayout(panel);
        grid->setAlignment(Qt::AlignTop|Qt::AlignLeft); grid->setSpacing(12);
        scroll->setWidget(panel); layout->addWidget(scroll,1);
        auto *status=new QLabel(&dialog); layout->addWidget(status);
        auto rebuild=[this,&apps,grid,search,category,status,panel,&dialog]() {
            while (QLayoutItem *item=grid->takeAt(0)) {
                if (item->widget()) item->widget()->deleteLater();
                delete item;
            }
            QSettings settings("MacaqueOS","ClassicControlStrip");
            const QStringList favorites=settings.value("appViewerFavorites").toStringList();
            const QStringList recent=settings.value("appViewerRecent").toStringList();
            int count=0;
            for (const DesktopApp &app : apps) {
                if (!app.name.contains(search->text(),Qt::CaseInsensitive)) continue;
                const QString filter=category->currentText();
                if (filter=="Favorites" && !favorites.contains(app.id)) continue;
                if (filter=="Recently Opened" && !recent.contains(app.id)) continue;
                const QMap<QString,QString> categoryMap={{"Games","Game"},{"Internet","Network"},{"Multimedia","AudioVideo"},{"Utilities","Utility"}};
                if (filter!="All Applications" && filter!="Favorites" && filter!="Recently Opened" && app.category!=categoryMap.value(filter,filter)) continue;
                auto *button=new QToolButton(panel);
                button->setToolButtonStyle(Qt::ToolButtonTextUnderIcon);
                button->setMinimumSize(112,104); button->setMaximumWidth(140);
                button->setIcon(QIcon::fromTheme(app.iconName)); button->setIconSize(QSize(48,48));
                button->setText(app.name.left(24)); button->setToolTip(app.name+"\nDouble-click to launch; right-click to favorite");
                // Text, background and selected colors come from the explicit App Viewer stylesheet.
                // A single click selects; a second click on the same item launches.
                connect(button,&QToolButton::clicked,&dialog,[this,app,button,&dialog] {
                    const QString current=dialog.property("selectedAppId").toString();
                    if (current==app.id) { launchDesktopApp(app); dialog.setProperty("selectedAppId",QString()); }
                    else { dialog.setProperty("selectedAppId",app.id); button->setFocus(); }
                });
                button->setContextMenuPolicy(Qt::CustomContextMenu);
                connect(button,&QPushButton::customContextMenuRequested,&dialog,[this,app,button,&dialog] (const QPoint &p) {
                    QSettings s("MacaqueOS","ClassicControlStrip");
                    QStringList fav=s.value("appViewerFavorites").toStringList();
                    QMenu m;
                    m.addAction(fav.contains(app.id)?"Remove from Favorites":"Add to Favorites",[app,&dialog] {
                        QSettings s2("MacaqueOS","ClassicControlStrip");
                        QStringList ids=s2.value("appViewerFavorites").toStringList();
                        if (ids.contains(app.id)) ids.removeAll(app.id); else ids.append(app.id);
                        s2.setValue("appViewerFavorites",ids);
                        dialog.setProperty("refreshFavorites",true);
                    });
                    m.addAction("Launch",[this,app]{launchDesktopApp(app);});
                    m.exec(button->mapToGlobal(p));
                });
                grid->addWidget(button,count/5,count%5); ++count;
            }
            status->setText(QString("%1 applications shown — click twice to launch; right-click for Favorites").arg(count));
        };
        connect(search,&QLineEdit::textChanged,&dialog,[rebuild](const QString &){rebuild();});
        connect(category,&QComboBox::currentTextChanged,&dialog,[rebuild](const QString &){rebuild();});
        auto *refresh=new QTimer(&dialog);
        connect(refresh,&QTimer::timeout,&dialog,[&dialog,rebuild] {
            if (dialog.property("refreshFavorites").toBool()) { dialog.setProperty("refreshFavorites",false); rebuild(); }
        });
        refresh->start(250);
        rebuild();
        dialog.exec();
    }

    void addSessionActions(QMenu &menu) {
        menu.addSeparator();
        menu.addAction("Restart Control Strip", this, [this] {
            // Delay startup to let this instance release its single-instance lock.
            const QString executable = QCoreApplication::applicationFilePath();
            if (!QProcess::startDetached(executable, {"--restart-control-strip"})) {
                QMessageBox::warning(this, "Restart Control Strip",
                                     "Unable to start a replacement instance.");
                return;
            }
            QCoreApplication::quit();
        });
        menu.addAction("Quit Control Strip", this, [] { QCoreApplication::quit(); });
    }

    void showCustomizeMenu(const QPoint &point) {
        QMenu menu(this);
        menu.setStyleSheet(themeMenuStyle());
        menu.addAction("Show / Hide Modules")->setEnabled(false);
        for (int id=0; id<moduleCount; ++id) {
            QAction *a = menu.addAction(moduleNames[id]);
            a->setCheckable(true);
            a->setChecked(visible[id]);
            connect(a, &QAction::toggled, this, [this,id](bool checked) {
                visible[id] = checked;
                saveModules();
                updateSize();
            });
        }
        menu.addSeparator();
        QMenu *move = menu.addMenu("Move Module");
        for (int id : order) {
            QMenu *sub = move->addMenu(moduleNames[id]);
            sub->addAction("Move Left", [this,id] {
                int i = order.indexOf(id);
                if (i > 0) { order.swapItemsAt(i,i-1); saveModules(); update(); }
            });
            sub->addAction("Move Right", [this,id] {
                int i = order.indexOf(id);
                if (i >= 0 && i < order.size()-1) { order.swapItemsAt(i,i+1); saveModules(); update(); }
            });
        }
        menu.addSeparator();
        addThemeMenu(menu);
        menu.addSeparator();
        menu.addAction("Control Strip Preferences…", [this] {
            QTimer::singleShot(0, this, [this] { showPreferences(); });
        });
        menu.addAction("System Settings…", [this] {
            QTimer::singleShot(0,this,[this]{showSystemSettings();});
        });
        menu.addAction("Restore Current Theme Defaults", [this] {
            restoreSelectedThemeDefaults();
        });
        menu.addAction("Theme Creator…", [this] {
            QTimer::singleShot(0,this,[this]{showThemeCreator();});
        });
        menu.addAction("Visual Icon Editor…", [this] {
            QTimer::singleShot(0, this, [this] { showVisualIconEditor(); });
        });
        menu.addAction("Theme Manager & Gallery…", [this] {
            QTimer::singleShot(0, this, [this] { showThemeManager(); });
        });
        menu.addAction("Custom Module Icons…", [this] {
            QTimer::singleShot(0, this, [this] { showCustomIconsMenu(QCursor::pos()); });
        });
        menu.addAction("Accent Color…", [this] { chooseAccentColor(); });
        menu.addAction("Export Preferences…", [this] { exportPreferences(); });
        menu.addAction("Import Preferences…", [this] { importPreferences(); });
        menu.addSeparator();
        menu.addAction("Restore Default Modules", [this] {
            order.clear();
            for (int id=0; id<moduleCount; ++id) { order.append(id); visible[id] = (id < 8 || id == 11); }
            saveModules(); updateSize();
        });
        addSessionActions(menu);
        menu.exec(point);
    }
    int maximumOffset() const {
        QScreen *screen = windowHandle() ? windowHandle()->screen() : nullptr;
        return qMax(0, (screen ? screen->geometry().width() : 1920) - width());
    }
    int maximumBottomOffset() const {
        QScreen *screen = windowHandle() ? windowHandle()->screen() : nullptr;
        return qMax(0, (screen ? screen->geometry().height() : 1080) - height());
    }
    void savePosition() {
        QSettings settings("MacaqueOS", "ClassicControlStrip");
        settings.setValue("leftOffset", leftOffset);
        settings.setValue("bottomOffset", bottomOffset);
    }

    QString autostartPath() const {
        return QStandardPaths::writableLocation(QStandardPaths::ConfigLocation)
             + "/autostart/classic-control-strip.desktop";
    }
    bool autostartEnabled() const { return QFile::exists(autostartPath()); }
    void setAutostart(bool enabled) {
        const QString path = autostartPath();
        if (!enabled) { QFile::remove(path); return; }
        QDir().mkpath(QFileInfo(path).absolutePath());
        const QString executable = QCoreApplication::applicationFilePath();
        QSaveFile file(path);
        if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
            const QString entry = "[Desktop Entry]\nType=Application\nName=Classic Control Strip\n"
                "Comment=Mac OS 9 inspired Control Strip\nExec=\"" + executable
                + "\"\nTerminal=false\nX-KDE-autostart-after=panel\n";
            file.write(entry.toUtf8());
            file.commit();
        }
    }
    void showAbout() {
        QMessageBox box(this);
        box.setWindowTitle("About Classic Control Strip");
        box.setTextFormat(Qt::RichText);
        box.setText("<b>Classic Control Strip</b><br/>Version 2.0 · MacaqueOS Edition");
        box.setInformativeText("A classic Macintosh-inspired control bar for MacaqueOS / KDE Plasma.<br/>"
                               "Built with Qt 6 and LayerShellQt.<br/><br/>"
                               "An independent homage, not affiliated with Apple.");
        box.setStyleSheet("QMessageBox { background:#cccccc; color:black; } "
                          "QPushButton { background:#dddddd; border:2px outset #eeeeee; padding:5px 18px; }");
        box.exec();
    }
    void showPreferences() {
        QDialog dialog(this);
        dialog.setWindowTitle("Control Strip Preferences");
        dialog.setStyleSheet("QDialog { background:#cccccc; color:#111; } "
                             "QCheckBox { padding:6px; } "
                             "QPushButton { background:#dddddd; color:black; border:2px outset #eeeeee; padding:5px 12px; }");
        auto *layout = new QVBoxLayout(&dialog);
        auto *heading = new QLabel("<b>Classic Control Strip · Preferences</b>", &dialog);
        layout->addWidget(heading);
        auto *startup = new QCheckBox("Open Control Strip when I log in", &dialog);
        startup->setChecked(autostartEnabled());
        layout->addWidget(startup);
        auto *themeLabel = new QLabel("Appearance:", &dialog);
        layout->addWidget(themeLabel);
        auto *themePicker = new QComboBox(&dialog);
        themePicker->addItems({"Classic Platinum", "Light", "Dark"});
        themePicker->setCurrentIndex(int(theme));
        layout->addWidget(themePicker);
        auto *tip = new QLabel("Module visibility and order are in Customize Modules.\n"
                               "To move the strip, right-click its left handle.", &dialog);
        tip->setWordWrap(true);
        layout->addWidget(tip);
        auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
        layout->addWidget(buttons);
        QObject::connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
        QObject::connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
        if (dialog.exec() == QDialog::Accepted) {
            setAutostart(startup->isChecked());
            setTheme(static_cast<Theme>(themePicker->currentIndex()));
        }
    }
    void showPositionMenu(const QPoint &point) {
        QScreen *screen = windowHandle() ? windowHandle()->screen() : nullptr;
        const int screenWidth = screen ? screen->geometry().width() : 1920;
        const int maxLeft = qMax(0, screenWidth - width());
        QMenu menu(this);
        menu.setStyleSheet(themeMenuStyle());
        auto *panel = new QWidget(&menu);
        auto *layout = new QVBoxLayout(panel);
        layout->setContentsMargins(10, 8, 10, 8);
        auto *label = new QLabel(panel);
        auto *slider = new QSlider(Qt::Horizontal, panel);
        slider->setRange(0, maxLeft);
        slider->setSingleStep(10);
        slider->setPageStep(100);
        slider->setMinimumWidth(250);
        slider->setValue(qBound(0, leftOffset, maxLeft));
        label->setText(QString("Horizontal position: %1 px").arg(slider->value()));
        layout->addWidget(label);
        layout->addWidget(slider);
        QObject::connect(slider, &QSlider::valueChanged, panel, [this,label](int value) {
            leftOffset = value;
            applyPosition();
            label->setText(QString("Horizontal position: %1 px").arg(value));
            savePosition();
        });
        auto *action = new QWidgetAction(&menu);
        action->setDefaultWidget(panel);
        menu.addAction(action);
        auto *verticalLabel = new QLabel(panel);
        auto *verticalSlider = new QSlider(Qt::Horizontal, panel);
        verticalSlider->setRange(0, maximumBottomOffset());
        verticalSlider->setSingleStep(10);
        verticalSlider->setPageStep(100);
        verticalSlider->setValue(qBound(0, bottomOffset, maximumBottomOffset()));
        verticalLabel->setText(QString("Height above bottom: %1 px").arg(verticalSlider->value()));
        layout->addWidget(verticalLabel);
        layout->addWidget(verticalSlider);
        QObject::connect(verticalSlider, &QSlider::valueChanged, panel, [this,verticalLabel](int value) {
            bottomOffset = value;
            applyPosition();
            verticalLabel->setText(QString("Height above bottom: %1 px").arg(value));
            savePosition();
        });
        menu.addSeparator();
        menu.addAction("Customize…", &menu, [this] {
            QTimer::singleShot(0, this, [this] { showCustomizeMenu(QCursor::pos()); });
        });
        menu.addAction("About Classic Control Strip…", &menu, [this] {
            QTimer::singleShot(0, this, [this] { showAbout(); });
        });
        addSessionActions(menu);
        menu.addSeparator();
        auto *dockAction = menu.addAction("Attach to left screen edge (Mac OS 9)");
        dockAction->setCheckable(true);
        dockAction->setChecked(dockedToLeft);
        QObject::connect(dockAction, &QAction::triggered, &menu, [this](bool checked) {
            if (checked && !dockedToLeft) {
                freeLeftOffset = leftOffset;
                freeBottomOffset = bottomOffset;
                leftOffset = 0; bottomOffset = 0;
            } else if (!checked && dockedToLeft) {
                leftOffset = qBound(0, freeLeftOffset, maximumOffset());
                bottomOffset = qBound(0, freeBottomOffset, maximumBottomOffset());
            }
            dockedToLeft = checked;
            QSettings("MacaqueOS", "ClassicControlStrip").setValue("dockedToLeft", dockedToLeft);
            applyPosition();
            savePosition();
        });
        menu.addSeparator();
        menu.addAction("Move to bottom-left", &menu, [this] {
            leftOffset = 0;
            bottomOffset = 0;
            applyPosition();
            savePosition();
        });
        menu.addAction("Move to far left", &menu, [this] {
            leftOffset = 0;
            applyPosition();
            savePosition();
        });
        menu.exec(point);
    }
    void applyPosition() {
        if (layerWindow) layerWindow->setMargins(QMargins(leftOffset, 0, 0, bottomOffset));
    }
    int stripHeightPx = 34;
    int moduleStepPx = 43;
    QColor customSurface;
    QColor customModuleSurface;
    QColor customBorder;
    int backgroundPattern = 0; // 0 solid, 1 fine dither, 2 checker, 3 pinstripe, 4 custom image
    QString backgroundTexturePath;
    void saveCreatorSettings() {
        QSettings settings("MacaqueOS","ClassicControlStrip");
        settings.setValue("creatorHeight",stripHeightPx);
        settings.setValue("creatorSpacing",moduleStepPx);
        settings.setValue("creatorSurface",customSurface.isValid() ? customSurface.name() : QString());
        settings.setValue("creatorModuleSurface",customModuleSurface.isValid() ? customModuleSurface.name() : QString());
        settings.setValue("creatorBorder",customBorder.isValid() ? customBorder.name() : QString());
        settings.setValue("creatorPattern",backgroundPattern);
        settings.setValue("creatorTexture",backgroundTexturePath);
        updateSize();
    }
    QColor accent = QColor("#333399");
    QMap<int, QString> customIconPaths;
    void saveCustomIcons() {
        QStringList paths;
        for (int id=0; id<moduleCount; ++id) paths << customIconPaths.value(id);
        QSettings("MacaqueOS", "ClassicControlStrip").setValue("customIconPaths", paths);
        update();
    }
    void showVisualIconEditor() {
        QDialog dialog(this);
        dialog.setWindowTitle("Control Strip — Visual Icon Editor");
        dialog.resize(740, 510);
        auto *layout = new QVBoxLayout(&dialog);
        auto *intro = new QLabel("Click an icon to replace it. Use arrows to change module order. "
                                 "Changes are saved immediately.", &dialog);
        intro->setWordWrap(true);
        layout->addWidget(intro);
        auto *scroll = new QScrollArea(&dialog);
        scroll->setWidgetResizable(true);
        auto *panel = new QWidget(scroll);
        auto *grid = new QGridLayout(panel);
        scroll->setWidget(panel);
        layout->addWidget(scroll);
        auto *rows = new QVector<QWidget*>;
        auto rebuild = [this,grid,panel,rows,&dialog]() {
            qDeleteAll(*rows); rows->clear();
            for (int pos=0; pos<order.size(); ++pos) {
                const int id=order.at(pos);
                auto *row = new QWidget(panel);
                auto *h = new QHBoxLayout(row);
                auto *preview = new QLabel(row);
                preview->setFixedSize(44,36);
                preview->setAlignment(Qt::AlignCenter);
                QPixmap pix(customIconPaths.value(id));
                if (pix.isNull()) {
                    QPixmap original(24,22);
                    original.fill(Qt::transparent);
                    QPainter painter(&original);
                    icon(painter,id,0,0);
                    pix=original;
                }
                preview->setPixmap(pix.scaled(32,28,Qt::KeepAspectRatio,Qt::FastTransformation));
                h->addWidget(preview);
                auto *name = new QLabel(moduleNames.at(id),row);
                name->setMinimumWidth(115);
                h->addWidget(name);
                auto *replace = new QPushButton("Choose Image…",row);
                h->addWidget(replace);
                QObject::connect(replace,&QPushButton::clicked,row,[this,id,preview] {
                    const QString path=QFileDialog::getOpenFileName(this,
                        "Choose "+moduleNames.at(id)+" Icon",QDir::homePath(),
                        "Images (*.png *.jpg *.jpeg *.bmp *.webp *.svg)");
                    if (path.isEmpty()) return;
                    QPixmap image(path);
                    if (image.isNull()) {
                        QMessageBox::warning(this,"Invalid Icon","Could not read this image.");
                        return;
                    }
                    const QString folder=QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)+"/icons";
                    QDir().mkpath(folder);
                    const QString target=folder+"/module-"+QString::number(id)+".png";
                    if (!image.save(target,"PNG")) {
                        QMessageBox::warning(this,"Icon Error","Could not save the icon.");
                        return;
                    }
                    customIconPaths[id]=target;
                    saveCustomIcons();
                    preview->setPixmap(image.scaled(32,28,Qt::KeepAspectRatio,Qt::FastTransformation));
                });
                auto *reset = new QPushButton("Reset",row);
                h->addWidget(reset);
                QObject::connect(reset,&QPushButton::clicked,row,[this,id,preview] {
                    customIconPaths.remove(id); saveCustomIcons();
                    QPixmap original(24,22); original.fill(Qt::transparent);
                    QPainter painter(&original); icon(painter,id,0,0); painter.end();
                    preview->setPixmap(original.scaled(32,28,Qt::KeepAspectRatio,Qt::FastTransformation));
                });
                auto *up = new QPushButton("↑",row);
                auto *down = new QPushButton("↓",row);
                up->setFixedWidth(34); down->setFixedWidth(34);
                up->setEnabled(pos>0); down->setEnabled(pos+1<order.size());
                h->addWidget(up); h->addWidget(down);
                QObject::connect(up,&QPushButton::clicked,row,[this,id,&dialog] {
                    int pos=order.indexOf(id);
                    if (pos>0) { order.swapItemsAt(pos,pos-1); saveModules(); updateSize(); dialog.accept(); QTimer::singleShot(0,this,[this]{showVisualIconEditor();}); }
                });
                QObject::connect(down,&QPushButton::clicked,row,[this,id,&dialog] {
                    int pos=order.indexOf(id);
                    if (pos>=0 && pos+1<order.size()) { order.swapItemsAt(pos,pos+1); saveModules(); updateSize(); dialog.accept(); QTimer::singleShot(0,this,[this]{showVisualIconEditor();}); }
                });
                grid->addWidget(row,pos,0);
                rows->append(row);
            }
        };
        rebuild();
        auto *bottom = new QHBoxLayout;
        auto *restore = new QPushButton("Restore All Original Icons",&dialog);
        QObject::connect(restore,&QPushButton::clicked,&dialog,[this,&dialog] {
            customIconPaths.clear(); saveCustomIcons();
            dialog.accept();
            QTimer::singleShot(0,this,[this]{showVisualIconEditor();});
        });
        bottom->addWidget(restore);
        bottom->addStretch();
        auto *close = new QPushButton("Done",&dialog);
        QObject::connect(close,&QPushButton::clicked,&dialog,&QDialog::accept);
        bottom->addWidget(close);
        layout->addLayout(bottom);
        dialog.exec();
        delete rows;
    }
    void showThemeCreator() {
        struct Snapshot {
            int height, spacing;
            QColor surface, module, border;
            int pattern;
            QString texture;
        };
        const Snapshot original{stripHeightPx,moduleStepPx,customSurface,customModuleSurface,
                                customBorder,backgroundPattern,backgroundTexturePath};
        QDialog dialog(this);
        dialog.setWindowTitle("MacaqueOS — Control Strip Theme Creator");
        dialog.setMinimumWidth(440);
        auto *layout = new QVBoxLayout(&dialog);
        auto *description = new QLabel(
            "Changes preview immediately on the real Control Strip. "
            "Choose Apply to save, or Cancel to restore your previous look.",&dialog);
        description->setWordWrap(true);
        layout->addWidget(description);
        auto *form = new QFormLayout;
        auto *height = new QSpinBox(&dialog);
        height->setRange(28,56); height->setValue(stripHeightPx);
        height->setSuffix(" px");
        form->addRow("Strip height:",height);
        auto *spacing = new QSpinBox(&dialog);
        spacing->setRange(43,66); spacing->setValue(moduleStepPx);
        spacing->setSuffix(" px");
        form->addRow("Icon spacing:",spacing);
        QObject::connect(height,qOverload<int>(&QSpinBox::valueChanged),&dialog,
            [this](int n){ stripHeightPx=n; updateSize(); });
        QObject::connect(spacing,qOverload<int>(&QSpinBox::valueChanged),&dialog,
            [this](int n){ moduleStepPx=n; updateSize(); });
        auto makeColorButton = [&](const QString &label, QColor *value) {
            auto *button = new QPushButton("Choose color…",&dialog);
            form->addRow(label,button);
            auto refresh = [button,value] {
                button->setText(value->isValid() ? value->name() : "Use theme default");
            };
            refresh();
            QObject::connect(button,&QPushButton::clicked,&dialog,[this,value,refresh] {
                QColor initial = value->isValid() ? *value : QColor("#cccccc");
                QColor selected = QColorDialog::getColor(initial,this,"Choose Theme Color");
                if (selected.isValid()) { *value=selected; refresh(); update(); }
            });
        };
        makeColorButton("Background:",&customSurface);
        makeColorButton("Module background:",&customModuleSurface);
        makeColorButton("Border / shadow:",&customBorder);
        auto *pattern = new QComboBox(&dialog);
        pattern->addItems({"Solid color", "Classic fine dither", "Retro checkerboard",
                           "Macintosh pinstripes", "Custom image texture"});
        pattern->setCurrentIndex(backgroundPattern);
        form->addRow("Background texture:",pattern);
        QObject::connect(pattern,qOverload<int>(&QComboBox::currentIndexChanged),
                         &dialog,[this](int index) {backgroundPattern=index;update();});
        auto *chooseTexture = new QPushButton("Choose PNG / JPG / BMP…",&dialog);
        form->addRow("Image texture:",chooseTexture);
        QObject::connect(chooseTexture,&QPushButton::clicked,&dialog,[this,pattern] {
            const QString source=QFileDialog::getOpenFileName(this,"Choose Strip Texture",
                                  QDir::homePath(),"Images (*.png *.jpg *.jpeg *.bmp *.webp)");
            if (source.isEmpty()) return;
            QImage image(source);
            if (image.isNull() || image.width()>2048 || image.height()>2048) {
                QMessageBox::warning(this,"Invalid Texture","Use an image up to 2048 × 2048 pixels.");
                return;
            }
            const QString dir=QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)+"/textures";
            QDir().mkpath(dir);
            const QString target=dir+"/background.png";
            if (!image.save(target,"PNG")) {
                QMessageBox::warning(this,"Texture Error","Could not save the texture.");
                return;
            }
            backgroundTexturePath=target;
            backgroundPattern=4;
            pattern->setCurrentIndex(4);
            update();
        });
        layout->addLayout(form);
        auto *previewLabel = new QLabel("Theme preview",&dialog);
        layout->addWidget(previewLabel);
        auto *preview = new QLabel(&dialog);
        preview->setFixedHeight(75);
        preview->setMinimumWidth(370);
        preview->setAlignment(Qt::AlignCenter);
        layout->addWidget(preview);
        auto renderPreview = [this,preview] {
            const int w=370,h=65;
            QPixmap canvas(w,h); canvas.fill(QColor("#888888"));
            QPainter painter(&canvas);
            const QColor base=customSurface.isValid()?customSurface:
                (theme==Theme::Dark?QColor("#363941"):
                 theme==Theme::Light?QColor("#efefef"):QColor("#cccccc"));
            const QColor cell=customModuleSurface.isValid()?customModuleSurface:base.lighter(107);
            painter.fillRect(8,13,w-16,40,base);
            if (backgroundPattern==4) {
                QPixmap texture(backgroundTexturePath);
                if (!texture.isNull()) painter.drawTiledPixmap(QRect(8,13,w-16,40),texture);
            } else if (backgroundPattern>0) {
                painter.setPen(base.lightness()<125?QColor(255,255,255,55):QColor(0,0,0,45));
                for (int y=14;y<52;++y) for (int x=9;x<w-9;++x)
                    if ((backgroundPattern==1 && (x+y)%4==0) ||
                        (backgroundPattern==2 && (x/3+y/3)%2==0) ||
                        (backgroundPattern==3 && y%4==0)) painter.drawPoint(x,y);
            }
            painter.setPen(customBorder.isValid()?customBorder:QColor("#555555"));
            painter.drawRect(8,13,w-17,39);
            for (int i=0;i<7;++i) {
                int x=31+i*47;
                painter.fillRect(x,18,40,30,cell);
                painter.drawRect(x,18,40,30);
                QPixmap custom(customIconPaths.value(i));
                if (!custom.isNull()) painter.drawPixmap(QRect(x+7,22,24,22),custom,custom.rect());
                else icon(painter,i,x+7,22);
            }
            painter.end();
            preview->setPixmap(canvas);
        };
        auto *previewTimer = new QTimer(&dialog);
        QObject::connect(previewTimer,&QTimer::timeout,&dialog,renderPreview);
        previewTimer->start(160);
        renderPreview();
        auto *reset = new QPushButton("Reset Colors to Current Theme",&dialog);
        QObject::connect(reset,&QPushButton::clicked,&dialog,[this] {
            customSurface=QColor();
            customModuleSurface=QColor();
            customBorder=QColor();
            update();
        });
        layout->addWidget(reset);
        auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok|QDialogButtonBox::Cancel,&dialog);
        buttons->button(QDialogButtonBox::Ok)->setText("Apply & Save");
        QObject::connect(buttons,&QDialogButtonBox::accepted,&dialog,&QDialog::accept);
        QObject::connect(buttons,&QDialogButtonBox::rejected,&dialog,&QDialog::reject);
        layout->addWidget(buttons);
        if (dialog.exec()==QDialog::Accepted) saveCreatorSettings();
        else {
            stripHeightPx=original.height; moduleStepPx=original.spacing;
            customSurface=original.surface; customModuleSurface=original.module;
            customBorder=original.border;
            backgroundPattern=original.pattern;
            backgroundTexturePath=original.texture;
            updateSize();
        }
    }
    void showSystemSettings() {
        QDialog dialog(this);
        dialog.setWindowTitle("Classic Control Strip — Settings");
        dialog.setMinimumWidth(450);
        auto *layout = new QVBoxLayout(&dialog);
        auto *heading = new QLabel("<b>Classic Control Strip 2.0.3</b><br>"
                                   "MacaqueOS desktop integration",&dialog);
        layout->addWidget(heading);
        auto *form = new QFormLayout;
        auto *monitor = new QComboBox(&dialog);
        monitor->addItem("Automatic (original DP-2 preference)",QString());
        for (QScreen *screen : QGuiApplication::screens())
            monitor->addItem(screen->name()+" — "+QString::number(screen->size().width())
                             +" × "+QString::number(screen->size().height()),screen->name());
        const QString current = QSettings("MacaqueOS","ClassicControlStrip")
                                    .value("preferredMonitor").toString();
        for (int i=0;i<monitor->count();++i)
            if (monitor->itemData(i).toString()==current) monitor->setCurrentIndex(i);
        form->addRow("Display:",monitor);
        auto *appearance = new QComboBox(&dialog);
        appearance->addItems({"Classic Platinum","Light","Dark"});
        appearance->setCurrentIndex(int(theme));
        form->addRow("Appearance:",appearance);
        auto *startup = new QCheckBox("Launch when I sign in",&dialog);
        startup->setChecked(QFileInfo::exists(QStandardPaths::writableLocation(
            QStandardPaths::ConfigLocation)+"/autostart/classic-control-strip.desktop"));
        form->addRow("Startup:",startup);
        layout->addLayout(form);
        auto *resetAppearance = new QPushButton("Restore Current Theme Defaults (remove custom background)", &dialog);
        QObject::connect(resetAppearance,&QPushButton::clicked,&dialog,[this] {
            restoreSelectedThemeDefaults();
        });
        layout->addWidget(resetAppearance);
        auto *note = new QLabel("Changing the display takes effect after restarting the Control Strip. "
                                "Other settings apply immediately.",&dialog);
        note->setWordWrap(true); layout->addWidget(note);
        auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok|QDialogButtonBox::Cancel,&dialog);
        QObject::connect(buttons,&QDialogButtonBox::accepted,&dialog,&QDialog::accept);
        QObject::connect(buttons,&QDialogButtonBox::rejected,&dialog,&QDialog::reject);
        layout->addWidget(buttons);
        if (dialog.exec()!=QDialog::Accepted) return;
        QSettings("MacaqueOS","ClassicControlStrip")
            .setValue("preferredMonitor",monitor->currentData().toString());
        setTheme(static_cast<Theme>(appearance->currentIndex()));
        setAutostart(startup->isChecked());
    }
    void restoreSelectedThemeDefaults() {
        // Leave icons, module order, monitor, position and autostart untouched.
        customSurface = QColor();
        customModuleSurface = QColor();
        customBorder = QColor();
        backgroundPattern = 0;
        backgroundTexturePath.clear();
        stripHeightPx = 34;
        moduleStepPx = 43;
        accent = theme == Theme::Dark ? QColor("#6885e0") : QColor("#333399");
        QSettings("MacaqueOS", "ClassicControlStrip").setValue("accentColor", accent.name());
        saveCreatorSettings();
        update();
    }
    bool hasPreviousAppearanceSettings() const {
        QSettings settings("MacaqueOS", "ClassicControlStrip");
        const QStringList keys = {"appearanceTheme", "creatorSurface", "creatorModuleSurface",
            "creatorBorder", "creatorPattern", "creatorTexture", "customIconPaths",
            "accentColor", "moduleOrder"};
        for (const QString &key : keys) if (settings.contains(key)) return true;
        return false;
    }
    void showFirstRunWizard() {
        QDialog dialog(this);
        dialog.setWindowTitle("Welcome to Classic Control Strip 2.0.3");
        dialog.setMinimumWidth(475);
        auto *layout = new QVBoxLayout(&dialog);
        auto *welcome = new QLabel("<h2>Welcome to Classic Control Strip</h2>"
            "<p>Bring the classic Mac OS 9 Control Strip to your MacaqueOS desktop.</p>"
            "<p>Choose a starting appearance. You can change everything later "
            "in the Theme Manager.</p>",&dialog);
        welcome->setWordWrap(true);layout->addWidget(welcome);
        auto *appearance = new QComboBox(&dialog);
        appearance->addItems({"Classic Platinum","Light","Dark"});
        appearance->setCurrentIndex(int(theme));
        layout->addWidget(new QLabel("Choose your appearance:",&dialog));
        layout->addWidget(appearance);
        auto *startup = new QCheckBox("Start Control Strip automatically at login",&dialog);
        startup->setChecked(true); layout->addWidget(startup);
        auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok|QDialogButtonBox::Cancel,&dialog);
        buttons->button(QDialogButtonBox::Ok)->setText("Finish Setup");
        QObject::connect(buttons,&QDialogButtonBox::accepted,&dialog,&QDialog::accept);
        QObject::connect(buttons,&QDialogButtonBox::rejected,&dialog,&QDialog::reject);
        layout->addWidget(buttons);
        if (dialog.exec()==QDialog::Accepted) {
            const bool upgrading = hasPreviousAppearanceSettings();
            setTheme(static_cast<Theme>(appearance->currentIndex()));
            if (!upgrading) restoreSelectedThemeDefaults();
            setAutostart(startup->isChecked());
            QSettings("MacaqueOS","ClassicControlStrip").setValue("firstRunCompleted",true);
        }
    }
    void showThemeManager() {
        QDialog dialog(this);
        dialog.setWindowTitle("MacaqueOS — Control Strip Theme Manager");
        dialog.setMinimumWidth(550);
        dialog.setStyleSheet(theme == Theme::Dark
            ? "QDialog {background:#30323a;color:#f2f2f2;} QLabel {color:#f2f2f2;}"
              "QGroupBox {border:1px solid #777c87;margin-top:12px;padding:10px;}"
              "QPushButton {background:#4c5060;color:white;border:1px solid #9296a2;padding:6px;}"
            : "QDialog {background:#d6d6d6;color:#111;} "
              "QGroupBox {border:1px solid #666;margin-top:12px;padding:10px;}"
              "QPushButton {background:#eeeeee;color:#111;border:1px solid #888;padding:6px;}");
        auto *layout = new QVBoxLayout(&dialog);
        auto *intro = new QLabel("Pick a built-in theme, customize its icons, or install a shared theme file.", &dialog);
        intro->setWordWrap(true);
        layout->addWidget(intro);
        auto *gallery = new QGroupBox("Theme Gallery — one-click apply", &dialog);
        auto *grid = new QGridLayout(gallery);
        struct Preset { const char *name; Theme mode; const char *accent; const char *bg; const char *fg; };
        const Preset presets[] = {
            {"Classic Platinum", Theme::Classic, "#333399", "#cccccc", "#111111"},
            {"Macintosh Light", Theme::Light, "#3478b8", "#f0f0f0", "#222222"},
            {"Macaque Dark", Theme::Dark, "#6885e0", "#363941", "#ffffff"},
            {"Bondi Blue", Theme::Light, "#168fbd", "#d4e9ef", "#17344a"},
            {"Grape", Theme::Dark, "#a77ad5", "#302b40", "#f5e9ff"},
            {"Graphite", Theme::Classic, "#62666e", "#bcbec3", "#161616"}
        };
        for (int i=0; i<6; ++i) {
            const Preset preset = presets[i];
            auto *card = new QWidget(gallery);
            auto *cardLayout = new QVBoxLayout(card);
            auto *preview = new QLabel(card);
            preview->setFixedHeight(38);
            preview->setAlignment(Qt::AlignCenter);
            preview->setText(QString("◧   ◷   ▣   ♪   ▥   ◉"));
            preview->setStyleSheet(QString("background:%1;color:%2;border:2px outset %3;"
                                           "font-size:18px;font-weight:bold;")
                                   .arg(preset.bg,preset.fg,preset.accent));
            cardLayout->addWidget(preview);
            auto *button = new QPushButton(QString::fromLatin1(preset.name), card);
            QObject::connect(button,&QPushButton::clicked,&dialog,[this,preset,&dialog] {
                setTheme(preset.mode);
                accent = QColor(preset.accent);
                QSettings("MacaqueOS", "ClassicControlStrip").setValue("accentColor", accent.name());
                update();
                dialog.accept();
            });
            cardLayout->addWidget(button);
            grid->addWidget(card,i/3,i%3);
        }
        layout->addWidget(gallery);
        auto *tools = new QGroupBox("Personalize & Share", &dialog);
        auto *buttons = new QGridLayout(tools);
        auto addButton = [&](const QString &label, int row, int col, auto fn) {
            auto *button = new QPushButton(label, tools);
            QObject::connect(button,&QPushButton::clicked,&dialog,fn);
            buttons->addWidget(button,row,col);
        };
        addButton("Theme Creator…",0,0,[this,&dialog] {
            dialog.accept();
            QTimer::singleShot(0,this,[this]{showThemeCreator();});
        });
        addButton("Visual Icon Editor…",0,1,[this,&dialog] {
            dialog.accept();
            QTimer::singleShot(0,this,[this] { showVisualIconEditor(); });
        });
        addButton("Accent Color…",3,0,[this,&dialog] {
            dialog.accept();
            QTimer::singleShot(0,this,[this] { chooseAccentColor(); });
        });
        addButton("Install Theme (.json)…",1,0,[this,&dialog] {
            dialog.accept();
            QTimer::singleShot(0,this,[this] { importPreferences(); });
        });
        addButton("Save & Share Theme…",1,1,[this,&dialog] {
            dialog.accept();
            QTimer::singleShot(0,this,[this] { exportPreferences(); });
        });
        addButton("Restore Original Icons",2,0,[this] {
            customIconPaths.clear();
            saveCustomIcons();
        });
        addButton("Open Theme Folder",2,1,[] {
            const QString folder = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
            QDir().mkpath(folder);
            QDesktopServices::openUrl(QUrl::fromLocalFile(folder));
        });
        layout->addWidget(tools);
        auto *hint = new QLabel("Theme files embed icon images, so you can share them with other MacaqueOS users. "
                                "Only install theme files from people you trust.", &dialog);
        hint->setWordWrap(true);
        layout->addWidget(hint);
        auto *close = new QDialogButtonBox(QDialogButtonBox::Close,&dialog);
        QObject::connect(close,&QDialogButtonBox::rejected,&dialog,&QDialog::reject);
        layout->addWidget(close);
        dialog.exec();
    }
    void chooseAccentColor() {
        QColor selected = QColorDialog::getColor(accent, this, "Control Strip Accent Color");
        if (!selected.isValid()) return;
        accent = selected;
        QSettings("MacaqueOS", "ClassicControlStrip").setValue("accentColor", accent.name());
        update();
    }
    void showCustomIconsMenu(const QPoint &at) {
        QMenu menu(this);
        menu.setStyleSheet(themeMenuStyle());
        menu.addAction("PNG, SVG, JPG or BMP icons (24 × 22 recommended)")->setEnabled(false);
        for (int id=0; id<moduleCount; ++id) {
            QMenu *sub = menu.addMenu(moduleNames[id]);
            sub->addAction("Choose Image…", [this,id] {
                QString path = QFileDialog::getOpenFileName(this, "Choose " + moduleNames[id] + " Icon",
                                  QDir::homePath(), "Images (*.png *.svg *.jpg *.jpeg *.bmp *.webp)");
                if (path.isEmpty()) return;
                QPixmap image(path);
                if (image.isNull()) {
                    QMessageBox::warning(this, "Invalid Icon", "This image could not be loaded.");
                    return;
                }
                // Copy to a persistent local theme folder so Downloads can be cleaned safely.
                const QString folder = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
                                       + "/icons";
                QDir().mkpath(folder);
                const QString ext = QFileInfo(path).suffix().toLower();
                const QString target = folder + "/module-" + QString::number(id) + "." + ext;
                if (QFileInfo(path).absoluteFilePath() != QFileInfo(target).absoluteFilePath()) {
                    QFile::remove(target);
                    if (!QFile::copy(path, target)) {
                        QMessageBox::warning(this, "Icon Error", "Could not save the selected icon.");
                        return;
                    }
                }
                customIconPaths[id] = target;
                saveCustomIcons();
            });
            sub->addAction("Use Original Pixel Icon", [this,id] {
                customIconPaths.remove(id);
                saveCustomIcons();
            });
        }
        menu.addSeparator();
        menu.addAction("Restore All Original Icons", [this] {
            customIconPaths.clear();
            saveCustomIcons();
        });
        menu.exec(at);
    }
    void exportPreferences() {
        const QString file = QFileDialog::getSaveFileName(this, "Export Control Strip Preferences",
                                  QDir::homePath() + "/control-strip-theme.json", "JSON Files (*.json)");
        if (file.isEmpty()) return;
        QJsonObject data;
        data["format"] = "MacaqueOS-ControlStrip-1";
        data["theme"] = int(theme);
        data["accent"] = accent.name();
        data["creatorHeight"] = stripHeightPx;
        data["creatorSpacing"] = moduleStepPx;
        data["creatorSurface"] = customSurface.isValid() ? customSurface.name() : QString();
        data["creatorModuleSurface"] = customModuleSurface.isValid() ? customModuleSurface.name() : QString();
        data["creatorBorder"] = customBorder.isValid() ? customBorder.name() : QString();
        data["creatorPattern"] = backgroundPattern;
        if (backgroundPattern==4) {
            QFile texture(backgroundTexturePath);
            if (texture.open(QIODevice::ReadOnly) && texture.size()<=2*1024*1024)
                data["creatorTexturePng"] = QString::fromLatin1(texture.readAll().toBase64());
        }
        data["leftOffset"] = leftOffset;
        data["bottomOffset"] = bottomOffset;
        QJsonArray ids, vis, icons;
        for (int id : order) ids.append(id);
        for (int id=0; id<moduleCount; ++id) {
            vis.append(visible[id]);
            const QString path = customIconPaths.value(id);
            if (!path.isEmpty()) {
                QFile iconFile(path);
                if (iconFile.open(QIODevice::ReadOnly) && iconFile.size() < 2*1024*1024) {
                    QJsonObject image;
                    image["extension"] = QFileInfo(path).suffix().toLower();
                    image["data"] = QString::fromLatin1(iconFile.readAll().toBase64());
                    icons.append(image);
                } else icons.append(QJsonValue());
            } else icons.append(QJsonValue());
        }
        data["order"] = ids; data["visible"] = vis; data["icons"] = icons;
        QSaveFile output(file);
        if (!output.open(QIODevice::WriteOnly) ||
            output.write(QJsonDocument(data).toJson(QJsonDocument::Indented)) < 0 ||
            !output.commit())
            QMessageBox::warning(this, "Export Failed", "Could not write the preferences file.");
    }
    void importPreferences() {
        const QString file = QFileDialog::getOpenFileName(this, "Import Control Strip Preferences",
                                   QDir::homePath(), "JSON Files (*.json)");
        if (file.isEmpty()) return;
        QFile input(file);
        if (!input.open(QIODevice::ReadOnly)) return;
        if (input.size() > 30*1024*1024) {
            QMessageBox::warning(this, "Theme Too Large", "Theme files must be under 30 MB.");
            return;
        }
        QJsonParseError error;
        const QJsonDocument doc = QJsonDocument::fromJson(input.readAll(), &error);
        if (error.error != QJsonParseError::NoError || !doc.isObject() ||
            doc.object().value("format").toString() != "MacaqueOS-ControlStrip-1") {
            QMessageBox::warning(this, "Import Failed", "Not a valid Control Strip theme file.");
            return;
        }
        const QJsonObject obj = doc.object();
        setTheme(static_cast<Theme>(qBound(0, obj.value("theme").toInt(0), 2)));
        const QColor color(obj.value("accent").toString("#333399"));
        if (color.isValid()) {
            accent = color;
            QSettings("MacaqueOS", "ClassicControlStrip").setValue("accentColor", accent.name());
        }
        stripHeightPx=qBound(28,obj.value("creatorHeight").toInt(34),56);
        moduleStepPx=qBound(43,obj.value("creatorSpacing").toInt(43),66);
        customSurface=QColor(obj.value("creatorSurface").toString());
        customModuleSurface=QColor(obj.value("creatorModuleSurface").toString());
        customBorder=QColor(obj.value("creatorBorder").toString());
        backgroundPattern=qBound(0,obj.value("creatorPattern").toInt(0),4);
        if (backgroundPattern==4) {
            const QByteArray encoded=obj.value("creatorTexturePng").toString().toLatin1();
            if (encoded.size()<=3*1024*1024) {
                const QByteArray bytes=QByteArray::fromBase64(encoded);
                QImage img;
                if (bytes.size()<=2*1024*1024 && img.loadFromData(bytes) &&
                    img.width()<=2048 && img.height()<=2048) {
                    const QString folder=QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)+"/textures";
                    QDir().mkpath(folder);
                    const QString target=folder+"/background.png";
                    if (img.save(target,"PNG")) backgroundTexturePath=target;
                }
            }
            if (backgroundTexturePath.isEmpty()) backgroundPattern=0;
        } else backgroundTexturePath.clear();
        saveCreatorSettings();
        const QJsonArray ids = obj.value("order").toArray();
        QVector<int> newOrder;
        for (const QJsonValue &v : ids) {
            const int id = v.toInt(-1);
            if (id>=0 && id<moduleCount && !newOrder.contains(id)) newOrder.append(id);
        }
        for (int id=0; id<moduleCount; ++id) if (!newOrder.contains(id)) newOrder.append(id);
        order = newOrder;
        const QJsonArray vis = obj.value("visible").toArray();
        for (int id=0; id<qMin(moduleCount,vis.size()); ++id)
            visible[id] = vis.at(id).toBool(visible[id]);
        const QJsonArray icons = obj.value("icons").toArray();
        customIconPaths.clear();
        for (int id=0; id<qMin(moduleCount,icons.size()); ++id) {
            const QJsonObject image = icons.at(id).toObject();
            const QString ext = image.value("extension").toString().toLower();
            const QStringList valid = {"png", "svg", "jpg", "jpeg", "bmp", "webp"};
            if (!valid.contains(ext)) continue;
            const QByteArray raw = QByteArray::fromBase64(image.value("data").toString().toLatin1());
            if (raw.isEmpty() || raw.size() > 2*1024*1024) continue;
            const QString folder = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/icons";
            QDir().mkpath(folder);
            const QString target = folder + "/imported-module-" + QString::number(id) + "." + ext;
            QSaveFile output(target);
            if (output.open(QIODevice::WriteOnly) && output.write(raw) == raw.size() && output.commit()) {
                if (!QPixmap(target).isNull()) customIconPaths[id] = target;
            }
        }
        saveCustomIcons(); saveModules(); updateSize();
        leftOffset = qBound(0, obj.value("leftOffset").toInt(leftOffset), maximumOffset());
        bottomOffset = qBound(0, obj.value("bottomOffset").toInt(bottomOffset), maximumBottomOffset());
        applyPosition(); savePosition(); update();
    }
    Theme theme = Theme::Classic;
    void setTheme(Theme next) {
        theme = next;
        QSettings("MacaqueOS", "ClassicControlStrip").setValue("appearanceTheme", int(theme));
        update();
    }
    QString themeMenuStyle() const {
        const bool dark = theme == Theme::Dark;
        const QString bg = dark ? "#30323a" : (theme == Theme::Light ? "#f2f2f2" : "#d6d6d6");
        const QString fg = dark ? "#f4f4f4" : "#111111";
        const QString border = dark ? "#777c87" : "#3b3b3b";
        const QString selected = accent.name();
        return QString(
          "QMenu { background:%1; color:%2; border:1px solid %3; padding:3px;"
          "font-family:'DejaVu Sans',sans-serif; font-size:11px; }"
          "QMenu::item { padding:4px 21px 4px 17px; margin:1px; }"
          "QMenu::item:selected { background:%4; color:white; }"
          "QMenu::item:disabled { color:%5; }"
          "QMenu::separator { height:1px; background:%3; margin:4px 7px; }"
          "QSlider::groove:horizontal { height:5px; background:%3; border:1px solid %3; }"
          "QSlider::handle:horizontal { background:%6; border:1px solid %3;"
          "width:12px; margin:-5px 0; }"
          "QLabel { color:%2; }")
          .arg(bg, fg, border, selected, dark ? "#a1a1a1" : "#777777",
               dark ? "#9ca6b7" : "#eeeeee");
    }
    void addThemeMenu(QMenu &parent) {
        QMenu *sub = parent.addMenu("Appearance Mode");
        sub->setStyleSheet(themeMenuStyle());
        const QStringList names = {"Classic Platinum", "Light", "Dark"};
        for (int i=0; i<names.size(); ++i) {
            QAction *a = sub->addAction(names.at(i));
            a->setCheckable(true);
            a->setChecked(int(theme)==i);
            QObject::connect(a, &QAction::triggered, sub, [this,i] {
                setTheme(static_cast<Theme>(i));
            });
        }
    }
    QVector<int> order;
    bool visible[moduleCount] = {true,true,true,true,true,true,true,true,false,false,false};
    LayerShellQt::Window *layerWindow = nullptr;
    bool dockedToLeft = false;
    int freeLeftOffset = 0;
    int freeBottomOffset = 0;
    int leftOffset = 0;
    int bottomOffset = 0;
    bool expanded=true;
    bool dragging=false;
    QPoint dragStartGlobal;
    int dragStartBottomOffset=0;
    int previewBottomOffset=0;
    int dragStartOffset=0;
    int previewOffset=0;
};

int main(int argc,char **argv) {
    QApplication app(argc,argv);
    app.setApplicationName("Classic Control Strip");
    // Prevent accidental duplicate panels, including when launching the
    // system-installed package and a local build at the same time.
    // Lock is scoped to this user, not to the executable's directory.
    const QString lockName = QString::fromLatin1(
        QCryptographicHash::hash(QDir::homePath().toUtf8(), QCryptographicHash::Sha256).toHex().left(16));
    QLockFile instanceLock(QDir::tempPath() + "/classic-control-strip-" + lockName + ".lock");
    instanceLock.setStaleLockTime(0);
    if (app.arguments().contains("--restart-control-strip"))
        QThread::msleep(750);
    if (!instanceLock.tryLock(1000)) {
        QMessageBox::information(nullptr, "Classic Control Strip",
                                 "Classic Control Strip is already running.\n"
                                 "Use its right-click menu to Quit or Restart it.");
        return 0;
    }
    app.setStyle(QStyleFactory::create("Fusion"));
    ControlStrip strip;
    strip.winId();
    strip.configureLayerShell();
    strip.show();
    strip.maybeShowFirstRun();
    return app.exec();
}
