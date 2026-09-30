#!/usr/bin/env bash

# Smoke test for V3.
# This test checks that the Isaac scene, ROS2 bridge, link_6-follow gripper,
# and saved policy model can all be loaded together.
#
# It is not expected to grasp the cube unless MoveIt2 first moves RM65 link_6
# near the cube.  For full grasping, use this as the Isaac side of the stack
# and run MoveIt2 pre-grasp commands from separate terminals.

set -eo pipefail

cd ~/robot-learning/rm-ik-rl
source /opt/ros/humble/setup.bash

ISAAC_HEADLESS="${ISAAC_HEADLESS:-1}" \
ISAAC_MAX_STEPS="${ISAAC_MAX_STEPS:-160}" \
ISAAC_POLICY_START_STEP="${ISAAC_POLICY_START_STEP:-20}" \
ISAAC_GRIPPER_CONTROL_MODE="${ISAAC_GRIPPER_CONTROL_MODE:-policy}" \
~/isaac-sim-5.1.0/python.sh isaac_sim/rm65_isaac_bridge_with_policy_gripper_v3.py
