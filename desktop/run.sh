#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"
export QT_STYLE_OVERRIDE=Fusion
printf '\nLaunching Macaque Classic 0.22.1 — Internal Applications\n\n'
# Reuse the working installation; do not launch an old desktop.py.
for candidate in .venv/bin/python3 ../macaque-classic-v0.14/.venv/bin/python3 ../macaque-classic-v0.13/.venv/bin/python3 ../macaque-classic-v0.12/.venv/bin/python3 ../macaque-classic-v0.11/.venv/bin/python3 ../macaque-classic-v0.10/.venv/bin/python3 ../macaque-classic-v0.9/.venv/bin/python3 ../macaque-classic-v0.8/.venv/bin/python3 ../macaque-classic-v0.7/.venv/bin/python3 ../macaque-classic-v0.6/.venv/bin/python3 ../macaque-classic-v0.5/.venv/bin/python3 ../classic-desktop/.venv/bin/python3 ../classic-desktop-v0.4/.venv/bin/python3 ../classic-desktop-v0.3/.venv/bin/python3; do
  if [ -x "$candidate" ] && "$candidate" -c 'import PySide6,chess' >/dev/null 2>&1; then
    exec "$candidate" "${MACAQUE_ENTRYPOINT:-$PWD/desktop.py}"
  fi
done
if ! command -v python3 >/dev/null; then
  echo 'Python 3 is required.' >&2; exit 1
fi
if [ ! -x .venv/bin/python3 ]; then python3 -m venv .venv; fi
.venv/bin/python3 -m pip install -r requirements.txt
exec .venv/bin/python3 "${MACAQUE_ENTRYPOINT:-$PWD/desktop.py}"
