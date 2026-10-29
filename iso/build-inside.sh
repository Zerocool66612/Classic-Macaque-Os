#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with build-iso.sh, or as root in Debian 13.' >&2; exit 1; }
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
 --bootappend-live 'boot=live quiet splash components username=macaque hostname=macaque-classic locales=en_US.UTF-8 keyboard-layouts=us' \
 --iso-application 'Macaque Classic Installer Preview' --iso-volume MACAQUE_CLASSIC
mkdir -p config/package-lists config/hooks/live
cp /kit/iso/packages.txt config/package-lists/macaque.list.chroot
python3 /kit/iso/prepare.py "$work/config/includes.chroot"
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
[[ -f "$work/readback-root/etc/lightdm/lightdm-gtk-greeter.conf" ]]
name="macaque-classic-0.25-installer-$(date -u +%Y%m%d-%H%M%S).iso"
cp -- "$image" "/output/$name"
(cd /output && sha256sum "$name" > "$name.sha256")
cp chroot/usr/share/macaque-build/manifest.txt /output/package-manifest.txt
printf '\nCreated: /output/%s\n' "$name"
