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
        DeclareLaunchArgument("center_x", default_value="0.30"),
        DeclareLaunchArgument("center_y", default_value="0.00"),
        DeclareLaunchArgument("center_z", default_value="0.45"),
        DeclareLaunchArgument("radius", default_value="0.05"),
        DeclareLaunchArgument("samples", default_value="36"),
        DeclareLaunchArgument("eef_step", default_value="0.01"),

        Node(
            package="rm65_moveit2_draw_circle",
            executable="draw_circle",
            output="screen",
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                {
                    "center_x": LaunchConfiguration("center_x"),
                    "center_y": LaunchConfiguration("center_y"),
                    "center_z": LaunchConfiguration("center_z"),
                    "radius": LaunchConfiguration("radius"),
                    "samples": LaunchConfiguration("samples"),
                    "eef_step": LaunchConfiguration("eef_step"),
                },
            ],
        )
    ])
