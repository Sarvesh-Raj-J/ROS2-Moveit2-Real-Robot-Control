# Connecting MoveIt 2 to Custom Hardware Using Raspberry Pi 5 with ROS 2 Jazzy

This repository provides a reproducible ROS 2 Jazzy workspace for running MoveIt 2 on a laptop while controlling a custom robotic arm through a Raspberry Pi 5.

The project is designed as a practical reference for teams who want to:

- Plan and visualize motion on a laptop.
- Run ros2_control close to hardware on the Pi.
- Adapt the stack to their own URDF, joints, controllers, and transport layer.

## System architecture

- Laptop: MoveIt 2 (move_group + RViz + planning).
- Raspberry Pi 5: ros2_control + hardware interface plugin + device I/O.
- DDS network: ROS 2 Jazzy communication across the same LAN.

This separation keeps timing-sensitive hardware control on the Pi and higher compute tasks on the laptop.

## Repository layout

- src/botarm: arm description package (URDF/meshes/launch).
- src/botarm_hardware: custom ros2_control hardware plugin and servo utilities.
- src/moveit: MoveIt configuration package and launch files.
- scripts: setup, build, run, sync helpers.

## Prerequisites

### 1) Supported OS and ROS

- Ubuntu 24.04 on both laptop and Pi is recommended.
- ROS 2 Jazzy must be installed on both systems.
- Both devices must use the same ROS_DOMAIN_ID.

### 2) Raspberry Pi hardware prerequisites

- Raspberry Pi 5 with I2C enabled (if using PCA9685-based servo control).
- Proper servo power wiring and common ground.

Install Pi-side packages:

```bash
sudo apt update
sudo apt install -y i2c-tools python3-pip python3-smbus python3-venv python3-dev
```

Enable and verify I2C:

```bash
sudo usermod -aG i2c $USER
sudo reboot
i2cdetect -y 1
```

Install Python libraries for PCA9685 bridge tools:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motor pyyaml
```

## Network configuration (Laptop_IP and Pi_IP)

Create a copy of config/network.env.example and fill your actual IP addresses.

Example values:

- LAPTOP_IP=192.168.1.10
- PI_IP=192.168.1.20

On both devices, export consistent ROS network variables:

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Fast DDS configuration guidance is provided in docs/FASTDDS_SETUP.md.

## Workspace setup and build

Recommended workspace path on both laptop and Pi:

```bash
$HOME/agropilot2working_ws
```

Build using the provided script:

```bash
cd $HOME/agropilot2working_ws
chmod +x scripts/*.sh
bash scripts/setup_and_build.sh
```

The script performs:

- ROS environment sourcing.
- rosdep initialization/update.
- Dependency installation from src.
- colcon build --merge-install.

## Runtime sequence (step by step)

### Step 1: Start control stack on Raspberry Pi 5

Safe loopback bring-up:

```bash
cd $HOME/agropilot2working_ws
bash scripts/run_pi_control.sh
```

For real robot mode, launch directly and disable loopback:

```bash
source /opt/ros/jazzy/setup.bash
source $HOME/agropilot2working_ws/install/setup.bash
ros2 launch moveit pi_control.launch.py \
	ros2_control_hardware_type:=botarm_hardware/BotarmSystem \
	serial_port:=/dev/ttyAMA0 \
	baud_rate:=115200 \
	loopback_mode:=false
```

### Step 2: Start MoveIt 2 on laptop

```bash
cd $HOME/agropilot2working_ws
bash scripts/run_laptop_moveit.sh
```

### Step 3: Plan and execute from RViz

- Open the MotionPlanning panel.
- Set a target pose or joint state.
- Click Plan and Execute.

MoveIt sends trajectories to /arm_controller/follow_joint_trajectory.

## Hardware and servo test utilities

Direct per-joint servo command test:

```bash
bash scripts/run_servo_test.sh rotating_base_joint 100
```

The servo map file is located at src/botarm_hardware/config/servo_map.yaml.

## Using this stack with your own robotic arm URDF

Use the following migration path to adapt this workspace to a different robot.

### 1) Prepare your robot description package

- Add your URDF or Xacro model.
- Ensure joint names are final and consistent.
- Verify TF tree and joint limits.

### 2) Generate or update MoveIt configuration

- Run MoveIt Setup Assistant for your URDF/Xacro.
- Replace or merge generated config files into src/moveit/config.
- Confirm planning groups, end effectors, kinematics, and SRDF semantics.

### 3) Align ros2_control configuration

- Update controller definitions in src/moveit/config/ros2_controllers.yaml.
- Update MoveIt controller bridge in src/moveit/config/moveit_controllers.yaml.
- Ensure command/state interfaces match your hardware interface implementation.

### 4) Map joints to hardware channels

- Update src/botarm_hardware/config/servo_map.yaml for your actuator channels and limits.
- Keep joint names identical across URDF, controller YAMLs, and servo map.

### 5) Implement your real hardware transport

- Complete hardware read/write logic in src/botarm_hardware/src/botarm_system.cpp.
- Replace placeholder/TODO sections with your bus implementation (UART/CAN/I2C/SPI/Ethernet).

### 6) Validate in phases

- Phase A: loopback_mode:=true for interface and controller validation.
- Phase B: real hardware mode at low speeds/limited ranges.
- Phase C: full trajectory execution with safety checks.

## Dependency installation checklist

On both devices:

```bash
sudo apt update
sudo apt install -y \
	python3-colcon-common-extensions \
	python3-rosdep \
	python3-vcstool \
	ros-jazzy-ros2-control \
	ros-jazzy-ros2-controllers \
	ros-jazzy-moveit
```

Then run:

```bash
cd $HOME/agropilot2working_ws
source /opt/ros/jazzy/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
```

## Sync workspace to Raspberry Pi

From laptop:

```bash
bash scripts/sync_to_pi.sh <pi_user>@<pi_host>
```

Default target path on Pi:

```bash
$HOME/agropilot2working_ws
```

## Publishing this folder to GitHub

Run from the repository root:

```bash
git init
git add .
git commit -m "Initial commit: MoveIt 2 + Pi 5 custom hardware workspace"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

If the repository already exists locally, skip git init and only add/commit/push your changes.

## Additional documentation

- Fast DDS setup: docs/FASTDDS_SETUP.md
- Existing real robot setup notes: src/moveit/REAL_ROBOT_SETUP.md

## License

Refer to project or package-level license files as applicable.
