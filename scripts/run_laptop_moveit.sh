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

exec ros2 launch moveit laptop_moveit.launch.py
