import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    ros2_control_hardware_type_arg = DeclareLaunchArgument(
        "ros2_control_hardware_type",
        default_value="botarm_hardware/BotarmSystem",
        description="ros2_control hardware plugin class",
    )
    serial_port_arg = DeclareLaunchArgument(
        "serial_port",
        default_value="/dev/ttyAMA10",
        description="Serial port for motor controller bridge",
    )
    baud_rate_arg = DeclareLaunchArgument(
        "baud_rate",
        default_value="115200",
        description="Serial baud rate for motor controller bridge",
    )
    loopback_mode_arg = DeclareLaunchArgument(
        "loopback_mode",
        default_value="true",
        description="Loop back command->state in plugin (set false for real bus IO)",
    )

    moveit_config = (
        MoveItConfigsBuilder("arm", package_name="moveit")
        .robot_description(
            mappings={
                "ros2_control_hardware_type": LaunchConfiguration("ros2_control_hardware_type"),
                "serial_port": LaunchConfiguration("serial_port"),
                "baud_rate": LaunchConfiguration("baud_rate"),
                "loopback_mode": LaunchConfiguration("loopback_mode"),
            }
        )
        .to_moveit_configs()
    )

    robot_description = moveit_config.to_dict()

    ros2_controllers_path = os.path.join(
        get_package_share_directory("moveit"), "config", "ros2_controllers.yaml"
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[robot_description, ros2_controllers_path],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        output="screen",
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "-c", "/controller_manager"],
        output="screen",
    )

    pca9685_bridge = Node(
        package="botarm_hardware",
        executable="pca9685_bridge.py",
        output="screen",
    )

    return LaunchDescription(
        [
            ros2_control_hardware_type_arg,
            serial_port_arg,
            baud_rate_arg,
            loopback_mode_arg,
            robot_state_publisher,
            ros2_control_node,
            TimerAction(period=3.0, actions=[joint_state_broadcaster_spawner]),
            TimerAction(period=5.0, actions=[arm_controller_spawner]),
            TimerAction(period=10.0, actions=[pca9685_bridge]),
        ]
    )
