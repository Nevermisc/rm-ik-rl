from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("rm_65_description", package_name="rm_65_config")
        .to_moveit_configs()
    )

    return LaunchDescription([
        Node(
            package="rm_moveit2_examples",
            executable="interactive_pose_commander",
            output="screen",
            emulate_tty=True,
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
            ],
        )
    ])
