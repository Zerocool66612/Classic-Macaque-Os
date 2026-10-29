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
| Bootable OS, display server, secure lock | Not implemented |

The Python desktop and native strip are a prototype. The optional App Session
uses Xephyr/Openbox. It has not been established as a production desktop session.
External apps keep native decorations and use Alt+Tab; the Window menu counts
internal Qt windows only. Closing the outer session window can lose unsaved work.

## Source and licensing

Project direction and original Control Strip: Drew Owen. AI-assisted development.
No general open-source license has been selected for this project. Publication of
source is not a grant of a new redistribution license. Existing upstream notices
and dependency licenses remain in effect. No Apple ROM, OS image or Mac application
is bundled. The included native strip binary is Linux x86-64; source and rebuild
instructions are included. No host user data is included in the preview package.

Before calling compatibility complete, test on the target Ryzen 7 / RX 6700 XT:
HTTPS download → Flatpak install → nested launch, actual sound/video, keyboard
focus and graphics, and a guest boot with a supplied emulator/ROM/disk combination.
