# Fast DDS Setup for Laptop + Raspberry Pi 5 (ROS 2 Jazzy)

This guide documents a practical Fast DDS configuration for running MoveIt 2 on a laptop and ros2_control on a Raspberry Pi 5.

## 1) Define your network values

Copy values from your LAN:

- LAPTOP_IP: IP address of the laptop running MoveIt 2.
- PI_IP: IP address of the Raspberry Pi 5 running hardware control.
- ROS_DOMAIN_ID: Any shared domain ID value (example: 42).

You can store them in config/network.env.example as a template before creating your local environment file.

## 2) Export required ROS variables on both devices

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Keep these values identical across laptop and Pi.

## 3) Optional: Fast DDS profile file for unicast peer discovery

Create a local file named fastdds_profiles.xml (not committed if you prefer private IP values) with your own addresses.

Example template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
  <participant profile_name="ros2_participant_profile" is_default_profile="true">
    <rtps>
      <builtin>
        <metatrafficUnicastLocatorList>
          <locator>
            <udpv4>
              <address>LAPTOP_IP</address>
              <port>7410</port>
            </udpv4>
          </locator>
          <locator>
            <udpv4>
              <address>PI_IP</address>
              <port>7410</port>
            </udpv4>
          </locator>
        </metatrafficUnicastLocatorList>
      </builtin>
    </rtps>
  </participant>
</profiles>
```

Then export:

```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=$HOME/agropilot2working_ws/fastdds_profiles.xml
```

## 4) Validate communication

On Pi:

```bash
source /opt/ros/jazzy/setup.bash
source $HOME/agropilot2working_ws/install/setup.bash
ros2 topic list
```

On laptop:

```bash
source /opt/ros/jazzy/setup.bash
source $HOME/agropilot2working_ws/install/setup.bash
ros2 topic list
```

Both sides should discover a consistent set of topics once stacks are launched.

## 5) Troubleshooting checklist

- Confirm both systems are on the same subnet.
- Confirm ping works both directions.
- Confirm ROS_DOMAIN_ID and RMW_IMPLEMENTATION match.
- Confirm firewall allows DDS UDP traffic.
- If discovery is unstable, restart launch order: Pi control stack first, then laptop MoveIt.

## 6) Recommended startup sequence

1. Export ROS and Fast DDS environment on Pi.
2. Launch Pi control stack.
3. Export ROS and Fast DDS environment on laptop.
4. Launch laptop MoveIt.

This order reduces startup race conditions in distributed deployments.
