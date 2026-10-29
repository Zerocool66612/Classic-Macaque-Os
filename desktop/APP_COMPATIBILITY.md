# Macaque Classic 0.13 — App Compatibility (experimental)

This update adds integration panels for native Linux Flatpaks and emulated classic
Mac software. The launch integration is implemented; a real Flatpak launch and Mac
OS guest boot have NOT been verified in this environment. Dependencies, emulator
binaries, ROMs, guest OS and apps are not bundled.

## Quick start

Close the old Macaque, extract this ZIP, open a terminal in its folder, then run:

    bash install-app-support.sh
    bash run-app-session.sh

The installer uses sudo to install Flatpak, Xephyr, Openbox, xauth, x11-utils,
dbus-daemon and procps from your configured Ubuntu/Debian repositories. It does not
add Flathub, download any apps or emulators, or change global Flatpak overrides.
The normal `bash run.sh` still runs the internal-app prototype and lets you set up
compatibility; external launches there explain how to start App Session.

App Session is the existing nested Creative Session with an additional launcher
name. Native app/emulator windows are managed by Openbox inside the outer Xephyr
window. They are not individual Qt MDI frames and retain native window decoration.
Alt+Tab switches external windows. Host X11 or XWayland DISPLAY is required.
GPU acceleration, Flatpak portals, sound and recording remain experimental.

## Flatpak Apps

Open Controls → Flatpak Apps, or launch Flatpak Apps from the system's Applications
menu. Refresh discovers installed user/system Flatpak apps and lets you filter and
launch them. No `.desktop` command strings are executed. Already-running instances
are refused to reduce the chance of forwarding to an existing host app. Some apps
can still implement non-D-Bus single-instance behavior; full compatibility cannot
be guaranteed. Quit all other instances first.

Install from file accepts a local .flatpakref or .flatpak bundle. Selecting a file
starts `flatpak install --user --assumeyes --noninteractive FILE` and may download
apps/runtimes or add a repository named by that reference. Output stays in the
internal panel. Only install references/bundles you intend to install. This is
file-based installation, not a remote app store or update/uninstall manager.

Launches explicitly allow X11, disable Wayland and choose X11 backends for GTK/Qt/
SDL. Flatpak forwards the current display authorization. Macaque HD is granted as
a read/write filesystem for that launch, so native apps can open/save Classic
files. Other app permissions come from the installed Flatpak. No permanent
permission override is saved. Wayland-only apps will not work in this mode.
A private session bus is used, but portal dialogs and desktop services may still
require host-specific integration. No claim of whole-system isolation is made.

## Classic Mac Apps

Open Controls → App Compatibility, or Classic Mac Apps in Applications. Choose:

- BasiliskII: 68k Mac software, compatible ROM/OS through Mac OS 8.1.
- SheepShaver: PowerPC Mac software, compatible ROM/OS through Mac OS 9.0.4.

Standard SheepShaver is not a Mac OS 9.2.2 solution. Matching the visual style of
9.2.2 does not mean its binaries run directly in the shell. This release does not
provide a QEMU/New World 9.2.2 guest or a general Mac binary compatibility layer.

Install a current compatible Linux emulator build separately, then select its
executable (or executable AppImage), compatible ROM, and a bootable guest hard-disk
image. Current builds must support `--config FILE`. Choose RAM, Save setup, then
Start Classic Mac inside App Session. File validation checks presence and paths;
it cannot verify that a ROM/OS combination will boot. Old emulator builds, kernel
memory-mapping policies and AppImage dependencies may need additional setup. This
app does not change sysctl settings or require elevated emulator execution.

The guest receives a dedicated Macaque HD/Classic Shared folder via ExtFS. Keep
classic software archives (.sit/.bin/.hqx) intact when transferring to preserve
resource forks; unpack/install and run applications inside the emulated Mac OS.
There is no direct Finder launch of individual old Mac applications in the outer
shell. Close/shut down guest Mac OS normally. The selected disk image is writable;
use a working copy and keep a separate backup. Do not mount the same guest disk
in another emulator at the same time. The outer backup tool only includes images
stored inside Macaque HD, subject to its existing size limits.

ROMs, Mac OS installation media and classic applications must be supplied by you.
No Apple files or applications are downloaded or included.

## Logs, lifetime and retained features

App failures show an internal explanation and a log location under the app data
folder / app-support-logs. Help → Show Data Folder opens that location internally.
No failure launches an app on the host display as a fallback. Normal desktop
closing checks tracked running processes and an active installation; nevertheless,
closing the outer Xephyr window can terminate apps with unsaved work. Some external
launchers detach child processes, so manually quit all external apps first.

Search Classic stays scoped to its catalog/Macaque HD. The icon-only system menu,
quiet top bar, Classic Sounds, Backup & Recovery, games, wallpapers and built-in
apps remain. Macaque is a desktop prototype, not a bootable OS or full compositor.

## Validation and sources

New tests validate Flatpak ID parsing, installed-app selection, session gating,
X11 permission arguments and display propagation, existing-instance refusal,
emulator preference generation and file checks, launch argv, missing-dependency
states and setup persistence. Tests use simulated external processes. They do not
prove emulator boot or real Flatpak compatibility. Existing desktop, migration,
search/backup, native-strip, sound and window/mouse tests remain included.

Primary references used for integration:
- https://docs.flatpak.org/en/latest/flatpak-command-reference.html
- https://basilisk.cebix.net/
- https://sheepshaver.cebix.net/
- https://github.com/cebix/macemu

Python 3.10+, PySide6 and chess are required. The included Control Strip library is
Linux x86-64; user-provided upstream source and adapter are in native/. python-chess
is GPL-3.0-or-later (https://github.com/niklasf/python-chess), installed via pip.
