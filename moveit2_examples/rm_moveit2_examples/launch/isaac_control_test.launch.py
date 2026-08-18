from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_description_content = Command([
        "xacro ",
        PathJoinSubstitution([
            FindPackageShare("rm_moveit2_examples"),
            "config",
            "rm_65_isaac_description.urdf.xacro",
        ]),
    ])

    robot_description = {
        "robot_description": robot_description_content
    }

    controllers_file = PathJoinSubstitution([
        FindPackageShare("rm_65_config"),
        "config",
        "ros2_controllers.yaml",
    ])

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            robot_description,
            controllers_file,
        ],
        output="screen",
    )

    joint_state_broadcaster_spawner = TimerAction(
        period=2.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2", "control", "load_controller",
                    "--set-state", "active",
                    "joint_state_broadcaster",
                ],
                output="screen",
            )
        ],
    )

    rm_group_controller_spawner = TimerAction(
        period=3.0,
        actions=[
            ExecuteProcess(
                cmd=[
                    "ros2", "control", "load_controller",
                    "--set-state", "active",
                    "rm_group_controller",
                ],
                output="screen",
            )
        ],
    )

    return LaunchDescription([
        control_node,
        joint_state_broadcaster_spawner,
        rm_group_controller_spawner,
    ])
