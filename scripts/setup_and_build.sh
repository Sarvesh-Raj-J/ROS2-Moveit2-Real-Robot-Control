#!/usr/bin/env bash
set -euo pipefail

WS_DIR="${1:-$HOME/agropilot2working_ws}"
ROS_SETUP="/opt/ros/jazzy/setup.bash"

safe_source() {
  # ROS setup scripts can reference optional vars not set under `set -u`.
  set +u
  # shellcheck disable=SC1090
  source "$1"
  set -u
}

if [ ! -d "$WS_DIR/src" ]; then
  echo "Workspace src not found: $WS_DIR/src" >&2
  exit 1
fi

if [ ! -f "$ROS_SETUP" ]; then
  echo "ROS setup not found: $ROS_SETUP" >&2
  echo "Install ROS 2 Jazzy first or update ROS_SETUP in this script." >&2
  exit 1
fi

echo "[1/4] Source ROS environment"
safe_source "$ROS_SETUP"

echo "[2/4] Initialize rosdep (safe to run repeatedly)"
sudo rosdep init 2>/dev/null || true
rosdep update

echo "[3/4] Install dependencies"
rosdep install --from-paths "$WS_DIR/src" --ignore-src -r -y

echo "[4/4] Build workspace"
cd "$WS_DIR"
colcon build --merge-install

echo "Done. Use:"
echo "  source $ROS_SETUP"
echo "  source $WS_DIR/install/setup.bash"
