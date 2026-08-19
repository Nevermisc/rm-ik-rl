from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("rm_65_description", package_name="rm_65_config")
        .to_moveit_configs()
    )

    return LaunchDescription([
        DeclareLaunchArgument("x", default_value="0.25"),
        DeclareLaunchArgument("y", default_value="-0.25"),
        DeclareLaunchArgument("z", default_value="0.45"),

        Node(
            package="rm_moveit2_examples",
            executable="plan_pose",
            output="screen",
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                {
                    "target_x": LaunchConfiguration("x"),
                    "target_y": LaunchConfiguration("y"),
                    "target_z": LaunchConfiguration("z"),
                },
            ],
        )
    ])
