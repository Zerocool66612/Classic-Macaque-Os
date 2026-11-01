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
