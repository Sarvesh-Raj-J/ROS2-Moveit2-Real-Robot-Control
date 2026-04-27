#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <pi_user@pi_host> [remote_ws_dir] [local_ws_dir]" >&2
  exit 1
fi

PI_TARGET="$1"
REMOTE_WS_DIR="${2:-~/agropilot2working_ws}"
LOCAL_WS_DIR="${3:-$HOME/agropilot2working_ws}"

rsync -av --delete \
  --exclude build --exclude install --exclude log --exclude .git \
  "$LOCAL_WS_DIR/" "$PI_TARGET:$REMOTE_WS_DIR/"

echo "Synced to $PI_TARGET:$REMOTE_WS_DIR"
