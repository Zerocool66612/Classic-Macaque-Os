## 0.42 — GNU Chess and Classic window controls

- Play GNU Chess inside the built-in board, with Quick, Normal and Deep thinking times. GNU Chess is included in the ISO and installed as a desktop-update dependency.
- Engine searches run outside the UI thread and cancel on undo, game/mode changes and close. Practice and two-player modes remain available.
- Classic interface uses square Platinum close, minimize and zoom boxes. Appearance and Settings → Fonts provide Match theme, Classic and Traffic lights choices, applied immediately to open built-in windows.
- Native Linux windows receive matching Platinum glyphs; applications drawing their own title bars retain their own controls. Log out/in after updating for compositor theme changes.
- Keeps the installed/booting 0.41.2 installer foundation and light blue selections.

## 0.41.2 — Installer graphics and selection colors

- Route every live installer launch through the validated native Wayland helper.
- Use software Qt Quick rendering for installer slideshow stability; retain verbose logs and signal exit status.
- Use light blue desktop selections and accessibility highlights.
- Gate ISO publication on actual Wayland installer startup and branded slideshow rendering, alongside installed boot/update checks. Full GUI installation and laptop testing remain manual.

## 0.41.1 — Installer bootloader and dialog corrections

- Restrict the desktop maximize rule to the desktop title, keeping dialogs normal-sized.
- Finalize GRUB again after package changes, immediately before installer unmount.
- Reject BIOS targets that are not the whole disk containing the installed boot files.
- Probe fresh boot UUIDs, regenerate the menu before embedding GRUB, and remember the selected BIOS disk for Debian updates.
- Gate ISO publication on disposable installed-disk BIOS boot and a real desktop package upgrade with a subsequent two-drive boot.
- Publish matching desktop package/checksum alongside the ISO.
- Physical laptop, UEFI installation, and full Calamares GUI validation remain manual.

## 0.41 — Update Center and recovery

- Show release notes, transfer activity, running-version checks and update history.
- Publish desktop .deb + SHA256 release assets so the in-system updater can find them.
- Retain installed desktop packages and offer explicit rollback to saved older versions.
- Serialize desktop installs, verify inspected hashes again and record failed/cancelled operations.
- Add one-login recovery startup: skip startup apps, display restoration and window animations without changing preferences.
- Include desktop update history in local diagnostics reports.
- Rollback is package-only, not an OS snapshot; the first upgrade may lack a previous cached package.
- Real APT changes, recovery login and hardware installation require manual testing.

## 0.40.1 — Macaque Web downloads

- Follow user-clicked new-window download links inside browser tabs; block automatic popups.
- Use server-suggested filenames and unique default names for existing files.
- Add Web Downloads progress, cancellation, saved/failed status and Show in folder.
- Confirm before closing active downloads; keep download files separate from installation.
- Verified a real local HTTP attachment byte-for-byte with Chromium sandbox enabled.
- External authenticated downloads and physical-device integration still need testing.

## 0.40 — Optional work and fonts

- Pause optional UI timers when inactive; preserve hidden countdown alarms.
- Defer Chess, Teapot, browser and backup modules until requested.
- Bundle MIT-licensed Chicago Kare, Settings/Fonts and Standard fallback.
- Stage font and attribution into both ISO filesystem and desktop package.
- Keep USB, Wi-Fi, lock and power service behavior unchanged.

## 0.39 — Classic Finder behavior

- Spatial folder windows, per-folder view/geometry/layout memory, grid positioning.
- Managed aliases with Show Original, rename tracking and missing-target repair.
- Get Info panels with custom icons, labels and stationery pads; label sorting/search.
- Multi-selection retention, scoped file shortcuts, and multi-item file actions.
- Running-app menu with application hiding and workspace-aware Show All.
- Direct mounted-drive opening, deferred/revalidated safe eject, removal notices.
- Full/empty Trash icon, keeping the existing reversible Trash backend.
- Silent checks avoid audio device probing; explicit fake audio checks remain active.

## 0.30 Wayland preview

Native labwc session, greetd/gtkgreet login, swaylock/swayidle, portals, Wayland-only launch rules and compositor shortcut integration. Lid overrides disabled pending implementation; logind owns lid policy. Offscreen/fixture checks pass; live GPU/PAM/locking/installer integration still requires machine testing.

# Changelog

## 0.20 — Web, workspaces and files

- Embedded Qt WebEngine browser with tabs, bookmarks and website downloads;
  regular-user execution with sandbox retained. Live rendering remains unverified.
- Four internal workspaces, overview, names, move-window controls and shortcuts.
- File-manager sidebar, pinned folders, editable address, history, filter, sort,
  hidden-file control, live filesystem refresh, F5 and Ctrl+L.
- Welcome Center and optional startup preference.
- Safe publish helper for a separate empty GitHub repository.
- New integration tests; prior desktop features and data formats retained.

## 0.14 — Daily preview

- Added Classic Downloads: paste a direct HTTPS file link, track progress, cancel,
  and save into Macaque HD/Downloads without switching to the host browser.
- Included a GIMP Flatpak-reference link and an explicit Install downloaded Flatpak
  action that hands the downloaded file to the existing Flatpak installation panel.
- Added size/time/redirect limits, TLS validation, cancellation cleanup and protection
  against overwriting existing downloads. Files never install or run automatically.
- Prepared standalone GitHub project documentation, a source-only test runner,
  ignore rules and a concrete compatibility/status table.

## 0.13

Experimental Flatpak discovery/file-based installation and emulator setup panels.
Real Flatpak launches and Mac OS guest boots remain unverified.

## 0.12

Unified internal Search Classic (F6), icon-only system menu, Backup & Recovery,
internal ZIP/media associations and Copy Path.

## 0.11

Simplified top bar and original classic-style sound effects with volume/mute.

## 0.9–0.10

Built-in desktop apps, Chess, software-rendered Teapot Studio, wallpapers, mouse
preferences, file dragging, desktop settings, notifications and window controls.
