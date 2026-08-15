"""End-to-end traditional FK/IK test for RM65-B in Isaac Sim.

This script loads the imported USD articulation, configures Lula from the
project-local URDF/YAML pair, solves a full-pose IK target, applies the joint
command, and reports both numerical IK error and simulated tracking error.
"""

from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": True})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.rotations import rot_matrix_to_quat
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.robot_motion.motion_generation import (
    ArticulationKinematicsSolver,
    LulaKinematicsSolver,
)


project_dir = Path(__file__).resolve().parent
usd_path = project_dir / "assets" / "RM65-B" / "RM65-B.usd"
urdf_path = project_dir / "assets" / "RM65-B" / "urdf" / "RM65-B.urdf"
description_path = project_dir / "rm65_robot_description.yaml"
prim_path = "/World/RM65_B"
end_effector_frame = "link_6"


def rotation_error_radians(actual: np.ndarray, target: np.ndarray) -> float:
    relative_rotation = actual.T @ target
    cosine = np.clip((np.trace(relative_rotation) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.arccos(cosine))


def main() -> int:
    required_files = (usd_path, urdf_path, description_path)
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        print(f"[RESULT] FAIL: Missing required files: {missing}")
        return 1

    world = World(stage_units_in_meters=1.0)
    add_reference_to_stage(usd_path=str(usd_path), prim_path=prim_path)
    robot = world.scene.add(SingleArticulation(prim_path=prim_path, name="rm65"))
    world.reset()

    start_q = np.array([0.0, -0.5, 1.0, 0.0, 0.5, 0.0])
    target_q = np.array([0.35, -0.8, 1.15, 0.25, 0.65, -0.3])
    robot.set_joint_positions(start_q)
    world.step(render=False)

    lula_solver = LulaKinematicsSolver(
        robot_description_path=str(description_path),
        urdf_path=str(urdf_path),
    )
    frame_names = lula_solver.get_all_frame_names()
    if end_effector_frame not in frame_names:
        print(f"[RM65] Available Lula frames: {frame_names}")
        print(f"[RESULT] FAIL: End-effector frame {end_effector_frame!r} was not found.")
        return 1

    articulation_ik = ArticulationKinematicsSolver(
        robot_articulation=robot,
        kinematics_solver=lula_solver,
        end_effector_frame_name=end_effector_frame,
    )

    # Generate a guaranteed-reachable target pose from a known joint state.
    target_position, target_rotation = lula_solver.compute_forward_kinematics(
        end_effector_frame, target_q
    )
    target_orientation = rot_matrix_to_quat(target_rotation)

    action, success = articulation_ik.compute_inverse_kinematics(
        target_position=target_position,
        target_orientation=target_orientation,
        position_tolerance=1e-4,
        orientation_tolerance=1e-3,
    )
    if not success or action.joint_positions is None:
        print("[RESULT] FAIL: Lula did not converge on the reachable RM65 target.")
        return 1

    solved_q = np.asarray(action.joint_positions, dtype=float)
    solved_position, solved_rotation = lula_solver.compute_forward_kinematics(
        end_effector_frame, solved_q
    )
    numerical_position_error = float(np.linalg.norm(solved_position - target_position))
    numerical_rotation_error = rotation_error_radians(solved_rotation, target_rotation)

    robot.get_articulation_controller().apply_action(action)
    for _ in range(240):
        world.step(render=False)

    actual_position, actual_rotation = articulation_ik.compute_end_effector_pose()
    tracking_position_error = float(np.linalg.norm(actual_position - target_position))
    tracking_rotation_error = rotation_error_radians(actual_rotation, target_rotation)

    print(f"[RM65] C-space joints: {lula_solver.get_joint_names()}")
    print(f"[RM65] End-effector frame: {end_effector_frame}")
    print(f"[RM65] Target position (m): {target_position.tolist()}")
    print(f"[RM65] IK solution (rad): {solved_q.tolist()}")
    print(f"[RM65] Numerical position error (m): {numerical_position_error:.8f}")
    print(f"[RM65] Numerical rotation error (rad): {numerical_rotation_error:.8f}")
    print(f"[RM65] Simulated tracking position error (m): {tracking_position_error:.8f}")
    print(f"[RM65] Simulated tracking rotation error (rad): {tracking_rotation_error:.8f}")

    numerical_ok = numerical_position_error < 1e-3 and numerical_rotation_error < 1e-2
    tracking_ok = tracking_position_error < 1e-2 and tracking_rotation_error < 5e-2
    if numerical_ok and tracking_ok:
        print("[RESULT] PASS: RM65-B traditional full-pose IK solved and moved the robot.")
        return 0

    print(f"[RM65] Checks: numerical={numerical_ok}, tracking={tracking_ok}")
    print("[RESULT] FAIL: IK solved, but the final error exceeded the project threshold.")
    return 1


try:
    exit_code = main()
finally:
    simulation_app.close()

raise SystemExit(exit_code)
