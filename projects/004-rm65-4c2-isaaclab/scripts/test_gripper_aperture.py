#!/usr/bin/env python3
"""Measure how software-coupled 4C2 joint targets change finger geometry."""

from __future__ import annotations

import argparse
import json
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
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import math as math_utils  # noqa: E402


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
GRIPPER_SAMPLES_RAD = [0.0, 0.25, 0.55, 0.85]
BODY_PAIRS = [("tool_l_3", "tool_r_3"), ("tool_l_2", "tool_r_2")]
TIP_LOCAL_POINTS = {
    "tool_r_2": (0.04368, -0.00645, 0.01250),
    "tool_l_2": (0.04368, 0.00645, 0.01257),
    "tool_r_3": (0.02850, 0.00720, 0.00900),
    "tool_l_3": (0.02850, -0.00720, 0.00900),
}


def main() -> int:
    usd = args.usd.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not usd.is_file():
        raise FileNotFoundError(usd)

    sim = SimulationContext(sim_utils.SimulationCfg(dt=1.0 / 120.0, device=args.device))
    robot = Articulation(
        ArticulationCfg(
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
                    effort_limit_sim=300.0,
                    velocity_limit_sim=1.0,
                    stiffness=1000.0,
                    damping=100.0,
                ),
                "gripper": ImplicitActuatorCfg(
                    joint_names_expr=["tool_.*"],
                    effort_limit_sim=50.0,
                    velocity_limit_sim=2.0,
                    stiffness=200.0,
                    damping=20.0,
                ),
            },
        )
    )
    sim.reset()
    robot.reset()
    joint_names = list(robot.data.joint_names)
    body_names = list(robot.data.body_names)
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
    pair_ids = [(body_names.index(left), body_names.index(right)) for left, right in BODY_PAIRS]
    base_state = robot.data.default_joint_pos.clone()
    base_state[:, arm_ids] = torch.tensor(
        [0.0, -0.55, 1.05, 0.0, 0.65, 0.0], device=sim.device
    )
    samples = []

    for gripper_target in GRIPPER_SAMPLES_RAD:
        state = base_state.clone()
        state[:, gripper_ids] = gripper_target
        robot.write_joint_state_to_sim(state, torch.zeros_like(state))
        robot.set_joint_position_target(state)
        robot.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        positions = robot.data.body_pos_w[0]
        orientations = robot.data.body_quat_w[0]
        distances = {}
        for (left_name, right_name), (left_id, right_id) in zip(BODY_PAIRS, pair_ids, strict=True):
            left_local = torch.tensor(TIP_LOCAL_POINTS[left_name], device=sim.device).unsqueeze(0)
            right_local = torch.tensor(TIP_LOCAL_POINTS[right_name], device=sim.device).unsqueeze(0)
            left_tip = positions[left_id] + math_utils.quat_apply(
                orientations[left_id].unsqueeze(0), left_local
            )[0]
            right_tip = positions[right_id] + math_utils.quat_apply(
                orientations[right_id].unsqueeze(0), right_local
            )[0]
            delta = left_tip - right_tip
            distances[f"{left_name}_to_{right_name}"] = {
                "euclidean_m": float(torch.linalg.vector_norm(delta)),
                "absolute_xyz_m": torch.abs(delta).detach().cpu().tolist(),
                "left_tip_world_m": left_tip.detach().cpu().tolist(),
                "right_tip_world_m": right_tip.detach().cpu().tolist(),
            }
        samples.append({"joint_target_rad": gripper_target, "pair_distances": distances})

    pair_trends = {}
    changed_enough = True
    for left_name, right_name in BODY_PAIRS:
        key = f"{left_name}_to_{right_name}"
        values = np.array([sample["pair_distances"][key]["euclidean_m"] for sample in samples])
        deltas = np.diff(values)
        monotonic_increasing = bool(np.all(deltas > 0))
        monotonic_decreasing = bool(np.all(deltas < 0))
        total_change = float(values[-1] - values[0])
        changed_enough = changed_enough and abs(total_change) > 0.005
        pair_trends[key] = {
            "distance_m": values.tolist(),
            "total_change_m": total_change,
            "monotonic": monotonic_increasing or monotonic_decreasing,
            "direction": "increasing" if monotonic_increasing else "decreasing" if monotonic_decreasing else "mixed",
        }

    all_monotonic = all(item["monotonic"] for item in pair_trends.values())
    finite = all(np.isfinite(item["distance_m"]).all() for item in pair_trends.values())
    passed = all_monotonic and changed_enough and finite
    report = {
        "status": "pass" if passed else "fail",
        "simulation_only": True,
        "control_mode": "one scalar copied to all six movable 4C2 joints",
        "joint_names": joint_names,
        "body_names": body_names,
        "gripper_joint_ids": gripper_ids,
        "tip_local_points_m": TIP_LOCAL_POINTS,
        "samples": samples,
        "pair_trends": pair_trends,
        "all_pair_distances_monotonic": all_monotonic,
        "all_values_finite": finite,
        "minimum_required_total_distance_change_m": 0.005,
        "note": "Body-origin distances verify geometric motion, not calibrated fingertip aperture or grasp contact.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"GRIPPER_APERTURE_TEST={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


try:
    exit_code = main()
finally:
    simulation_app.close(skip_cleanup=True)

raise SystemExit(exit_code)
