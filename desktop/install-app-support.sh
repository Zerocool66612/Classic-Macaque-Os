#!/usr/bin/env bash
set -e
if ! command -v apt-get >/dev/null; then
 echo 'Install Flatpak, Xephyr, Openbox, xauth, x11-utils and dbus-run-session using your distribution package manager.'
 exit 1
fi
sudo apt-get update
sudo apt-get install flatpak xserver-xephyr openbox xauth x11-utils dbus-daemon procps
printf '\nApp Session dependencies installed. Run: bash run-app-session.sh\nClassic emulators, ROMs and Mac OS disks are supplied separately.\n'
