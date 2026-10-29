#!/usr/bin/env bash
set -euo pipefail
kit=$(cd -- "$(dirname -- "$0")" && pwd)
if [[ $(uname -m) != x86_64 ]]; then echo 'Build on an x86-64 Linux computer.' >&2; exit 1; fi
if ! command -v docker >/dev/null; then
 echo 'Install the builder first: sudo apt install docker.io' >&2
 echo 'Then: sudo systemctl start docker' >&2
 exit 1
fi
runner=(docker)
if ! docker info >/dev/null 2>&1; then runner=(sudo docker); fi
"${runner[@]}" info >/dev/null
mkdir -p "$kit/output"
# No host devices, home folder, Docker socket or host root are mounted in the builder.
# Privilege is required by live-build for chroot, mount and loop operations.
"${runner[@]}" build -t macaque-classic-iso-builder:trixie "$kit/iso"
"${runner[@]}" run --rm --privileged \
 --mount "type=bind,src=$kit,dst=/kit,readonly" \
 --mount "type=bind,src=$kit/output,dst=/output" \
 macaque-classic-iso-builder:trixie bash /kit/iso/build-inside.sh
printf '\nISO and checksum are in: %s/output\n' "$kit"
