from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    rviz_arg = DeclareLaunchArgument(
        "rviz", default_value="true", description="Start RViz on laptop"
    )

    moveit_config = MoveItConfigsBuilder("arm", package_name="moveit").to_moveit_configs()

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=["-d", str(moveit_config.package_path / "config" / "moveit.rviz")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            moveit_config.planning_pipelines,
        ],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    return LaunchDescription([rviz_arg, move_group_node, rviz_node])
