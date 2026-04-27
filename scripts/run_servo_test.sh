#!/usr/bin/env bash
set -euo pipefail

JOINT="${1:-rotating_base_joint}"
DEG="${2:-100}"
WS_DIR="${3:-$HOME/agropilot2working_ws}"
ROS_SETUP="/opt/ros/jazzy/setup.bash"
CFG_PATH="$WS_DIR/src/botarm_hardware/config/servo_map.yaml"

safe_source() {
  set +u
  # shellcheck disable=SC1090
  source "$1"
  set -u
}

safe_source "$ROS_SETUP"
safe_source "$WS_DIR/install/setup.bash"

exec ros2 run botarm_hardware pca9685_servo_control.py \
  --joint "$JOINT" \
  --config "$CFG_PATH" \
  --deg "$DEG"
