#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with build-iso.sh, or as root in Debian 13.' >&2; exit 1; }
python3 /kit/iso/test_dialog_rules.py
python3 /kit/iso/test_bootloader_checked.py
python3 /kit/iso/test_grub_theme.py
python3 /kit/iso/test_loop_devices.py
python3 /kit/build-desktop-deb.py --output /output
version=$(dpkg-deb -f /output/macaque-classic_*.deb Version)
work=$(mktemp -d /output/build-XXXXXX)
cd "$work"
echo "Build workspace: $work"
lb config --mode debian --distribution trixie --architectures amd64 \
 --binary-image iso-hybrid --archive-areas 'main contrib non-free-firmware' \
 --bootloaders 'syslinux grub-efi' --uefi-secure-boot enable \
 --debian-installer none --apt-recommends true --firmware-chroot true \
 --mirror-bootstrap https://deb.debian.org/debian/ \
 --mirror-chroot https://deb.debian.org/debian/ \
 --mirror-binary https://deb.debian.org/debian/ \
 --bootappend-live 'boot=live loglevel=7 systemd.show_status=1 plymouth.enable=0 console=ttyS0,115200n8 console=tty0 components username=macaque hostname=macaque-classic locales=en_US.UTF-8 keyboard-layouts=us' \
 --iso-application 'Macaque Classic Installer Preview' --iso-volume MACAQUE_CLASSIC
mkdir -p config/package-lists config/hooks/live
cp /kit/iso/packages.txt config/package-lists/macaque.list.chroot
python3 /kit/iso/prepare.py "$work/config/includes.chroot"
python3 /kit/iso/stage-grub.py live "$work/config"
cp /kit/iso/0100-macaque.hook.chroot config/hooks/live/
chmod +x config/hooks/live/0100-macaque.hook.chroot
lb build 2>&1 | tee /output/build-latest.log
image=live-image-amd64.hybrid.iso
[[ -s $image ]] || { echo 'live-build did not produce the expected ISO.' >&2; exit 1; }
# Check that the ISO includes both BIOS and EFI boot entries; not a boot test.
xorriso -indev "$image" -report_el_torito plain 2>&1 | tee /output/boot-layout.txt
grep -q 'UEFI' /output/boot-layout.txt
grep -q 'BIOS' /output/boot-layout.txt
# Read back the complete filesystem from the generated ISO, not the chroot.
xorriso -osirrox on -indev "$image" -extract /live/filesystem.squashfs "$work/readback.squashfs"
unsquashfs -processors 2 -no-progress -d "$work/readback-root" "$work/readback.squashfs" > /output/filesystem-readback.log 2>&1
[[ -f "$work/readback-root/opt/macaque-classic/terminal_app.py" ]]
[[ -f "$work/readback-root/usr/share/macaque-bootloader/manifest.json" ]]
[[ -f "$work/readback-root/etc/calamares/branding/macaque/show.qml" ]]
[[ -f "$work/readback-root/usr/share/plymouth/themes/macaque/startup.png" ]]
[[ -f "$work/readback-root/etc/greetd/config.toml" ]]
[[ -f "$work/readback-root/boot/grub/themes/macaque/theme.txt" ]]
[[ -f "$work/readback-root/etc/default/grub.d/60-macaque-theme.cfg" ]]
python3 /kit/iso/test-installer-graphics.py "$work/readback-root" /output > /output/installer-graphics.log 2>&1 || { cat /output/installer-graphics.log; cat /output/installer-graphics-compositor.log; cat /output/installer-graphics-calamares.log; exit 1; }
# Gate publication on a genuine installed-disk boot and real package upgrade.
python3 /kit/iso/test-installed-boot.py "$work/readback-root" /output "/output/macaque-classic_${version}_amd64.deb" > /output/installed-boot-test.log 2>&1 || { tail -n 100 /output/installed-boot-test.log; tail -n 100 /output/installed-fresh.log 2>/dev/null || true; tail -n 100 /output/installed-updated.log 2>/dev/null || true; exit 1; }
name="macaque-classic-${version}-installer-$(date -u +%Y%m%d-%H%M%S).iso"
cp -- "$image" "/output/$name"
(cd /output && sha256sum "$name" > "$name.sha256")
cp chroot/usr/share/macaque-build/manifest.txt /output/package-manifest.txt
printf '\nCreated: /output/%s\n' "$name"
if python3 /kit/iso/boot-check.py "/output/$name" /output/boot-check.log; then
 echo 'Automated BIOS userspace check passed; physical graphics/USB still need testing.'
else
 echo 'ISO created in output. Automated boot check did not confirm startup; test this preview manually before installation.' >&2
fi
if [[ -f /output/boot-check.log.result.json ]]; then cp /output/boot-check.log.result.json "/output/$name.boot-check.json"; fi
