#!/usr/bin/env bash
set -e
if ! command -v apt-get >/dev/null; then
  echo 'This installer supports Ubuntu/Debian. Install GIMP, Audacity, OBS Studio, Xephyr, Openbox, xauth, xdpyinfo, procps and dbus-run-session with your distribution package manager.' >&2
  exit 1
fi
printf 'Installing creative applications and the nested desktop layer.\nThis uses your configured Ubuntu/Debian repositories and asks for your sudo password.\n'
sudo apt-get update
sudo apt-get install gimp audacity obs-studio xserver-xephyr openbox xauth x11-utils dbus-daemon procps
printf '\nSetup complete. Run: bash run-creative.sh\n'
