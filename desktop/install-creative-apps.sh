#!/usr/bin/env bash
set -e
command -v apt-get >/dev/null || { echo "Use your distribution package manager to install gimp audacity obs-studio labwc qt6-wayland swayidle swaylock wlopm foot dbus-daemon procps"; exit 1; }
sudo apt-get update
sudo apt-get install gimp audacity obs-studio labwc qt6-wayland swayidle swaylock wlopm foot dbus-daemon procps
printf "\nSetup complete. Preview from a Wayland host: bash run-app-session.sh\n"
