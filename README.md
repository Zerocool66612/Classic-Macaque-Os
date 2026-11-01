# Macaque Classic 0.31 — laptop controls and Screenshot

Build: extract this kit into a new folder, open that folder in a terminal and run `bash build-iso.sh`. The ISO and checksum are always placed directly in `output/` after assembly/readback. The BIOS QEMU test then runs and saves its result alongside the ISO. A failed or inconclusive boot test no longer hides the assembled image in a root-owned build directory. Failure still means manual boot testing is required before installing.

## Included in this update

- Installer password rule fixed in the build: 8–128 characters, matching confirmation, no inherited dictionary-score rejection. The installed system's PAM policy is unchanged.
- Screenshot app in Applications, the system menu and Controls: Classic desktop or Classic window, plus actual Wayland full-screen and region capture through grim/slurp. Optional 0–10 second delay, pointer inclusion for native captures, preview, clipboard copy and automatic PNGs in Macaque HD/Pictures. Esc cancels region selection. Print opens the tool; Shift+Print selects a region; Ctrl+Print captures the display. Full-screen/region mode includes external app windows; Classic captures only cover the Qt desktop/windows.
- Laptop Controls panel: output volume, mute, microphone mute, screen brightness, battery status and a link to Battery & Power.
- Global Wayland laptop media keys: speaker mute/down/up, microphone mute and brightness down/up. Changes use the default PipeWire device and logind backlight controls in 5% steps. Output is capped at 100%; backlight stays at least 5%. Feedback appears over the Classic desktop and may be covered by external app windows.
- F-key row behavior follows the keyboard's media events. Fn/Fn Lock may be needed. Ordinary F1–F12 remain app shortcuts. No firmware-level Fn remapping is claimed. VM brightness and external-monitor brightness generally do not expose a supported laptop backlight.

Keyboard routing, PipeWire/logind boundaries, screenshot saving/cancel/failure cleanup and UI checks are verified with fixtures/offscreen Qt. Real laptop keys/backlight, microphone/audio hardware and live Wayland grim/slurp capture still need device testing. No new ISO was assembled here. The prior desktop was reached in VirtualBox with 3D acceleration enabled; physical USB boot remains unresolved.

## Build on Ubuntu / Kubuntu

Use an x86-64 Linux computer with Internet, Docker, about 60 GB free space and preferably 8 GB RAM. Open the extracted `macaque-classic-installer-kit-v0.31` folder in Terminal, or clone the repository. First-time Docker setup:

```bash
sudo apt update
sudo apt install docker.io
sudo systemctl start docker
```

Then run:

```bash
bash build-iso.sh
```

The builder uses a privileged Debian live-build container. It mounts this kit and its output folder; it does not flash USB or install to the host. Finished media is `output/macaque-classic-0.31-installer-DATE-TIME.iso` with `.sha256` and `.boot-check.json`. Boot-test logs are `output/boot-check.log` and `output/boot-check.qemu.log`. The generated ISO is copied before the QEMU test. An inconclusive test is reported explicitly; it is not a successful boot certification. The earlier empty serial-log failure can occur while the manually booted VM reaches the desktop. Manual VirtualBox testing requires VMSVGA with 3D acceleration enabled for the accelerated compositor.

## Installed desktop update

The included `packages/macaque-classic_0.31_amd64.deb` is only for an existing installed Macaque target, not the live USB or your normal Ubuntu/Kubuntu build host. It rebuilds the Control Strip for target Qt and may download dependencies:

```bash
sudo apt install ./packages/macaque-classic_0.31_amd64.deb
```

Save work and reboot afterward. Installer-policy and boot-image changes require a new ISO; a desktop update cannot change an already-built ISO. Package configuration is not tested in a real target chroot here. Keep your older working image and backups.

## Wayland and compatibility

The OS uses labwc, greetd/gtkgreet, native Qt/GTK/SDL Wayland clients, swaylock, swayidle and GTK/wlroots portals. Debian's labwc package pulls in XWayland binaries, but the session disables the XWayland server and provides no automatic X11 fallback. Flatpaks are launched with Wayland access and X11 sockets disabled. Older X11-only applications and some emulator builds will not run. External apps retain compositor-managed windows above the Classic desktop; internal apps use classic Qt frames.

The installed login requires a password. Live media has the `macaque` account and live-only recovery console on Ctrl+Alt+F2. Recovery autologin/account-initialization overrides are removed from the installed target. Lid closing uses system logind policy; custom lid actions are disabled. The visual screensaver is not a secure lock.

The offline installer and checked GRUB wrapper retain selected-disk handling and root UUID checks. Another physical disk can retain an older bootloader; do not rewrite other disks blindly. Swap defaults to none, with an optional swap file. Actual physical USB/bootloader installation remains unverified for this release.

## Testing and publication

26 desktop suites pass offscreen, including native Control Strip loading, real internal screenshot PNG/clipboard checks, media key routing and mocked PipeWire/logind/grim/slurp boundaries. Build-kit fixtures check password rules and installed recovery cleanup. The authoring runtime denies AF_UNIX, so the real shortcut socket test is explicitly skipped. No 0.31 ISO assembly, live display capture, PAM authentication or physical laptop key/backlight/audio test ran here.

[GitHub releases](https://github.com/Zerocool66612/Classic-Macaque-Os/releases) contain published ISO assets; source archives are build kits. Source pushes do not upload an ISO or update installed machines. Software Update discovers matching desktop `.deb` and `.deb.sha256` release assets. No signed custom Macaque update feed is claimed.

## Desktop gallery (0.30.4)

Current 0.30.4 UI, rendered from the Qt desktop code with the real embedded Control Strip and example data. These are offscreen UI captures, not photographs of a hardware boot. The author has reached the desktop in VirtualBox with 3D acceleration enabled; physical USB boot and installation remain under testing.

### Dark mode

![Macaque Classic 0.30.4 dark desktop with Files, Notes, Teapot Studio and Control Strip](docs/desktop-0.30.4-dark.png)

### Light mode

![Macaque Classic 0.30.4 light desktop with Files, Notes, Teapot Studio and Control Strip](docs/desktop-0.30.4-light.png)

The system menu uses the new white macaque profile, with green only on hover/press. ISO files belong under **Releases → Assets**; GitHub's source ZIP is a build kit, not a bootable ISO. Check the version shown on each release before downloading.

---

Project direction and original Control Strip: Drew Owen. AI-assisted development. No general project redistribution license has been selected; dependency notices remain in effect. No Apple ROM, OS image or application is bundled. Classic Mac emulator configuration does not implement Mac OS 9.2.2 application compatibility. No UNIX certification is claimed.
