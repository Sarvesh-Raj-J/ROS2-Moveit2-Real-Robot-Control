# Real Robot Setup (Laptop + Raspberry Pi 5)

## Recommended architecture
- Raspberry Pi 5: `ros2_control`, `botarm_hardware` plugin, `joint_state_broadcaster`, `arm_controller`
- Laptop: `move_group` + RViz + planning UI

This keeps motor timing close to hardware while using laptop compute for planning.

## Network requirements
- Same ROS 2 distro (`jazzy`) on both devices
- Same `ROS_DOMAIN_ID` on both
- Same LAN/subnet

## Raspberry Pi Ubuntu packages (PWM servo driver stack)
```bash
sudo apt update
sudo apt install -y i2c-tools python3-pip python3-smbus python3-venv python3-dev
```

Enable I2C and verify device:
```bash
sudo usermod -aG i2c $USER
sudo reboot
i2cdetect -y 1
```

Install Python driver libs (PCA9685 + servo helpers):
```bash
python3 -m pip install --upgrade pip
python3 -m pip install adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motor pyyaml
```

## 1) Build/install (both laptop and Pi)
```bash
source /opt/ros/jazzy/setup.bash
colcon build --merge-install --packages-select botarm botarm_hardware moveit --base-paths /home/emmanuel/botarm/arm /home/emmanuel/botarm_hardware /home/emmanuel/moveit
source /home/emmanuel/install/setup.bash
```

## 2) Start control stack on Raspberry Pi

### A) Plugin smoke-test (no real motor bus I/O)
```bash
source /opt/ros/jazzy/setup.bash
source /home/emmanuel/install/setup.bash
ros2 launch moveit pi_control.launch.py \
  ros2_control_hardware_type:=botarm_hardware/BotarmSystem \
  loopback_mode:=true
```

### B) Real robot mode (your transport implementation active)
```bash
source /opt/ros/jazzy/setup.bash
source /home/emmanuel/install/setup.bash
ros2 launch moveit pi_control.launch.py \
  ros2_control_hardware_type:=botarm_hardware/BotarmSystem \
  serial_port:=/dev/ttyAMA0 \
  baud_rate:=115200 \
  loopback_mode:=false
```

## 3) Start MoveIt on laptop
```bash
source /opt/ros/jazzy/setup.bash
source /home/emmanuel/install/setup.bash
ros2 launch moveit laptop_moveit.launch.py
```

## 4) Execute RViz target on real robot
- In RViz MotionPlanning, set pose/state target
- Click Plan and Execute
- MoveIt sends trajectory to `/arm_controller/follow_joint_trajectory`

## Important
- `botarm_hardware` plugin currently contains TODO sections for actual serial/CAN bus read/write.
- You must implement those TODOs in `botarm_hardware/src/botarm_system.cpp` for real motor control.

## Per-servo test script on Pi
After build:
```bash
source /home/emmanuel/install/setup.bash
ros2 run botarm_hardware pca9685_servo_control.py --center-all
ros2 run botarm_hardware pca9685_servo_control.py --joint link1_joint --sweep
ros2 run botarm_hardware pca9685_servo_control.py --joint gripper_joint --deg 120
```

Servo joint-channel map:
- `botarm_hardware/config/servo_map.yaml`
