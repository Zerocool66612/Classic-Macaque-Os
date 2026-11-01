#!/usr/bin/env bash
set -e
command -v apt-get >/dev/null || { echo "Use your distribution package manager to install flatpak labwc qt6-wayland swayidle swaylock wlopm foot dbus-daemon"; exit 1; }
sudo apt-get update
sudo apt-get install flatpak labwc qt6-wayland swayidle swaylock wlopm foot dbus-daemon
printf "\nSetup complete. Preview from a Wayland host: bash run-app-session.sh\n"
