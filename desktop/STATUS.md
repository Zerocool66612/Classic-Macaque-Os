0.32: seven Laptop & Reliability panels: Touchpad, Displays with independent rollback, Power Profiles, Bluetooth, Audio Devices, Recovery & Diagnostics and Installer Status. All 28 desktop suites and build-kit checks pass using offscreen Qt and simulated hardware services. Installer logging tested with harmless child processes. ISO assembly, live hardware, physical installation and reboot remain unverified.

0.31: installer password validation correction included; Screenshot app and Wayland grim/slurp capture; Laptop Controls and global media-key routing through PipeWire/logind; stable top-level ISO output with separate boot-check status. New service/capture boundaries checked using mocks, UI offscreen. Hardware/real Wayland capture not verified here.

0.30.4: transparent idle system-menu button, accent hover/pressed state and a new white macaque side-profile icon. Boot stack unchanged from 0.30.3; user reached the desktop in VirtualBox after enabling 3D acceleration. Physical USB boot remains unverified.

0.30.3 diagnostic boot candidate: restore recommends, MODULES=most, visible live kernel/systemd output, diskless BIOS QEMU userspace gate in builder. Runner arguments/marker detection verified with fixtures; generated ISO boot and physical boot not performed here.

0.30.2: candidate repair for live USB authentication/startup failure. Explicit libpam-systemd/login dependencies; greetd common PAM policies; live-user initialization ordered before greetd; live-only tty2 recovery autologin removed from installed targets. Account writes and PAM policy tested with fixtures, not actual PAM authentication. Physical boot and exact original failure cause remain unverified.

0.30.1: bundle labwc-rc.xml with the desktop and use it for installed session staging and nested previews. Regression check executes test_creative.py from the staged installed layout. Fixes the 0.30 chroot hook failure; no ISO assembly/boot performed here.

0.30 Wayland preview: labwc native session; greetd/gtkgreet login; swaylock and swayidle; wlopm blanking; wlroots/GTK portals; Wayland-only native/Flatpak launches; compositor shortcut IPC and foot recovery; shared ISO/update staging. Custom lid actions are disabled; logind manages lid suspend. 22 desktop suites pass offscreen. AF_UNIX is denied by the authoring runtime, so live shortcut transport is explicitly skipped and a real Wayland compositor was not run. ISO generation/staging tests pass. No ISO assembly/boot, DRM/GPU output, PAM login/unlock, screen sharing, suspend/resume or privileged display-manager migration was tested here. The .deb is assembled and inspected, not installed on a target.

0.29 Laptop & Updates: GUI Wi-Fi secrets over stdin to NetworkManager D-Bus; saved profile controls; battery alerts, brightness/lid/idle controls through logind and Xfce power manager; LightDM/light-locker integration; UDisks removable discovery, mount/eject, staged non-overwriting file copy; checksummed desktop release downloads and local .deb updates; APT system maintenance. Native daemon startup included. Service calls use fixtures/mocks; actual Wi-Fi authentication, lock/unlock/suspend/lid/backlight, USB filesystems and APT package installation are not verified on hardware. The .deb archive is built/extracted/inspected; its postinst compile is not executed in a real target chroot. No ISO was assembled in the authoring environment.

0.28: login-style platinum top bar with matching graphite dark variant. Desktop styling only; no bootloader behavior changes.

0.27: checked GRUB installation and fresh device probing; root UUID/menu/module checks and install diagnostic report. Actual bootloader writes, ISO assembly and BIOS/UEFI reboot remain untested here.

0.26: real NetworkManager Wi-Fi scan/radio UI and embedded nmcli authentication; sysfs battery percentage/charging in the top bar. All 19 suites pass offscreen, including fake nmcli scan and battery edge cases. Actual laptop adapter, authentication and battery hardware remain unverified.

0.24: embedded PTY Terminal uses Macaque MDI frame; original installer branding; version-matched cached BIOS/UEFI GRUB setup. Real PTY tests pass. Offline target preparation and package install calls are fixture/mocked checks, not a physical installation. ISO assembly and reboot remain unverified here.

0.23: dedicated native Control Strip Terminal launcher and visible desktop access; guided selected-disk swap release; Calamares default no-swap/optional swap-file configuration. Privileged disk operations tested with mocks only. Actual ISO build, storage installation and reboot are unverified in authoring environment.

v0.22: shared internal file clipboard and context menus added; file operations, multi-selection, protected and host-folder states covered by test_context.py.

v0.21: animation and monochrome icon checks added. Timed Qt offscreen transitions verified; perceived smoothness on physical GPU/display remains to be checked.

# Preview status

| Feature | Current status |
| --- | --- |
| Internal desktop apps, windows, search, preferences and file operations | Automated offscreen checks |
| Embedded WebEngine browser | Implemented; URL/root/sandbox guards checked; live rendering not verified in this environment |
| Four workspaces and upgraded file manager | Automated switching/move/filter/sort/history/watcher checks |
| Classic Downloads | Response/file-lifetime checks with simulated replies; live HTTPS not yet verified |
| Original sound effects | WAV/event checks; physical speaker playback not verified here |
| Backup and recovery | Round-trip and unsafe-archive checks; recovery never overwrites current files |
| Qt Media Player | UI checked; actual codec/device playback needs machine testing |
| Flatpak discovery/install/launch | Experimental integration; real launch not verified here |
| Basilisk II/SheepShaver | Configuration/launch arguments checked; no guest boot verified |
| Mac OS 9.2.2 application compatibility | Not implemented |
| Wayland OS session, login and secure lock | Implemented in ISO source; hardware/PAM integration unverified |

The Python desktop and native strip are a prototype. The OS and optional nested App Session
use labwc/Wayland. They have not been established as a production desktop session.
External apps keep native decorations and use Alt+Tab; the Window menu counts
internal Qt windows only. Closing the outer session window can lose unsaved work.

## Source and licensing

Project direction and original Control Strip: Drew Owen. AI-assisted development.
No general open-source license has been selected for this project. Publication of
source is not a grant of a new redistribution license. Existing upstream notices
and dependency licenses remain in effect. No Apple ROM, OS image or Mac application
is bundled. The native strip builds from included source against the target Qt. No host user data is included in the preview package.

Before calling compatibility complete, test on the target Ryzen 7 / RX 6700 XT:
HTTPS download → Flatpak install → Wayland launch, actual sound/video, keyboard
focus and graphics, and a guest boot with a supplied emulator/ROM/disk combination.
