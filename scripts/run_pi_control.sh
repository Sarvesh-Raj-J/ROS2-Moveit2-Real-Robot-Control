#!/usr/bin/env bash
set -euo pipefail

WS_DIR="${1:-$HOME/agropilot2working_ws}"
ROS_SETUP="/opt/ros/jazzy/setup.bash"

safe_source() {
  set +u
  # shellcheck disable=SC1090
  source "$1"
  set -u
}

safe_source "$ROS_SETUP"
safe_source "$WS_DIR/install/setup.bash"

# Defaults are hardware plugin loopback for safe bring-up.
exec ros2 launch moveit pi_control.launch.py \
  ros2_control_hardware_type:=botarm_hardware/BotarmSystem \
  loopback_mode:=true
