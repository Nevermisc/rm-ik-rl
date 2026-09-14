#!/usr/bin/env python3
"""Render a close-up of the 4C2 gripper and its contact-test block."""

from __future__ import annotations

import argparse
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg  # noqa: E402
from isaaclab.sensors.camera import Camera, CameraCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402


def main() -> None:
    usd = args.usd.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not usd.is_file():
        raise FileNotFoundError(usd)
    output.parent.mkdir(parents=True, exist_ok=True)

    sim = SimulationContext(sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args.device))
    light_cfg = sim_utils.DomeLightCfg(intensity=3500.0, color=(0.9, 0.9, 0.9))
    light_cfg.func("/World/Light", light_cfg)
    block_center = (-0.22128649, -0.00000383, 0.75670463)
    block_cfg = sim_utils.CuboidCfg(
        size=(0.060, 0.040, 0.025),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
    )
    block_cfg.func(
        "/World/ContactBlock",
        block_cfg,
        translation=block_center,
        orientation=(-0.20872162, -0.00000211, 0.97797507, 0.00002437),
    )
    robot = Articulation(
        ArticulationCfg(
            prim_path="/World/Robot",
            spawn=sim_utils.UsdFileCfg(
                usd_path=str(usd),
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True),
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(enabled_self_collisions=False),
            ),
            init_state=ArticulationCfg.InitialStateCfg(joint_pos={"joint_.*": 0.0, "tool_.*": 0.0}),
            actuators={
                "arm": ImplicitActuatorCfg(
                    joint_names_expr=["joint_[1-6]"], effort_limit_sim=300.0, stiffness=1000.0, damping=100.0
                ),
                "gripper": ImplicitActuatorCfg(
                    joint_names_expr=["tool_.*"], effort_limit_sim=50.0, stiffness=200.0, damping=20.0
                ),
            },
        )
    )
    camera = Camera(
        CameraCfg(
            prim_path="/World/DiagnosticCamera",
            update_period=0.0,
            height=600,
            width=800,
            data_types=["rgb"],
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=35.0,
                focus_distance=0.5,
                horizontal_aperture=20.955,
                clipping_range=(0.01, 3.0),
            ),
        )
    )
    sim.reset()
    robot.reset()
    joint_names = list(robot.data.joint_names)
    arm_ids = [joint_names.index(f"joint_{index}") for index in range(1, 7)]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
    state = robot.data.default_joint_pos.clone()
    state[:, arm_ids] = torch.tensor([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], device=sim.device)
    state[:, gripper_ids] = 0.65
    robot.write_joint_state_to_sim(state, torch.zeros_like(state))
    robot.set_joint_position_target(state)
    robot.write_data_to_sim()
    sim.step(render=False)
    robot.update(sim.get_physics_dt())

    eye = torch.tensor([[-0.03, 0.24, 0.88]], device=sim.device)
    target = torch.tensor([block_center], device=sim.device)
    camera.set_world_poses_from_view(eye, target)
    for _ in range(3):
        robot.write_data_to_sim()
        sim.step(render=True)
        robot.update(sim.get_physics_dt())
        camera.update(sim.get_physics_dt())
    rgb = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(output)
    print(f"GRIPPER_CLOSE_DIAGNOSTIC_IMAGE={output}", flush=True)


try:
    main()
finally:
    simulation_app.close(skip_cleanup=True)
