#!/usr/bin/env bash

# This file is a runbook, not a one-click launcher.
# The full MoveIt2 + ros2_control + Isaac Sim stack is easier to debug when
# each long-running process stays in its own terminal.

set -euo pipefail

cat <<'EOF'
Run these commands on the lab Ubuntu machine.

Terminal 1: start Isaac Sim bridge with the link_6-follow gripper.

  cd ~/robot-learning/rm-ik-rl
  source /opt/ros/humble/setup.bash
  ~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_bridge_with_link6_gripper_v2.py

Terminal 2: start ros2_control with the RM Isaac hardware plugin.

  cd ~/robot-learning/rm_moveit2_ws
  source install/setup.bash
  ros2 launch rm_moveit2_examples isaac_control_test.launch.py

Terminal 3: start MoveIt2 move_group.

  cd ~/robot-learning/rm_moveit2_ws
  source install/setup.bash
  ros2 launch rm_65_config move_group.launch.py

Terminal 4: send one MoveIt2 target pose.

  cd ~/robot-learning/rm_moveit2_ws
  source install/setup.bash
  ros2 launch rm_moveit2_examples plan_pose.launch.py x:=0.30 y:=0.20 z:=0.40

Useful checks:

  source /opt/ros/humble/setup.bash
  ros2 topic list | grep isaac
  ros2 topic echo /isaac_joint_states --once
  ros2 topic echo /isaac_joint_commands --once

Headless smoke test:

  cd ~/robot-learning/rm-ik-rl
  source /opt/ros/humble/setup.bash
  ISAAC_HEADLESS=1 ISAAC_MAX_STEPS=80 \
  GRIPPER_CLOSE_START_STEP=20 \
  GRIPPER_CLOSE_DURATION_STEPS=40 \
  ~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_bridge_with_link6_gripper_v2.py
EOF
