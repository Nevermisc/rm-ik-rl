#!/usr/bin/env python3
"""Render one external or wrist-like RGB view of the RM65 + 4C2 scene."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--view", choices=("external", "wrist"), required=True)
parser.add_argument("--output-dir", type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import numpy as np  # noqa: E402
import omni.usd  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from pxr import UsdGeom  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg  # noqa: E402
from isaaclab.sensors.camera import Camera, CameraCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import math as math_utils  # noqa: E402


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
GRIPPER_MASTER_JOINT = "tool_gripper_joint"
CUBE_POSITION = (0.45, 0.0, 0.045)


def camera_world_position(prim_path: str, device: str) -> torch.Tensor:
    """Read the authored USD camera transform; CameraData.pos_w is stale on this setup."""

    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path)
    transform = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    return torch.tensor(transform.ExtractTranslation(), dtype=torch.float32, device=device)


def robot_config(usd: Path) -> ArticulationCfg:
    return ArticulationCfg(
        prim_path="/World/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(usd),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=32,
                solver_velocity_iteration_count=4,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(joint_pos={"joint_.*": 0.0, "tool_.*": 0.0}),
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["joint_[1-6]"],
                effort_limit_sim=120.0,
                velocity_limit_sim=1.0,
                stiffness=500.0,
                damping=60.0,
            ),
            "gripper": ImplicitActuatorCfg(
                joint_names_expr=["tool_.*joint.*"],
                effort_limit_sim=50.0,
                velocity_limit_sim=2.0,
                stiffness=200.0,
                damping=20.0,
            ),
        },
    )


def main() -> None:
    usd = args.usd.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"CAPTURE_VIEW_STAGE=CREATE_SIMULATION view={args.view}", flush=True)
    sim = SimulationContext(sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args.device))
    sim_utils.GroundPlaneCfg().func("/World/Ground", sim_utils.GroundPlaneCfg())
    light_cfg = sim_utils.DomeLightCfg(intensity=3000.0, color=(0.85, 0.85, 0.85))
    light_cfg.func("/World/Light", light_cfg)
    table_cfg = sim_utils.CuboidCfg(
        size=(0.70, 0.70, 0.04),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.25, 0.28, 0.32)),
    )
    table_cfg.func("/World/Table", table_cfg, translation=(0.35, 0.0, 0.0))
    cube_cfg = sim_utils.CuboidCfg(
        size=(0.05, 0.05, 0.05),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
    )
    cube_cfg.func("/World/TargetCube", cube_cfg, translation=CUBE_POSITION)

    robot = Articulation(robot_config(usd))
    camera_prim_path = "/World/CaptureCamera"
    camera = Camera(
        CameraCfg(
            prim_path=camera_prim_path,
            update_period=0.0,
            height=480,
            width=640,
            data_types=["rgb"],
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=24.0 if args.view == "external" else 18.0,
                focus_distance=2.0 if args.view == "external" else 1.0,
                horizontal_aperture=20.955,
                clipping_range=(0.01, 10.0),
            ),
        )
    )

    print(f"CAPTURE_VIEW_STAGE=RESET view={args.view}", flush=True)
    sim.reset()
    robot.reset()
    joint_names = list(robot.data.joint_names)
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
    target = robot.data.default_joint_pos.clone()
    target[:, arm_ids] = torch.tensor([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], device=sim.device)
    target[:, gripper_ids] = 0.35
    robot.write_joint_state_to_sim(target, torch.zeros_like(target))
    robot.set_joint_position_target(target)
    robot.write_data_to_sim()
    sim.step(render=False)
    robot.update(sim.get_physics_dt())

    body_names = list(robot.data.body_names)
    tool_body_id = body_names.index("tool_base_link")
    tool_position = robot.data.body_pos_w[0, tool_body_id].clone()
    wrist_local_offset = None
    wrist_local_forward = None
    if args.view == "external":
        eye = torch.tensor([[1.15, 1.15, 0.90]], device=sim.device)
        target_point = torch.tensor([[0.18, 0.0, 0.35]], device=sim.device)
    else:
        tool_quaternion = robot.data.body_quat_w[0, tool_body_id].clone()
        world_offset = torch.tensor([0.0, 0.15, 0.10], device=sim.device)
        eye_position = tool_position + world_offset
        world_forward = torch.nn.functional.normalize(
            torch.tensor(CUBE_POSITION, device=sim.device) - eye_position,
            dim=0,
        )
        # Store the successful initial camera pose in the moving tool frame.
        # A closed-loop environment calls the same transform update each step.
        inverse_tool_quaternion = math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]
        wrist_local_offset = math_utils.quat_apply(
            inverse_tool_quaternion.unsqueeze(0), world_offset.unsqueeze(0)
        )[0]
        wrist_local_forward = math_utils.quat_apply(
            inverse_tool_quaternion.unsqueeze(0), world_forward.unsqueeze(0)
        )[0]
        eye = eye_position.unsqueeze(0)
        target_point = (eye_position + world_forward).unsqueeze(0)
    camera.set_world_poses_from_view(eye, target_point)

    print(f"CAPTURE_VIEW_STAGE=RENDER view={args.view}", flush=True)
    for _ in range(2):
        robot.write_data_to_sim()
        sim.step(render=True)
        robot.update(sim.get_physics_dt())
        camera.update(sim.get_physics_dt())

    rgb = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    image_path = output_dir / f"{args.view}_rgb.png"
    Image.fromarray(rgb).save(image_path)
    red_pixels = (rgb[..., 0] > 120) & (rgb[..., 0] > 1.25 * rgb[..., 1]) & (rgb[..., 0] > 1.25 * rgb[..., 2])
    image_stats = {
        "path": image_path.name,
        "shape": list(rgb.shape),
        "dtype": str(rgb.dtype),
        "min": int(rgb.min()),
        "max": int(rgb.max()),
        "mean": float(rgb.mean()),
        "std": float(rgb.std()),
        "red_target_pixel_count": int(red_pixels.sum()),
    }
    passed = (
        image_stats["shape"] == [480, 640, 3]
        and image_stats["dtype"] == "uint8"
        and image_stats["std"] > 1.0
        and image_stats["red_target_pixel_count"] > 20
    )
    observation_arm_position = robot.data.joint_pos[0, arm_ids].detach().cpu().tolist()
    observation_gripper_position = robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist()
    follow_check = None
    if args.view == "wrist":
        camera_position_1 = camera_world_position(camera_prim_path, sim.device)
        tool_position_1 = robot.data.body_pos_w[0, tool_body_id].clone()
        moved_target = target.clone()
        moved_target[:, arm_ids] += torch.tensor(
            [0.20, -0.10, 0.05, 0.0, 0.0, 0.0], device=sim.device
        )
        robot.write_joint_state_to_sim(moved_target, torch.zeros_like(moved_target))
        robot.set_joint_position_target(moved_target)
        robot.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        moved_tool_quaternion = robot.data.body_quat_w[0, tool_body_id].clone()
        moved_tool_position = robot.data.body_pos_w[0, tool_body_id].clone()
        moved_eye = moved_tool_position + math_utils.quat_apply(
            moved_tool_quaternion.unsqueeze(0), wrist_local_offset.unsqueeze(0)
        )[0]
        moved_forward = math_utils.quat_apply(
            moved_tool_quaternion.unsqueeze(0), wrist_local_forward.unsqueeze(0)
        )[0]
        camera.set_world_poses_from_view(
            moved_eye.unsqueeze(0), (moved_eye + moved_forward).unsqueeze(0)
        )
        sim.step(render=True)
        robot.update(sim.get_physics_dt())
        camera.update(sim.get_physics_dt())
        camera_position_2 = camera_world_position(camera_prim_path, sim.device)
        tool_position_2 = robot.data.body_pos_w[0, tool_body_id].clone()
        moved_rgb = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
        if moved_rgb.dtype != np.uint8:
            moved_rgb = np.clip(moved_rgb, 0, 255).astype(np.uint8)
        moved_red_pixels = (
            (moved_rgb[..., 0] > 120)
            & (moved_rgb[..., 0] > 1.25 * moved_rgb[..., 1])
            & (moved_rgb[..., 0] > 1.25 * moved_rgb[..., 2])
        )
        first_offset_m = float(torch.linalg.vector_norm(camera_position_1 - tool_position_1))
        second_offset_m = float(torch.linalg.vector_norm(camera_position_2 - tool_position_2))
        camera_motion_m = float(torch.linalg.vector_norm(camera_position_2 - camera_position_1))
        offset_change_m = abs(second_offset_m - first_offset_m)
        first_command_error_m = float(torch.linalg.vector_norm(camera_position_1 - eye[0]))
        second_command_error_m = float(torch.linalg.vector_norm(camera_position_2 - moved_eye))
        follow_check = {
            "camera_prim_path": camera_prim_path,
            "follow_mode": "tool-frame pose updated every simulation step",
            "camera_motion_m": camera_motion_m,
            "first_camera_to_tool_distance_m": first_offset_m,
            "second_camera_to_tool_distance_m": second_offset_m,
            "camera_to_tool_distance_change_m": offset_change_m,
            "first_pose_command_error_m": first_command_error_m,
            "second_pose_command_error_m": second_command_error_m,
            "moved_view_red_target_pixel_count": int(moved_red_pixels.sum()),
            "passed": (
                camera_motion_m > 0.01
                and offset_change_m < 0.002
                and first_command_error_m < 0.002
                and second_command_error_m < 0.002
            ),
        }
        passed = passed and follow_check["passed"]

    report = {
        "status": "pass" if passed else "fail",
        "view": args.view,
        "usd": str(usd),
        "joint_names": joint_names,
        "body_names": body_names,
        "rm65_joint_position_rad": observation_arm_position,
        "gripper_joint_position_rad": observation_gripper_position,
        "tool_position_world_m": tool_position.detach().cpu().tolist(),
        "camera_eye_world_m": eye[0].detach().cpu().tolist(),
        "camera_target_world_m": target_point[0].detach().cpu().tolist(),
        "camera_parented_to_tool": False,
        "camera_follows_tool_pose": args.view == "wrist",
        "camera_follow_check": follow_check,
        "image": image_stats,
    }
    report_path = output_dir / f"{args.view}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"CAPTURE_SINGLE_VIEW_{args.view.upper()}={'PASS' if passed else 'FAIL'}", flush=True)


try:
    main()
finally:
    simulation_app.close(skip_cleanup=True)
