#!/usr/bin/env python3
"""Check a static 4C2 close; optionally reproduce the unstable transport path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--attempt-lift", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import numpy as np  # noqa: E402
import torch  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402
from isaaclab.sensors import ContactSensor, ContactSensorCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import math as math_utils  # noqa: E402
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
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
TIP_LOCAL_POINTS = {
    "tool_r_2": (0.04368, -0.00645, 0.01250),
    "tool_l_2": (0.04368, 0.00645, 0.01257),
    "tool_r_3": (0.02850, 0.00720, 0.00900),
    "tool_l_3": (0.02850, -0.00720, 0.00900),
}


def tip_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
    body_id = list(robot.data.body_names).index(body_name)
    local = torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
    )[0]


def step_simulation(
    sim: SimulationContext,
    robot: Articulation,
    cube: RigidObject,
    contact_sensors: dict[str, ContactSensor],
    target: torch.Tensor,
    steps: int,
) -> None:
    for _ in range(steps):
        robot.set_joint_position_target(target)
        robot.write_data_to_sim()
        cube.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        cube.update(sim.get_physics_dt())
        for contact_sensor in contact_sensors.values():
            contact_sensor.update(sim.get_physics_dt())


def main() -> int:
    usd = args.usd.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not usd.is_file():
        raise FileNotFoundError(usd)

    sim = SimulationContext(sim_utils.SimulationCfg(dt=1.0 / 240.0, device=args.device))
    print("CONTACT_STAGE=SIMULATION_CREATED", flush=True)
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
    light_cfg.func("/World/Light", light_cfg)
    print("CONTACT_STAGE=NO_SUPPORT_SURFACE", flush=True)

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
    print("CONTACT_STAGE=ROBOT_CREATED", flush=True)
    cube = RigidObject(
        RigidObjectCfg(
            prim_path="/World/Cube",
            spawn=sim_utils.CuboidCfg(
                size=(0.025, 0.060, 0.025),
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=True,
                    solver_position_iteration_count=32,
                    solver_velocity_iteration_count=4,
                    max_depenetration_velocity=1.0,
                ),
                mass_props=sim_utils.MassPropertiesCfg(mass=0.03),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.5, dynamic_friction=1.2, restitution=0.0
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(pos=(-0.2225, 0.0, 0.7575)),
        )
    )
    print("CONTACT_STAGE=CUBE_CREATED", flush=True)
    contact_sensors = {
        body_path.rsplit("/", 1)[-1]: ContactSensor(
            ContactSensorCfg(
                prim_path=body_path,
                update_period=0.0,
                history_length=400,
                filter_prim_paths_expr=["/World/Cube"],
            )
        )
        for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)
    }
    isolated_paths = []
    for prim in get_current_stage().Traverse():
        path = str(prim.GetPath())
        if path in MOVING_GRIPPER_BODY_PATHS and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
            isolated_paths.append(path)

    print("CONTACT_STAGE=BEFORE_RESET", flush=True)
    sim.reset()
    print("CONTACT_STAGE=AFTER_RESET", flush=True)
    robot.reset()
    cube.reset()
    for contact_sensor in contact_sensors.values():
        contact_sensor.reset()
    print("CONTACT_STAGE=ASSETS_RESET", flush=True)
    joint_names = list(robot.data.joint_names)
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
    open_state = robot.data.default_joint_pos.clone()
    start_arm_q = torch.tensor([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], device=sim.device)
    open_state[:, arm_ids] = start_arm_q
    open_state[:, gripper_ids] = 0.0
    robot.write_joint_state_to_sim(open_state, torch.zeros_like(open_state))
    step_simulation(sim, robot, cube, contact_sensors, open_state, 1)
    print("CONTACT_STAGE=OPEN_STATE", flush=True)

    tool_body_id = list(robot.data.body_names).index("tool_base_link")
    start_arm_np = start_arm_q.detach().cpu().numpy().astype(np.float64)
    # Selected offline from the RM65 URDF: decreasing joints 2 and 3 by
    # 0.18 rad raises link_6 by 0.0387 m from the test pose.
    lift_q = start_arm_np.copy()
    lift_q[1] -= 0.18
    lift_q[2] -= 0.18
    expected_lift_height = 0.038703798585405735
    print("CONTACT_STAGE=LIFT_SELECTED", flush=True)

    tip_midpoints = []
    for left_name, right_name in (("tool_l_2", "tool_r_2"), ("tool_l_3", "tool_r_3")):
        tip_midpoints.append(
            (tip_world_position(robot, left_name) + tip_world_position(robot, right_name)) / 2.0
        )
    open_midpoint = torch.stack(tip_midpoints).mean(dim=0)
    tool_position_before_close = robot.data.body_pos_w[0, tool_body_id].clone()
    outward_direction = torch.nn.functional.normalize(open_midpoint - tool_position_before_close, dim=0)
    contact_block_center = open_midpoint - 0.025 * outward_direction
    cube_pose = cube.data.default_root_state[:, :7].clone()
    cube_pose[:, :3] = contact_block_center
    cube_pose[:, 3:7] = torch.tensor([1.0, 0.0, 0.0, 0.0], device=sim.device)
    cube.write_root_pose_to_sim(cube_pose)
    cube.write_root_velocity_to_sim(torch.zeros((1, 6), device=sim.device))
    step_simulation(sim, robot, cube, contact_sensors, open_state, 60)
    print("CONTACT_STAGE=CUBE_SETTLED", flush=True)
    initial_cube_position = cube.data.root_pos_w[0].clone()
    initial_tool_position = robot.data.body_pos_w[0, tool_body_id].clone()
    initial_cube_to_tool = initial_cube_position - initial_tool_position

    close_state = open_state.clone()
    close_target_rad = 0.55
    for step in range(180):
        progress = (step + 1) / 180
        close_state[:, gripper_ids] = close_target_rad * (3 * progress**2 - 2 * progress**3)
        step_simulation(sim, robot, cube, contact_sensors, close_state, 1)
    step_simulation(sim, robot, cube, contact_sensors, close_state, 120)
    print("CONTACT_STAGE=GRIPPER_CLOSED", flush=True)
    closed_cube_position = cube.data.root_pos_w[0].clone()
    closed_gripper_position = robot.data.joint_pos[0, gripper_ids].clone()
    closed_l2_gap = float(
        torch.linalg.vector_norm(
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
        )
    )
    closed_l3_gap = float(
        torch.linalg.vector_norm(
            tip_world_position(robot, "tool_l_3") - tip_world_position(robot, "tool_r_3")
        )
    )
    close_cube_displacement = float(torch.linalg.vector_norm(closed_cube_position - initial_cube_position))
    contact_force_by_body_n = {}
    net_contact_force_by_body_n = {}
    for body_name, contact_sensor in contact_sensors.items():
        filtered_forces = contact_sensor.data.force_matrix_w_history
        contact_force_by_body_n[body_name] = (
            0.0
            if filtered_forces is None
            else float(torch.linalg.vector_norm(filtered_forces, dim=-1).max())
        )
        net_forces = contact_sensor.data.net_forces_w_history
        net_contact_force_by_body_n[body_name] = (
            0.0
            if net_forces is None
            else float(torch.linalg.vector_norm(net_forces, dim=-1).max())
        )
    maximum_cube_contact_force_n = max(contact_force_by_body_n.values())
    contact_confirmed = maximum_cube_contact_force_n > 0.05
    close_state_finite = bool(
        torch.isfinite(cube.data.root_state_w).all().item()
        and torch.isfinite(robot.data.joint_pos).all().item()
    )
    close_passed = (
        close_state_finite
        and float(closed_gripper_position.min()) > 0.10
        and closed_l2_gap < 0.065
        and closed_l3_gap < 0.085
    )
    if not args.attempt_lift:
        report = {
            "status": "pass" if close_passed else "fail",
            "simulation_only": True,
            "task": "stability check while closing the software-coupled 4C2 around a floating 25 x 60 x 25 mm contact block",
            "contact_block_size_m": [0.025, 0.060, 0.025],
            "contact_block_gravity_disabled": True,
            "support_surface_present": False,
            "lift_attempted": False,
            "contact_confirmed": contact_confirmed,
            "maximum_cube_contact_force_n": maximum_cube_contact_force_n,
            "cube_contact_force_by_gripper_body_n": contact_force_by_body_n,
            "net_contact_force_by_gripper_body_n": net_contact_force_by_body_n,
            "moving_gripper_gravity_disabled": True,
            "gravity_disabled_body_paths": isolated_paths,
            "gripper_close_target_rad": close_target_rad,
            "open_fingertip_midpoint_m": open_midpoint.detach().cpu().tolist(),
            "contact_block_center_m": contact_block_center.detach().cpu().tolist(),
            "contact_block_inward_offset_m": 0.025,
            "closed_gripper_joint_position_rad": closed_gripper_position.detach().cpu().tolist(),
            "closed_l2_tip_gap_m": closed_l2_gap,
            "closed_l3_tip_gap_m": closed_l3_gap,
            "cube_displacement_during_close_m": close_cube_displacement,
            "all_states_finite": close_state_finite,
            "warning": (
                "Finite closing is verified and contact_confirmed is derived from a filtered ContactSensor. "
                "The experimental --attempt-lift path currently causes a native PhysX exit."
            ),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2), flush=True)
        print(f"GRIPPER_CLOSE_STABILITY={'PASS' if close_passed else 'FAIL'}", flush=True)
        return 0 if close_passed else 1

    lifted_state = close_state.clone()
    for step in range(240):
        progress = (step + 1) / 240
        smooth = 3 * progress**2 - 2 * progress**3
        command = start_arm_np + smooth * (lift_q - start_arm_np)
        lifted_state[:, arm_ids] = torch.tensor(command, device=sim.device)
        step_simulation(sim, robot, cube, contact_sensors, lifted_state, 1)
    step_simulation(sim, robot, cube, contact_sensors, lifted_state, 120)
    print("CONTACT_STAGE=LIFT_COMPLETE", flush=True)

    final_cube_position = cube.data.root_pos_w[0].clone()
    final_tool_position = robot.data.body_pos_w[0, tool_body_id].clone()
    final_cube_to_tool = final_cube_position - final_tool_position
    cube_lift_m = float(final_cube_position[2] - closed_cube_position[2])
    tool_lift_m = float(final_tool_position[2] - initial_tool_position[2])
    relative_pose_change_m = float(torch.linalg.vector_norm(final_cube_to_tool - initial_cube_to_tool))
    cube_finite = bool(torch.isfinite(cube.data.root_state_w).all().item())
    passed = (
        cube_finite
        and expected_lift_height > 0.03
        and tool_lift_m > 0.03
        and cube_lift_m > 0.02
        and relative_pose_change_m < 0.04
    )
    report = {
        "status": "pass" if passed else "fail",
        "simulation_only": True,
        "task": "close the software-coupled 4C2 on a floating 25 x 60 x 25 mm contact block and transport",
        "moving_gripper_gravity_disabled": True,
        "gravity_disabled_body_paths": isolated_paths,
        "gripper_close_target_rad": close_target_rad,
        "open_fingertip_midpoint_m": open_midpoint.detach().cpu().tolist(),
        "initial_cube_position_m": initial_cube_position.detach().cpu().tolist(),
        "closed_cube_position_m": closed_cube_position.detach().cpu().tolist(),
        "final_cube_position_m": final_cube_position.detach().cpu().tolist(),
        "selected_lift_joint_position_rad": lift_q.tolist(),
        "urdf_predicted_tool_lift_m": expected_lift_height,
        "actual_tool_lift_m": tool_lift_m,
        "actual_cube_lift_m": cube_lift_m,
        "cube_to_tool_relative_position_change_m": relative_pose_change_m,
        "cube_state_finite": cube_finite,
        "criteria": {
            "urdf_predicted_tool_lift_m_gt": 0.03,
            "actual_tool_lift_m_gt": 0.03,
            "actual_cube_lift_m_gt": 0.02,
            "cube_to_tool_relative_position_change_m_lt": 0.04,
        },
        "warning": "This is a contact-model diagnostic, not a validated grasp benchmark.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"GRIPPER_CONTACT_LIFT={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


try:
    exit_code = main()
finally:
    simulation_app.close(skip_cleanup=True)

raise SystemExit(exit_code)
