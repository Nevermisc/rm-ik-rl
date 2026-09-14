#!/usr/bin/env python3
"""Verify that Lula's six-axis RM65 IK maps onto the combined RM65+4C2 USD."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--urdf", type=Path, required=True)
parser.add_argument("--description", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()

from isaacsim import SimulationApp  # noqa: E402


simulation_app = SimulationApp({"headless": True})

import numpy as np  # noqa: E402
from isaacsim.core.api import World  # noqa: E402
from isaacsim.core.prims import SingleArticulation  # noqa: E402
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
from isaacsim.core.utils.stage import add_reference_to_stage  # noqa: E402
from isaacsim.robot_motion.motion_generation import (  # noqa: E402
    ArticulationKinematicsSolver,
    LulaKinematicsSolver,
)


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
END_EFFECTOR_FRAME = "link_6"


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

    world = World(stage_units_in_meters=1.0)
    world.get_physics_context().set_gravity(0.0)
    asset_prim = "/World/RM65_4C2"
    articulation_prim = f"{asset_prim}/root_joint"
    add_reference_to_stage(usd_path=str(usd), prim_path=asset_prim)
    robot = world.scene.add(SingleArticulation(prim_path=articulation_prim, name="rm65_4c2"))
    world.reset()

    dof_names = list(robot.dof_names)
    arm_indices = [dof_names.index(name) for name in ARM_JOINTS]
    gripper_names = [name for name in dof_names if name.startswith("tool_")]
    start_q = np.array([0.0, -0.5, 1.0, 0.0, 0.5, 0.0], dtype=np.float64)
    target_q = np.array([0.35, -0.8, 1.15, 0.25, 0.65, -0.3], dtype=np.float64)
    robot.set_joint_positions(start_q, joint_indices=arm_indices)
    world.step(render=False)

    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
    solver_joint_names = list(lula.get_joint_names())
    if solver_joint_names != ARM_JOINTS:
        raise AssertionError(f"unexpected Lula joint order: {solver_joint_names}")
    if END_EFFECTOR_FRAME not in lula.get_all_frame_names():
        raise AssertionError(f"missing Lula frame: {END_EFFECTOR_FRAME}")

    articulation_ik = ArticulationKinematicsSolver(
        robot_articulation=robot,
        kinematics_solver=lula,
        end_effector_frame_name=END_EFFECTOR_FRAME,
    )
    target_position, target_rotation = lula.compute_forward_kinematics(END_EFFECTOR_FRAME, target_q)
    target_orientation = rot_matrix_to_quat(target_rotation)
    action, success = articulation_ik.compute_inverse_kinematics(
        target_position=target_position,
        target_orientation=target_orientation,
        position_tolerance=1e-4,
        orientation_tolerance=1e-3,
    )
    if not success or action.joint_positions is None:
        raise AssertionError("Lula IK failed on a pose generated from a reachable joint state")

    solved_q = np.asarray(action.joint_positions, dtype=np.float64)
    solved_position, solved_rotation = lula.compute_forward_kinematics(END_EFFECTOR_FRAME, solved_q)
    numerical_position_error = float(np.linalg.norm(solved_position - target_position))
    numerical_rotation_error = rotation_error_radians(solved_rotation, target_rotation)

    robot.set_joint_positions(solved_q, joint_indices=arm_indices)
    world.step(render=False)
    usd_position, usd_rotation = articulation_ik.compute_end_effector_pose()
    usd_position_error = float(np.linalg.norm(usd_position - target_position))
    usd_rotation_error = rotation_error_radians(usd_rotation, target_rotation)

    passed = (
        len(dof_names) == 12
        and len(gripper_names) == 6
        and numerical_position_error < 1e-3
        and numerical_rotation_error < 1e-2
        and usd_position_error < 1e-3
        and usd_rotation_error < 1e-2
    )
    report = {
        "status": "pass" if passed else "fail",
        "usd": str(usd),
        "articulation_prim": articulation_prim,
        "dof_count": len(dof_names),
        "dof_names": dof_names,
        "arm_joint_indices": arm_indices,
        "lula_joint_names": solver_joint_names,
        "gripper_dof_count": len(gripper_names),
        "end_effector_frame": END_EFFECTOR_FRAME,
        "target_joint_position_rad": target_q.tolist(),
        "solved_joint_position_rad": solved_q.tolist(),
        "numerical_position_error_m": numerical_position_error,
        "numerical_rotation_error_rad": numerical_rotation_error,
        "combined_usd_position_error_m": usd_position_error,
        "combined_usd_rotation_error_rad": usd_rotation_error,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"COMBINED_IK_TEST={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


try:
    exit_code = main()
finally:
    simulation_app.close()

raise SystemExit(exit_code)
