#!/usr/bin/env bash
set -euo pipefail

# V0 pipeline:
#   1. Use MoveIt2 to move RM65-B to a pre-grasp pose.
#   2. Evaluate the trained RL gripper policy on the simplified grasp task.
#
# This script assumes the following are already running in separate terminals:
#   - rm65_isaac_ros2_bridge.py
#   - ros2_control via isaac_control_test.launch.py
#   - move_group via rm_65_config move_group.launch.py

MOVEIT_WS="${MOVEIT_WS:-$HOME/robot-learning/rm_moveit2_ws}"
PROJECT_DIR="${PROJECT_DIR:-$HOME/robot-learning/rm-ik-rl}"
ISAAC_PYTHON="${ISAAC_PYTHON:-$HOME/isaac-sim-5.1.0/python.sh}"

PREGRASP_X="${PREGRASP_X:-0.35}"
PREGRASP_Y="${PREGRASP_Y:-0.00}"
PREGRASP_Z="${PREGRASP_Z:-0.32}"

EVAL_EPISODES="${ISAAC_EVAL_EPISODES:-3}"
EVAL_STEPS="${ISAAC_EVAL_STEPS:-240}"
HEADLESS="${ISAAC_HEADLESS:-1}"

echo "[Stage A] MoveIt2 pre-grasp planning"
echo "  target: x=${PREGRASP_X}, y=${PREGRASP_Y}, z=${PREGRASP_Z}"

cd "${MOVEIT_WS}"
source install/setup.bash

ros2 launch rm_moveit2_examples plan_pose.launch.py \
  x:="${PREGRASP_X}" \
  y:="${PREGRASP_Y}" \
  z:="${PREGRASP_Z}"

echo "[Stage B] RL gripper policy evaluation"

cd "${PROJECT_DIR}"

ISAAC_HEADLESS="${HEADLESS}" \
ISAAC_EVAL_EPISODES="${EVAL_EPISODES}" \
ISAAC_EVAL_STEPS="${EVAL_STEPS}" \
"${ISAAC_PYTHON}" isaac_sim/rm65_grasp_policy_eval.py

echo "[Done] Pre-grasp + RL grasp V0 pipeline completed."
