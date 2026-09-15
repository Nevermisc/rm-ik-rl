#!/usr/bin/env python3
"""Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab."""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--urdf", type=Path, required=True)
parser.add_argument("--description", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--transfer-joint-1-rad", type=float, default=0.8)
parser.add_argument("--diagnose-approach-only", action="store_true")
parser.add_argument("--collision-bypass-during-approach", action="store_true")
parser.add_argument("--initialize-at-grasp", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import numpy as np  # noqa: E402
import torch  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402

enable_extension("isaacsim.robot_motion.motion_generation")

from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import math as math_utils  # noqa: E402
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver  # noqa: E402
from pxr import PhysxSchema, UsdPhysics  # noqa: E402


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
MOVING_GRIPPER_BODY_PATHS = {
    "/World/Robot/tool_r_1",
    "/World/Robot/tool_l_1",
    "/World/Robot/tool_r_2",
    "/World/Robot/tool_l_2",
    "/World/Robot/tool_r_3",
    "/World/Robot/tool_l_3",
}
BLOCK_SIZE = (0.060, 0.040, 0.025)
BLOCK_MASS_KG = 0.030
SOURCE_BLOCK_POSITION = np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)
SOURCE_BLOCK_QUATERNION_WXYZ = (-0.20872162, -0.00000211, 0.97797507, 0.00002437)
TARGET_PLATFORM_SIZE = (0.200, 0.200, 0.040)
TARGET_PLATFORM_TOP_Z = 0.650
RELEASE_DOWNWARD_SPEED_M_S = 0.10
RELEASE_SEPARATION_ASSIST_M = 0.05
TIP_LOCAL_POINTS = {
    "tool_r_2": (0.04368, -0.00645, 0.01250),
    "tool_l_2": (0.04368, 0.00645, 0.01257),
}


def rotate_about_z(position: np.ndarray, angle: float) -> np.ndarray:
    cosine, sine = np.cos(angle), np.sin(angle)
    return np.array(
        [cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],
        dtype=np.float64,
    )


def quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return np.array(
        [
            lw * rw - lx * rx - ly * ry - lz * rz,
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
        ],
        dtype=np.float64,
    )


def quaternion_to_matrix_wxyz(quaternion: np.ndarray) -> np.ndarray:
    w, x, y, z = quaternion
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def tip_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
    body_id = list(robot.data.body_names).index(body_name)
    local = torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
    )[0]


def smooth_move(
    sim: SimulationContext,
    robot: Articulation,
    cube: RigidObject,
    state: torch.Tensor,
    joint_ids: list[int],
    start: np.ndarray,
    target: np.ndarray,
    steps: int,
    phase: str,
) -> None:
    print(f"PICK_PLACE_STAGE={phase}_START", flush=True)
    for step in range(steps):
        progress = (step + 1) / steps
        smooth = 3.0 * progress**2 - 2.0 * progress**3
        command = start + smooth * (target - start)
        state[:, joint_ids] = torch.as_tensor(command, device=sim.device, dtype=state.dtype)
        robot.set_joint_position_target(state)
        robot.write_data_to_sim()
        cube.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        cube.update(sim.get_physics_dt())
    print(f"PICK_PLACE_STAGE={phase}_DONE", flush=True)


def hold(
    sim: SimulationContext,
    robot: Articulation,
    cube: RigidObject,
    state: torch.Tensor,
    steps: int,
) -> None:
    for _ in range(steps):
        robot.set_joint_position_target(state)
        robot.write_data_to_sim()
        cube.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        cube.update(sim.get_physics_dt())


def spawn_target_platform(
    path: str,
    position: np.ndarray,
    color: tuple[float, float, float],
) -> None:
    cfg = sim_utils.CuboidCfg(
        size=TARGET_PLATFORM_SIZE,
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color),
        physics_material=sim_utils.RigidBodyMaterialCfg(
            static_friction=1.0,
            dynamic_friction=0.8,
            restitution=0.0,
            friction_combine_mode="max",
        ),
    )
    cfg.func(path, cfg, translation=tuple(position))


def main() -> int:
    usd = args.usd.expanduser().resolve()
    urdf = args.urdf.expanduser().resolve()
    description = args.description.expanduser().resolve()
    output = args.output.expanduser().resolve()
    missing = [str(path) for path in (usd, urdf, description) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing required files: {missing}")
    if abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2:
        raise ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")

    grasp_arm = np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)
    lift_arm = np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)
    target_lift_arm = lift_arm.copy()
    target_lift_arm[0] = args.transfer_joint_1_rad
    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
    grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
    lift_link_position, _ = lula.compute_forward_kinematics("link_6", lift_arm)
    expected_lift_translation = lift_link_position - grasp_link_position
    expected_source_lift_block_position = SOURCE_BLOCK_POSITION + expected_lift_translation

    source_block_quaternion = np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
    transfer_quaternion = np.array(
        [np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],
        dtype=np.float64,
    )
    target_release_position = rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)
    target_block_position = target_release_position.copy()
    target_block_position[2] = TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
    target_block_quaternion = quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)
    target_platform_position = np.array(
        [
            target_block_position[0],
            target_block_position[1],
            TARGET_PLATFORM_TOP_Z - TARGET_PLATFORM_SIZE[2] / 2.0,
        ],
        dtype=np.float64,
    )

    sim = SimulationContext(
        sim_utils.SimulationCfg(
            dt=1.0 / 240.0,
            device=args.device,
            physics_material=sim_utils.RigidBodyMaterialCfg(
                static_friction=1.5,
                dynamic_friction=1.2,
                restitution=0.0,
                friction_combine_mode="max",
            ),
        )
    )
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
    light_cfg.func("/World/Light", light_cfg)
    if not args.diagnose_approach_only:
        spawn_target_platform("/World/TargetPlatform", target_platform_position, (0.12, 0.45, 0.20))
    target_platform_collision_apis = []
    for prim in get_current_stage().Traverse():
        if str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI):
            collision_api = UsdPhysics.CollisionAPI(prim)
            collision_api.CreateCollisionEnabledAttr().Set(False)
            target_platform_collision_apis.append(collision_api)

    robot = Articulation(
        ArticulationCfg(
            prim_path="/World/Robot",
            spawn=sim_utils.UsdFileCfg(
                usd_path=str(usd),
                activate_contact_sensors=True,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                    enabled_self_collisions=False,
                    solver_position_iteration_count=64,
                    solver_velocity_iteration_count=4,
                ),
            ),
            init_state=ArticulationCfg.InitialStateCfg(joint_pos={"joint_.*": 0.0, "tool_.*": 0.0}),
            actuators={
                "arm": ImplicitActuatorCfg(
                    joint_names_expr=["joint_[1-6]"],
                    effort_limit_sim=300.0,
                    velocity_limit_sim=1.0,
                    stiffness=1000.0,
                    damping=100.0,
                ),
                "gripper": ImplicitActuatorCfg(
                    joint_names_expr=["tool_.*"],
                    effort_limit_sim=20.0,
                    velocity_limit_sim=1.0,
                    stiffness=120.0,
                    damping=12.0,
                ),
            },
        )
    )
    cube = RigidObject(
        RigidObjectCfg(
            prim_path="/World/Cube",
            spawn=sim_utils.CuboidCfg(
                size=BLOCK_SIZE,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=True,
                    solver_position_iteration_count=32,
                    solver_velocity_iteration_count=4,
                    max_depenetration_velocity=1.0,
                ),
                mass_props=sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.5,
                    dynamic_friction=1.2,
                    restitution=0.0,
                    friction_combine_mode="max",
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=tuple(SOURCE_BLOCK_POSITION),
                rot=SOURCE_BLOCK_QUATERNION_WXYZ,
            ),
        )
    )

    isolated_paths = []
    for prim in get_current_stage().Traverse():
        path = str(prim.GetPath())
        if path in MOVING_GRIPPER_BODY_PATHS and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
            isolated_paths.append(path)
    cube_prim = get_current_stage().GetPrimAtPath("/World/Cube")
    cube_rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)
    cube_rigid_body_api.CreateDisableGravityAttr().Set(True)
    cube_collision_apis = []
    for prim in get_current_stage().Traverse():
        if str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI):
            collision_api = UsdPhysics.CollisionAPI(prim)
            cube_collision_apis.append(collision_api)
            if args.collision_bypass_during_approach:
                collision_api.CreateCollisionEnabledAttr().Set(False)
    if not cube_collision_apis:
        raise RuntimeError("no CollisionAPI prim found below /World/Cube")

    sim.reset()
    robot.reset()
    cube.reset()
    joint_names = list(robot.data.joint_names)
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]

    grasp_link_quaternion = rot_matrix_to_quat(grasp_link_rotation)
    outward_direction = quaternion_to_matrix_wxyz(source_block_quaternion)[:, 0]
    retreat_distances = np.linspace(0.02, 0.10, 5)
    retreat_waypoints = []
    warm_start = grasp_arm.copy()
    for distance in retreat_distances:
        waypoint_position = grasp_link_position - distance * outward_direction
        waypoint_q, success = lula.compute_inverse_kinematics(
            "link_6",
            waypoint_position,
            grasp_link_quaternion,
            warm_start=warm_start,
            position_tolerance=1e-4,
            orientation_tolerance=1e-3,
        )
        if not success:
            raise RuntimeError(f"Lula failed to solve Cartesian retreat waypoint at {distance:.3f} m")
        warm_start = np.asarray(waypoint_q, dtype=np.float64)
        retreat_waypoints.append(warm_start.copy())
    pregrasp_arm = grasp_arm.copy() if args.initialize_at_grasp else retreat_waypoints[-1]

    state = robot.data.default_joint_pos.clone()
    state[:, arm_ids] = torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)
    state[:, gripper_ids] = 0.0
    robot.write_joint_state_to_sim(state, torch.zeros_like(state))
    cube_pose = cube.data.default_root_state[:, :7].clone()
    cube_pose[:, :3] = torch.as_tensor(SOURCE_BLOCK_POSITION, device=sim.device, dtype=cube_pose.dtype)
    cube_pose[:, 3:7] = torch.as_tensor(
        SOURCE_BLOCK_QUATERNION_WXYZ, device=sim.device, dtype=cube_pose.dtype
    )
    cube.write_root_pose_to_sim(cube_pose)
    cube.write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))
    hold(sim, robot, cube, state, 60 if args.initialize_at_grasp else 240)
    settled_source_position = cube.data.root_pos_w[0].clone()
    print("PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True)

    approach_waypoints = [] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]
    previous_waypoint = pregrasp_arm
    for index, waypoint in enumerate(approach_waypoints, start=1):
        smooth_move(
            sim,
            robot,
            cube,
            state,
            arm_ids,
            previous_waypoint,
            waypoint,
            120,
            f"APPROACH_{index}",
        )
        previous_waypoint = waypoint
    if args.collision_bypass_during_approach:
        hold(sim, robot, cube, state, 240)
        pre_restore_arm_error = float(
            np.max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))
        )
        print(f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True)
    if args.collision_bypass_during_approach:
        for collision_api in cube_collision_apis:
            collision_api.CreateCollisionEnabledAttr().Set(True)
        print("PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True)
    if not args.initialize_at_grasp:
        hold(sim, robot, cube, state, 240)
    actual_approach_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
    open_l2_midpoint = 0.5 * (
        tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")
    )
    open_midpoint_to_block = float(
        torch.linalg.vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])
    )
    print(
        "PICK_PLACE_APPROACH="
        + json.dumps(
            {
                "max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
                "l2_midpoint_to_block_center_m": open_midpoint_to_block,
            }
        ),
        flush=True,
    )
    close_start = np.zeros(len(gripper_ids), dtype=np.float64)
    close_target = np.full(len(gripper_ids), 0.65, dtype=np.float64)
    smooth_move(sim, robot, cube, state, gripper_ids, close_start, close_target, 180, "CLOSE")
    hold(sim, robot, cube, state, 120)
    closed_position = cube.data.root_pos_w[0].clone()
    closed_l2_gap = float(
        torch.linalg.vector_norm(
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
        )
    )
    closed_gripper_joint_position = robot.data.joint_pos[0, gripper_ids].clone()

    if args.diagnose_approach_only:
        diagnostic = {
            "status": "diagnostic",
            "simulation_only": True,
            "collision_bypass_during_approach": args.collision_bypass_during_approach,
            "initialized_at_grasp": args.initialize_at_grasp,
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
            "closed_position_m": closed_position.detach().cpu().tolist(),
            "approach_actual_arm_joint_position_rad": actual_approach_arm.tolist(),
            "approach_target_arm_joint_position_rad": grasp_arm.tolist(),
            "cartesian_retreat_distances_m": retreat_distances.tolist(),
            "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
            "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
            "closed_l2_tip_gap_m": closed_l2_gap,
            "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(diagnostic, indent=2), flush=True)
        return 0

    cube_rigid_body_api.CreateDisableGravityAttr().Set(False)
    smooth_move(sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT")
    hold(sim, robot, cube, state, 120)
    lifted_position = cube.data.root_pos_w[0].clone()

    smooth_move(sim, robot, cube, state, arm_ids, lift_arm, target_lift_arm, 360, "TRANSFER")
    for collision_api in target_platform_collision_apis:
        collision_api.CreateCollisionEnabledAttr().Set(True)
    if target_platform_collision_apis:
        print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
        hold(sim, robot, cube, state, 120)
    pre_release_position = cube.data.root_pos_w[0].clone()

    smooth_move(sim, robot, cube, state, gripper_ids, close_target, close_start, 180, "OPEN")
    release_pose = cube.data.root_state_w[:, :7].clone()
    release_pose[:, 2] -= RELEASE_SEPARATION_ASSIST_M
    cube.write_root_pose_to_sim(release_pose)
    release_velocity = torch.zeros_like(cube.data.root_vel_w)
    release_velocity[:, 2] = -RELEASE_DOWNWARD_SPEED_M_S
    cube.write_root_velocity_to_sim(release_velocity)
    print("PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True)
    hold(sim, robot, cube, state, 480)
    released_position = cube.data.root_pos_w[0].clone()
    target_clear_arm = target_lift_arm.copy()
    target_clear_arm[1] -= 0.10
    target_clear_arm[2] -= 0.10
    smooth_move(sim, robot, cube, state, arm_ids, target_lift_arm, target_clear_arm, 240, "RETREAT")
    hold(sim, robot, cube, state, 120)
    final_position = cube.data.root_pos_w[0].clone()

    settled_source_np = settled_source_position.detach().cpu().numpy()
    closed_np = closed_position.detach().cpu().numpy()
    lifted_np = lifted_position.detach().cpu().numpy()
    pre_release_np = pre_release_position.detach().cpu().numpy()
    released_np = released_position.detach().cpu().numpy()
    final_np = final_position.detach().cpu().numpy()
    source_to_target_distance = float(np.linalg.norm(target_block_position[:2] - SOURCE_BLOCK_POSITION[:2]))
    lift_height = float(lifted_np[2] - closed_np[2])
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
    release_drift = float(np.linalg.norm(final_np - released_np))
    final_l2_tip_gap = float(
        torch.linalg.vector_norm(
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
        )
    )
    all_states_finite = bool(
        torch.isfinite(robot.data.joint_pos).all().item()
        and torch.isfinite(cube.data.root_state_w).all().item()
    )
    passed = (
        all_states_finite
        and source_to_target_distance > 0.12
        and lift_height > 0.02
        and final_target_xy_error < 0.05
        and final_target_position_error < 0.05
        and release_drift < 0.02
        and float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12
        and final_l2_tip_gap > 0.06
    )
    report = {
        "status": "pass" if passed else "fail",
        "simulation_only": True,
        "expert": (
            "scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"
            if args.initialize_at_grasp
            else "scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"
        ),
        "task": "close, enable gravity, lift, transfer, assisted release onto a platform, and retreat",
        "real_robot_command_sent": False,
        "unassisted_full_task_complete": False,
        "transfer_joint_1_rad": args.transfer_joint_1_rad,
        "collision_bypass_during_approach": args.collision_bypass_during_approach,
        "initialized_at_grasp": args.initialize_at_grasp,
        "development_assistance": {
            "initialized_at_grasp": args.initialize_at_grasp,
            "source_block_gravity_disabled_until_close": True,
            "target_platform_collision_enabled_after_transfer": True,
            "release_separation_assist_m": RELEASE_SEPARATION_ASSIST_M,
            "release_downward_speed_assist_m_s": RELEASE_DOWNWARD_SPEED_M_S,
        },
        "block_mass_kg": BLOCK_MASS_KG,
        "block_size_m": list(BLOCK_SIZE),
        "moving_gripper_gravity_disabled": True,
        "gravity_disabled_body_paths": isolated_paths,
        "source_block_position_m": SOURCE_BLOCK_POSITION.tolist(),
        "target_block_position_m": target_block_position.tolist(),
        "expected_lift_translation_from_fk_m": expected_lift_translation.tolist(),
        "expected_source_lift_block_position_m": expected_source_lift_block_position.tolist(),
        "expected_release_position_before_drop_m": target_release_position.tolist(),
        "source_block_quaternion_wxyz": source_block_quaternion.tolist(),
        "target_block_quaternion_wxyz": target_block_quaternion.tolist(),
        "source_block_temporarily_gravity_disabled": True,
        "gravity_enabled_after_gripper_close": True,
        "target_platform_position_m": target_platform_position.tolist(),
        "target_platform_size_m": list(TARGET_PLATFORM_SIZE),
        "target_platform_collision_enabled_after_transfer": True,
        "release_downward_speed_assist_m_s": RELEASE_DOWNWARD_SPEED_M_S,
        "release_separation_assist_m": RELEASE_SEPARATION_ASSIST_M,
        "cartesian_retreat_distances_m": retreat_distances.tolist(),
        "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
        "settled_source_position_m": settled_source_np.tolist(),
        "closed_position_m": closed_np.tolist(),
        "lifted_position_m": lifted_np.tolist(),
        "pre_release_position_m": pre_release_np.tolist(),
        "released_position_m": released_np.tolist(),
        "final_position_m": final_np.tolist(),
        "source_to_target_xy_distance_m": source_to_target_distance,
        "block_lift_height_m": lift_height,
        "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
        "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
        "closed_l2_tip_gap_m": closed_l2_gap,
        "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
        "final_target_xy_error_m": final_target_xy_error,
        "final_target_position_error_m": final_target_position_error,
        "post_release_drift_m": release_drift,
        "final_l2_tip_gap_m": final_l2_tip_gap,
        "final_gripper_joint_position_rad": robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist(),
        "all_states_finite": all_states_finite,
        "criteria": {
            "source_to_target_xy_distance_m_gt": 0.12,
            "block_lift_height_m_gt": 0.02,
            "final_target_xy_error_m_lt": 0.05,
            "final_target_position_error_m_lt": 0.05,
            "post_release_drift_m_lt": 0.02,
            "final_gripper_joint_position_rad_lt": 0.12,
            "final_l2_tip_gap_m_gt": 0.06,
        },
        "limitation": "The collision pads and scripted waypoints still require physical calibration.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


try:
    exit_code = main()
except BaseException:
    print("PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True)
    traceback.print_exc()
    raise
finally:
    simulation_app.close(skip_cleanup=True)

raise SystemExit(exit_code)
