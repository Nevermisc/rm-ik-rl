#!/usr/bin/env python3
"""Run a deterministic RM65+4C2 pre-grasp reach baseline in simulation only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--urdf", type=Path, required=True)
parser.add_argument("--description", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--trajectory-steps", type=int, default=240)
parser.add_argument("--settle-steps", type=int, default=120)
args = parser.parse_args()

from isaacsim import SimulationApp  # noqa: E402


simulation_app = SimulationApp({"headless": True})

import numpy as np  # noqa: E402
from isaacsim.core.api import World  # noqa: E402
from isaacsim.core.api.objects import VisualCuboid  # noqa: E402
from isaacsim.core.prims import SingleArticulation  # noqa: E402
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
from isaacsim.core.utils.stage import add_reference_to_stage  # noqa: E402
from isaacsim.core.utils.types import ArticulationAction  # noqa: E402
from isaacsim.robot_motion.motion_generation import (  # noqa: E402
    ArticulationKinematicsSolver,
    LulaKinematicsSolver,
)


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
END_EFFECTOR_FRAME = "link_6"
LOWER_LIMITS = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])
UPPER_LIMITS = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])


def rotation_error_radians(actual: np.ndarray, target: np.ndarray) -> float:
    relative = actual.T @ target
    cosine = np.clip((np.trace(relative) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.arccos(cosine))


def main() -> int:
    usd = args.usd.expanduser().resolve()
    urdf = args.urdf.expanduser().resolve()
    description = args.description.expanduser().resolve()
    output = args.output.expanduser().resolve()
    missing = [str(path) for path in (usd, urdf, description) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing required files: {missing}")
    if args.trajectory_steps < 2 or args.settle_steps < 1:
        raise ValueError("trajectory-steps must be >=2 and settle-steps must be >=1")

    world = World(stage_units_in_meters=1.0)
    world.get_physics_context().set_gravity(0.0)
    asset_prim = "/World/RM65_4C2"
    articulation_prim = f"{asset_prim}/root_joint"
    add_reference_to_stage(usd_path=str(usd), prim_path=asset_prim)
    robot = world.scene.add(SingleArticulation(prim_path=articulation_prim, name="rm65_4c2"))

    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
    start_q = np.array([0.0, -0.5, 1.0, 0.0, 0.5, 0.0], dtype=np.float64)
    seed_target_q = np.array([0.35, -0.8, 1.15, 0.25, 0.65, -0.3], dtype=np.float64)
    target_position, target_rotation = lula.compute_forward_kinematics(END_EFFECTOR_FRAME, seed_target_q)
    target_orientation = rot_matrix_to_quat(target_rotation)
    cube_position = target_position.copy()
    cube_position[2] -= 0.10
    world.scene.add(
        VisualCuboid(
            prim_path="/World/TargetCube",
            name="target_cube",
            position=cube_position,
            scale=np.array([0.05, 0.05, 0.05]),
            color=np.array([0.85, 0.10, 0.08]),
        )
    )
    world.reset()

    dof_names = list(robot.dof_names)
    arm_indices = [dof_names.index(name) for name in ARM_JOINTS]
    robot.set_joint_positions(start_q, joint_indices=arm_indices)
    world.step(render=False)
    articulation_ik = ArticulationKinematicsSolver(
        robot_articulation=robot,
        kinematics_solver=lula,
        end_effector_frame_name=END_EFFECTOR_FRAME,
    )
    initial_position, _ = articulation_ik.compute_end_effector_pose()
    action, ik_success = articulation_ik.compute_inverse_kinematics(
        target_position=target_position,
        target_orientation=target_orientation,
        position_tolerance=1e-4,
        orientation_tolerance=1e-3,
    )
    if not ik_success or action.joint_positions is None:
        raise AssertionError("Lula IK failed for deterministic reach target")
    solved_q = np.asarray(action.joint_positions, dtype=np.float64)
    if np.any(solved_q < LOWER_LIMITS + 0.02) or np.any(solved_q > UPPER_LIMITS - 0.02):
        raise AssertionError("IK solution violates the configured 0.02 rad joint-limit margin")

    controller = robot.get_articulation_controller()
    command_history = [start_q.copy()]
    for step in range(args.trajectory_steps):
        progress = (step + 1) / args.trajectory_steps
        smooth_progress = 3.0 * progress**2 - 2.0 * progress**3
        command = start_q + smooth_progress * (solved_q - start_q)
        controller.apply_action(
            ArticulationAction(joint_positions=command, joint_indices=np.asarray(arm_indices))
        )
        command_history.append(command.copy())
        world.step(render=False)
    for _ in range(args.settle_steps):
        controller.apply_action(
            ArticulationAction(joint_positions=solved_q, joint_indices=np.asarray(arm_indices))
        )
        world.step(render=False)

    actual_q = np.asarray(robot.get_joint_positions(joint_indices=arm_indices), dtype=np.float64)
    actual_position, actual_rotation = articulation_ik.compute_end_effector_pose()
    position_error = float(np.linalg.norm(actual_position - target_position))
    rotation_error = rotation_error_radians(actual_rotation, target_rotation)
    initial_distance = float(np.linalg.norm(initial_position - target_position))
    final_joint_error = float(np.max(np.abs(actual_q - solved_q)))
    commands = np.asarray(command_history)
    maximum_command_step = float(np.max(np.abs(np.diff(commands, axis=0))))
    passed = (
        position_error < 0.01
        and rotation_error < 0.05
        and final_joint_error < 0.03
        and maximum_command_step < 0.05
        and initial_distance > position_error + 0.05
    )
    report = {
        "status": "pass" if passed else "fail",
        "simulation_only": True,
        "task": "move link_6 to a deterministic pre-grasp pose 0.10 m above a red cube",
        "gravity_enabled": False,
        "gravity_note": "zero gravity isolates the kinematic reach baseline from the known 4C2 gravity issue",
        "dof_names": dof_names,
        "arm_joint_indices": arm_indices,
        "target_cube_position_m": cube_position.tolist(),
        "target_end_effector_position_m": target_position.tolist(),
        "start_joint_position_rad": start_q.tolist(),
        "ik_joint_position_rad": solved_q.tolist(),
        "actual_joint_position_rad": actual_q.tolist(),
        "trajectory_steps": args.trajectory_steps,
        "settle_steps": args.settle_steps,
        "initial_position_error_m": initial_distance,
        "final_position_error_m": position_error,
        "final_rotation_error_rad": rotation_error,
        "final_joint_error_rad": final_joint_error,
        "maximum_command_step_rad": maximum_command_step,
        "criteria": {
            "final_position_error_m_lt": 0.01,
            "final_rotation_error_rad_lt": 0.05,
            "final_joint_error_rad_lt": 0.03,
            "maximum_command_step_rad_lt": 0.05,
            "minimum_position_improvement_m_gt": 0.05,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"RM65_REACH_BASELINE={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


try:
    exit_code = main()
finally:
    simulation_app.close()

raise SystemExit(exit_code)
