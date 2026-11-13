#!/usr/bin/env bash
# Theme-only update for an installed Macaque system. No grub-install/disk writes.
set -euo pipefail
kit=$(cd -- "$(dirname -- "$0")" && pwd)
[[ $EUID == 0 ]] || { echo 'Run with sudo on your installed Macaque system.' >&2; exit 1; }
[[ -f /etc/macaque-installed && ! -e /etc/macaque-live ]] || { echo 'This is only for an installed Macaque system, not a live USB or another Linux desktop.' >&2; exit 1; }
command -v update-grub >/dev/null
[[ -f "$kit/grub-theme/theme.txt" && -f /boot/grub/grub.cfg ]] || { echo 'Missing theme assets or an existing GRUB configuration.' >&2; exit 1; }
backup=$(mktemp -d /var/backups/macaque-grub-theme-XXXXXXXX)
config=/etc/default/grub.d/60-macaque-theme.cfg
theme=/boot/grub/themes/macaque
mkdir -p /etc/default/grub.d /boot/grub/themes
if [[ -e $config ]]; then cp -a "$config" "$backup/config"; fi
if [[ -e $theme ]]; then cp -a "$theme" "$backup/theme"; fi
cp -a /boot/grub/grub.cfg "$backup/grub.cfg"
rollback() {
 rm -rf -- "$theme"
 if [[ -e "$backup/theme" ]]; then cp -a "$backup/theme" "$theme"; fi
 if [[ -e "$backup/config" ]]; then cp -a "$backup/config" "$config"; else rm -f -- "$config"; fi
 cp -a "$backup/grub.cfg" /boot/grub/grub.cfg
 echo "Theme update failed; previous menu restored. Backup: $backup" >&2
}
trap rollback ERR
mkdir -p "$theme"
cp -- "$kit"/grub-theme/*.png "$kit/grub-theme/theme.txt" "$theme/"
cp -- "$kit/grub-theme/60-macaque-theme.cfg" "$config"
update-grub
trap - ERR
printf 'Macaque startup theme installed. Previous menu saved in %s\nReboot when ready to see it.\n' "$backup"
