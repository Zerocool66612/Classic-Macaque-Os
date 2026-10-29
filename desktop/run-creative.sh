#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"
export MACAQUE_ENTRYPOINT="$PWD/creative_session.py"
exec bash ./run.sh
