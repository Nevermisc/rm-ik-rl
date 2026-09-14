#!/usr/bin/env python3
"""Load the combined robot in Isaac Lab and run a bounded position-control smoke test."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--steps", type=int, default=240)
parser.add_argument("--settle-steps", type=int, default=120)
parser.add_argument("--enable-gravity", action="store_true")
parser.add_argument(
    "--gripper-control-mode",
    choices=("software-coupled", "master-only"),
    default="software-coupled",
)
parser.add_argument("--gripper-effort", type=float, default=50.0)
parser.add_argument("--gripper-stiffness", type=float, default=200.0)
parser.add_argument("--gripper-damping", type=float, default=20.0)
parser.add_argument("--disable-gripper-gravity", action="store_true")
parser.add_argument("--disable-distal-gripper-gravity", action="store_true")
parser.add_argument("--disable-moving-gripper-gravity", action="store_true")
parser.add_argument("--no-ground", action="store_true")
parser.add_argument("--robot-height", type=float, default=0.0)
parser.add_argument("--physics-dt", type=float, default=1.0 / 120.0)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
from pxr import PhysxSchema, UsdPhysics  # noqa: E402


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
GRIPPER_MASTER_JOINT = "tool_gripper_joint"
GRIPPER_FOLLOWER_JOINTS = [
    "tool_l_1_joint",
    "tool_r_3_joint",
    "tool_l_3_joint",
    "tool_l_2_joint",
    "tool_r_2_joint",
]


def main() -> None:
    usd = args.usd.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not usd.is_file():
        raise FileNotFoundError(usd)
    gravity_isolation_options = (
        args.disable_gripper_gravity,
        args.disable_distal_gripper_gravity,
        args.disable_moving_gripper_gravity,
    )
    if sum(gravity_isolation_options) > 1:
        raise ValueError("choose only one gripper gravity isolation scope")

    if args.physics_dt <= 0:
        raise ValueError("physics-dt must be positive")
    sim = SimulationContext(sim_utils.SimulationCfg(dt=args.physics_dt, device=args.device))
    if not args.no_ground:
        sim_utils.GroundPlaneCfg().func("/World/Ground", sim_utils.GroundPlaneCfg())
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
    light_cfg.func("/World/Light", light_cfg)

    actuators = {
        "arm": ImplicitActuatorCfg(
            joint_names_expr=["joint_[1-6]"],
            effort_limit_sim=300.0,
            velocity_limit_sim=1.0,
            stiffness=1000.0,
            damping=100.0,
        ),
    }
    if args.gripper_control_mode == "software-coupled":
        actuators["gripper"] = ImplicitActuatorCfg(
            joint_names_expr=["tool_.*"],
            effort_limit_sim=args.gripper_effort,
            velocity_limit_sim=2.0,
            stiffness=args.gripper_stiffness,
            damping=args.gripper_damping,
        )
    else:
        actuators["gripper_master"] = ImplicitActuatorCfg(
            joint_names_expr=[GRIPPER_MASTER_JOINT],
            effort_limit_sim=args.gripper_effort,
            velocity_limit_sim=2.0,
            stiffness=args.gripper_stiffness,
            damping=args.gripper_damping,
        )

    robot_cfg = ArticulationCfg(
        prim_path="/World/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(usd),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=not args.enable_gravity,
                max_depenetration_velocity=3.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=32,
                solver_velocity_iteration_count=4,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, args.robot_height),
            joint_pos={"joint_.*": 0.0, "tool_.*": 0.0},
        ),
        actuators=actuators,
    )
    robot = Articulation(robot_cfg)
    gravity_disabled_body_paths: list[str] = []
    distal_paths = {
        "/World/Robot/tool_r_2",
        "/World/Robot/tool_l_2",
        "/World/Robot/tool_r_3",
        "/World/Robot/tool_l_3",
    }
    moving_paths = distal_paths | {
        "/World/Robot/tool_r_1",
        "/World/Robot/tool_l_1",
    }
    if any(gravity_isolation_options):
        for prim in get_current_stage().Traverse():
            path = str(prim.GetPath())
            selected = (
                args.disable_gripper_gravity and path.startswith("/World/Robot/tool_")
            ) or (args.disable_distal_gripper_gravity and path in distal_paths) or (
                args.disable_moving_gripper_gravity and path in moving_paths
            )
            if selected and prim.HasAPI(UsdPhysics.RigidBodyAPI):
                PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
                gravity_disabled_body_paths.append(path)
    sim.reset()
    robot.reset()
    sim_dt = sim.get_physics_dt()

    joint_names = list(robot.data.joint_names)
    missing = sorted(set(ARM_JOINTS + [GRIPPER_MASTER_JOINT]) - set(joint_names))
    if missing:
        raise RuntimeError(f"missing expected joints: {missing}; found {joint_names}")
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
    gripper_master_id = joint_names.index(GRIPPER_MASTER_JOINT)
    gripper_follower_ids = [index for index in gripper_ids if index != gripper_master_id]
    if not gripper_ids:
        raise RuntimeError(f"no 4C2 gripper DOF found; joints={joint_names}")
    initial = robot.data.joint_pos.clone()
    max_abs_error = torch.zeros_like(initial)
    peak_abs_movement = torch.zeros_like(initial)
    all_finite = True

    total_steps = args.steps + args.settle_steps
    for step in range(total_steps):
        target = initial.clone()
        if step < args.steps:
            phase = step / max(1, args.steps - 1)
            arm_delta = 0.08 * math.sin(math.pi * phase)
            grip_target = 0.55 * math.sin(math.pi * phase)
            target[:, arm_ids] += arm_delta
            if args.gripper_control_mode == "software-coupled":
                target[:, gripper_ids] = grip_target
            else:
                target[:, gripper_master_id] = grip_target
        robot.set_joint_position_target(target)
        robot.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim_dt)
        error = (target - robot.data.joint_pos).abs()
        max_abs_error = torch.maximum(max_abs_error, error)
        peak_abs_movement = torch.maximum(peak_abs_movement, (robot.data.joint_pos - initial).abs())
        all_finite = all_finite and bool(torch.isfinite(robot.data.joint_pos).all().item())

    final_pos = robot.data.joint_pos[0].detach().cpu()
    initial_pos = initial[0].detach().cpu()
    return_error = (final_pos - initial_pos).abs()
    max_arm_return_error = float(return_error[arm_ids].max().item())
    max_gripper_return_error = float(return_error[gripper_ids].max().item())
    min_arm_peak_movement = float(peak_abs_movement[0, arm_ids].min().item())
    evaluated_gripper_ids = gripper_ids if args.gripper_control_mode == "software-coupled" else [gripper_master_id]
    min_gripper_peak_movement = float(peak_abs_movement[0, evaluated_gripper_ids].min().item())
    min_follower_peak_movement = float(peak_abs_movement[0, gripper_follower_ids].min().item())
    passed = (
        all_finite
        and max_arm_return_error < 0.03
        and max_gripper_return_error < 0.08
        and min_arm_peak_movement > 0.03
        and min_gripper_peak_movement > 0.10
    )
    report = {
        "status": "pass" if passed else "fail",
        "usd": str(usd),
        "motion_steps": args.steps,
        "settle_steps": args.settle_steps,
        "physics_dt_seconds": args.physics_dt,
        "gravity_enabled": args.enable_gravity,
        "ground_enabled": not args.no_ground,
        "robot_height_m": args.robot_height,
        "gripper_gravity_disabled": args.disable_gripper_gravity,
        "distal_gripper_gravity_disabled": args.disable_distal_gripper_gravity,
        "moving_gripper_gravity_disabled": args.disable_moving_gripper_gravity,
        "gravity_disabled_body_paths": gravity_disabled_body_paths,
        "actuator_profile": {
            "arm": {"effort_limit": 300.0, "stiffness": 1000.0, "damping": 100.0},
            "gripper": {
                "effort_limit": args.gripper_effort,
                "stiffness": args.gripper_stiffness,
                "damping": args.gripper_damping,
            },
        },
        "actuator_joint_names": {
            name: list(actuator.joint_names) for name, actuator in robot.actuators.items()
        },
        "gripper_control_mode": args.gripper_control_mode,
        "gripper_master_joint": GRIPPER_MASTER_JOINT,
        "gripper_follower_joints": [joint_names[index] for index in gripper_follower_ids],
        "mimic_followers_responded_to_master_only": (
            min_follower_peak_movement > 0.10 if args.gripper_control_mode == "master-only" else None
        ),
        "min_follower_peak_movement_rad": min_follower_peak_movement,
        "joint_names": joint_names,
        "dof_count": len(joint_names),
        "all_joint_positions_finite": all_finite,
        "criteria": {
            "max_arm_return_error_rad_lt": 0.03,
            "max_gripper_return_error_rad_lt": 0.08,
            "min_arm_peak_movement_rad_gt": 0.03,
            "min_gripper_peak_movement_rad_gt": 0.10,
        },
        "max_arm_return_error_rad": max_arm_return_error,
        "max_gripper_return_error_rad": max_gripper_return_error,
        "min_arm_peak_movement_rad": min_arm_peak_movement,
        "min_gripper_peak_movement_rad": min_gripper_peak_movement,
        "max_abs_tracking_error_rad": {name: float(max_abs_error[0, i].item()) for i, name in enumerate(joint_names)},
        "peak_abs_movement_rad": {name: float(peak_abs_movement[0, i].item()) for i, name in enumerate(joint_names)},
        "final_return_error_rad": {name: float(return_error[i].item()) for i, name in enumerate(joint_names)},
        "final_joint_position_rad": {name: float(final_pos[i].item()) for i, name in enumerate(joint_names)},
        "final_computed_torque": {
            name: float(robot.data.computed_torque[0, i].item()) for i, name in enumerate(joint_names)
        },
        "final_applied_torque": {
            name: float(robot.data.applied_torque[0, i].item()) for i, name in enumerate(joint_names)
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


try:
    main()
finally:
    simulation_app.close(skip_cleanup=True)
