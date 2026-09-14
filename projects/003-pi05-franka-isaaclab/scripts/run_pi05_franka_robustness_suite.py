"""π0.5 + Franka 的 DROID Isaac Lab 多场景鲁棒性评测。"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description="π0.5 Franka 多场景鲁棒性评测")
parser.add_argument("--scene", type=int, choices=(1, 2, 3), required=True)
parser.add_argument("--suite", choices=("baseline", "robustness", "audit", "full"), default="full")
parser.add_argument("--output-root", type=Path, default=Path("runs/pi05_franka_suite"))
parser.add_argument("--open-loop-horizon", type=int, default=8)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
args.enable_cameras = True
args.headless = True

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import gymnasium as gym
import imageio.v2 as imageio
import numpy as np
import torch
from openpi_client import image_tools, websocket_client_policy

import sim_evals.environments  # noqa: F401,E402
from isaaclab_tasks.utils import parse_env_cfg


FPS = 15
CAMERA_HEIGHT = 180
CAMERA_WIDTH = 320
STABLE_STEPS = 15
OPEN_GRIPPER_THRESHOLD = 0.25
STABLE_RADIUS_METERS = 0.015


@dataclass(frozen=True)
class Task:
    source: str
    target: str
    instruction: str
    paraphrase: str
    success_xy_m: float
    success_z_min_m: float
    success_z_max_m: float


@dataclass(frozen=True)
class Case:
    name: str
    prompt: str
    source_dx: float = 0.0
    source_dy: float = 0.0
    target_dx: float = 0.0
    target_dy: float = 0.0
    brightness: float = 1.0


TASKS = {
    1: Task(
        source="rubiks_cube",
        target="_24_bowl",
        instruction="put the cube in the bowl",
        paraphrase="pick up the cube and place it inside the red bowl",
        success_xy_m=0.10,
        success_z_min_m=-0.02,
        success_z_max_m=0.16,
    ),
    2: Task(
        source="_10_potted_meat_can",
        target="_25_mug",
        instruction="put the can in the mug",
        paraphrase="pick up the meat can and place it inside the red mug",
        success_xy_m=0.075,
        success_z_min_m=-0.02,
        success_z_max_m=0.20,
    ),
    3: Task(
        source="_11_banana",
        target="small_KLT_visual_collision",
        instruction="put banana in the bin",
        paraphrase="pick up the banana and place it inside the purple bin",
        success_xy_m=0.12,
        success_z_min_m=-0.05,
        success_z_max_m=0.20,
    ),
}


class DroidJointPosClient:
    def __init__(self, open_loop_horizon: int) -> None:
        self.open_loop_horizon = open_loop_horizon
        self.client = websocket_client_policy.WebsocketClientPolicy("localhost", 8000)
        self.reset()

    def reset(self) -> None:
        self.action_index = 0
        self.action_chunk = None

    def infer(self, obs: dict, instruction: str, brightness: float) -> dict:
        policy = obs["policy"]
        external = policy["external_cam"][0].detach().cpu().numpy()
        wrist = policy["wrist_cam"][0].detach().cpu().numpy()
        external = image_tools.resize_with_pad(external, 224, 224)
        wrist = image_tools.resize_with_pad(wrist, 224, 224)
        if brightness != 1.0:
            external = np.clip(external.astype(np.float32) * brightness, 0, 255).astype(np.uint8)
            wrist = np.clip(wrist.astype(np.float32) * brightness, 0, 255).astype(np.uint8)

        replanned = self.action_index == 0 or self.action_index >= self.open_loop_horizon
        inference_seconds = None
        if replanned:
            request = {
                "observation/exterior_image_1_left": external,
                "observation/wrist_image_left": wrist,
                "observation/joint_position": policy["arm_joint_pos"].detach().cpu().numpy(),
                "observation/gripper_position": policy["gripper_pos"].detach().cpu().numpy(),
                "prompt": instruction,
            }
            inference_start = time.perf_counter()
            self.action_chunk = np.asarray(self.client.infer(request)["actions"])
            inference_seconds = time.perf_counter() - inference_start
            self.action_index = 0

        action = np.asarray(self.action_chunk[self.action_index], dtype=np.float32).copy()
        self.action_index += 1
        action[-1] = 1.0 if action[-1] > 0.5 else 0.0
        return {
            "action": action,
            "viz": np.concatenate((external, wrist), axis=1),
            "replanned": replanned,
            "inference_seconds": inference_seconds,
        }


def make_cases(task: Task, suite: str) -> list[Case]:
    baseline = [
        Case("baseline_1", task.instruction),
        Case("baseline_2", task.instruction),
        Case("baseline_3", task.instruction),
    ]
    robustness = [
        Case("source_plus", task.instruction, source_dx=0.035, source_dy=0.020),
        Case("source_minus", task.instruction, source_dx=-0.035, source_dy=-0.020),
        Case("target_shift", task.instruction, target_dx=0.025, target_dy=-0.020),
        Case("paraphrase", task.paraphrase),
        Case("darker_input", task.instruction, brightness=0.75),
        Case("brighter_input", task.instruction, brightness=1.25),
    ]
    if suite == "baseline":
        return baseline
    if suite == "robustness":
        return robustness
    if suite == "audit":
        return [Case("engineering_audit", task.instruction)]
    return baseline + robustness


def xyz(asset) -> np.ndarray:
    return asset.data.root_pos_w[0, :3].detach().cpu().numpy().astype(np.float64)


def shift_asset(asset, dx: float, dy: float) -> None:
    if dx == 0.0 and dy == 0.0:
        return
    state = asset.data.root_state_w.clone()
    pose = state[:, :7].clone()
    pose[:, 0] += dx
    pose[:, 1] += dy
    asset.write_root_pose_to_sim(pose)
    asset.write_root_velocity_to_sim(torch.zeros_like(state[:, 7:]))


def neutral_action(obs: dict, device: str) -> torch.Tensor:
    policy = obs["policy"]
    return torch.cat((policy["arm_joint_pos"], policy["gripper_pos"]), dim=-1).to(device).unsqueeze(0)


def write_video(path: Path, frames: list[np.ndarray]) -> None:
    writer = imageio.get_writer(path, fps=FPS, codec="libx264", quality=7)
    try:
        for frame in frames:
            writer.append_data(frame)
    finally:
        writer.close()


def main() -> None:
    task = TASKS[args.scene]
    cases = make_cases(task, args.suite)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_root / stamp / f"scene_{args.scene}"
    run_dir.mkdir(parents=True, exist_ok=True)

    cfg = parse_env_cfg("DROID", device=args.device, num_envs=1, use_fabric=True)
    cfg.set_scene(args.scene)
    for camera_name in ("external_cam", "external_cam_2", "wrist_cam"):
        camera = getattr(cfg.scene, camera_name)
        camera.height = CAMERA_HEIGHT
        camera.width = CAMERA_WIDTH
    env = gym.make("DROID", cfg=cfg)
    obs, _ = env.reset()
    obs, _ = env.reset()
    client = DroidJointPosClient(args.open_loop_horizon)
    source = env.unwrapped.scene[task.source]
    target = env.unwrapped.scene[task.target]
    robot = env.unwrapped.scene["robot"]
    arm_joint_names = [f"panda_joint{i}" for i in range(1, 8)]
    arm_joint_indices = [robot.data.joint_names.index(name) for name in arm_joint_names]
    arm_limits = robot.data.soft_joint_pos_limits[0, arm_joint_indices].detach().cpu().numpy()
    max_steps = int(env.unwrapped.max_episode_length)
    device = env.unwrapped.device
    summaries: list[dict] = []

    print(f"场景 {args.scene}: {task.instruction}", flush=True)
    print(f"评测用例数: {len(cases)}", flush=True)
    print(f"严格成功条件: 进入目标 + 夹爪实际张开 + 稳定 {STABLE_STEPS} 步", flush=True)
    print(f"结果目录: {run_dir.resolve()}", flush=True)

    with torch.inference_mode():
        for case_index, case in enumerate(cases, start=1):
            obs, _ = env.reset()
            obs, _ = env.reset()
            for _ in range(5):
                obs, _, _, _, _ = env.step(neutral_action(obs, device))
            shift_asset(source, case.source_dx, case.source_dy)
            shift_asset(target, case.target_dx, case.target_dy)
            for _ in range(8):
                obs, _, _, _, _ = env.step(neutral_action(obs, device))
            client.reset()

            initial_source = xyz(source)
            initial_target = xyz(target)
            initial_distance = float(np.linalg.norm(initial_source[:2] - initial_target[:2]))
            frames: list[np.ndarray] = []
            source_positions: list[np.ndarray] = []
            target_positions: list[np.ndarray] = []
            commanded_gripper: list[float] = []
            observed_gripper: list[float] = []
            arm_actions: list[np.ndarray] = []
            arm_observations: list[np.ndarray] = []
            inference_latencies: list[float] = []
            stable_history: list[np.ndarray] = []
            released_inside_steps = 0
            entered_target_while_closed = False
            success = False
            start = time.perf_counter()

            print(
                f"\n用例 {case_index}/{len(cases)} {case.name} | "
                f"初始XY距离={initial_distance:.3f}m | 指令={case.prompt}",
                flush=True,
            )

            for step in range(max_steps):
                ret = client.infer(obs, case.prompt, case.brightness)
                frames.append(np.asarray(ret["viz"], dtype=np.uint8))
                action_np = np.asarray(ret["action"], dtype=np.float32)
                if not np.isfinite(action_np).all():
                    raise RuntimeError(f"π0.5 在第 {step + 1} 步输出 NaN/Inf")
                if ret["replanned"]:
                    inference_latencies.append(float(ret["inference_seconds"]))
                action = torch.as_tensor(action_np, dtype=torch.float32, device=device).unsqueeze(0)
                obs, _, terminated, truncated, _ = env.step(action)
                # Isaac Lab 会在 time-out 时自动 reset；不要把重置后的关节和物体位置
                # 当成当前回合的最后一个样本，否则会制造一个并不存在的巨大跳变。
                if bool(torch.as_tensor(terminated).any()) or bool(torch.as_tensor(truncated).any()):
                    break

                source_pos = xyz(source)
                target_pos = xyz(target)
                source_positions.append(source_pos.copy())
                target_positions.append(target_pos.copy())
                commanded_gripper.append(float(action_np[-1]))
                arm_actions.append(action_np[:7].copy())
                arm_observed = obs["policy"]["arm_joint_pos"].detach().cpu().numpy().astype(np.float32)
                if not np.isfinite(arm_observed).all():
                    raise RuntimeError(f"仿真关节状态在第 {step + 1} 步出现 NaN/Inf")
                arm_observations.append(arm_observed.copy())
                gripper_pos = float(obs["policy"]["gripper_pos"].detach().cpu().numpy()[0])
                observed_gripper.append(gripper_pos)

                xy_distance = float(np.linalg.norm(source_pos[:2] - target_pos[:2]))
                relative_z = float(source_pos[2] - target_pos[2])
                displacement = float(np.linalg.norm(source_pos - initial_source))
                inside = (
                    xy_distance <= task.success_xy_m
                    and task.success_z_min_m <= relative_z <= task.success_z_max_m
                    and displacement >= 0.05
                )
                is_open = gripper_pos <= OPEN_GRIPPER_THRESHOLD
                stable_history.append(source_pos.copy())
                if len(stable_history) > STABLE_STEPS:
                    stable_history.pop(0)
                is_stable = (
                    len(stable_history) == STABLE_STEPS
                    and max(float(np.linalg.norm(p - stable_history[-1])) for p in stable_history)
                    <= STABLE_RADIUS_METERS
                )
                if inside and not is_open:
                    entered_target_while_closed = True
                if inside and is_open and is_stable:
                    released_inside_steps += 1
                else:
                    released_inside_steps = 0

                if step == 0 or (step + 1) % 30 == 0:
                    print(
                        f"  步 {step + 1:3d}: 位移={displacement:.3f}m, "
                        f"目标XY={xy_distance:.3f}m, 指令夹爪={action_np[-1]:.0f}, "
                        f"实际夹爪={gripper_pos:.2f}, 已进目标={inside}",
                        flush=True,
                    )

                if released_inside_steps >= STABLE_STEPS:
                    success = True
                    print("  严格成功：已松爪，物体稳定留在目标中。", flush=True)
                    break
            elapsed = time.perf_counter() - start
            source_array = np.asarray(source_positions)
            target_array = np.asarray(target_positions)
            command_array = np.asarray(commanded_gripper, dtype=np.float32)
            observed_array = np.asarray(observed_gripper, dtype=np.float32)
            arm_action_array = np.asarray(arm_actions, dtype=np.float32)
            arm_observation_array = np.asarray(arm_observations, dtype=np.float32)
            latency_array = np.asarray(inference_latencies, dtype=np.float64)
            final_source = source_array[-1]
            final_target = target_array[-1]
            final_xy = float(np.linalg.norm(final_source[:2] - final_target[:2]))
            displacement = float(np.linalg.norm(final_source - initial_source))

            case_dir = run_dir / f"{case_index:02d}_{case.name}"
            case_dir.mkdir(parents=True, exist_ok=True)
            write_video(case_dir / "policy_views.mp4", frames)
            imageio.imwrite(case_dir / "final_policy_view.png", frames[-1])
            imageio.imwrite(
                case_dir / "final_external_camera.png",
                obs["policy"]["external_cam"][0].detach().cpu().numpy(),
            )
            imageio.imwrite(
                case_dir / "final_wrist_camera.png",
                obs["policy"]["wrist_cam"][0].detach().cpu().numpy(),
            )
            np.savez_compressed(
                case_dir / "trajectory.npz",
                source_position=source_array,
                target_position=target_array,
                gripper_command=command_array,
                gripper_observed=observed_array,
                arm_action=arm_action_array,
                arm_observed=arm_observation_array,
                inference_latency_seconds=latency_array,
            )
            command_jump = (
                float(np.max(np.abs(np.diff(arm_action_array, axis=0))))
                if len(arm_action_array) > 1
                else 0.0
            )
            observed_jump = (
                float(np.max(np.abs(np.diff(arm_observation_array, axis=0))))
                if len(arm_observation_array) > 1
                else 0.0
            )
            lower_margin = arm_observation_array - arm_limits[:, 0]
            upper_margin = arm_limits[:, 1] - arm_observation_array
            min_limit_margin = float(np.min(np.minimum(lower_margin, upper_margin)))
            summary = {
                "scene": args.scene,
                "case": asdict(case),
                "success": success,
                "steps": len(source_positions),
                "elapsed_seconds": round(elapsed, 3),
                "entered_target_while_closed": entered_target_while_closed,
                "initial_source_xyz": initial_source.tolist(),
                "initial_target_xyz": initial_target.tolist(),
                "final_source_xyz": final_source.tolist(),
                "final_target_xyz": final_target.tolist(),
                "source_displacement_m": displacement,
                "final_source_target_xy_m": final_xy,
                "final_gripper_observed": float(observed_array[-1]),
                "safety_and_performance": {
                    "action_all_finite": bool(np.isfinite(arm_action_array).all()),
                    "observation_all_finite": bool(np.isfinite(arm_observation_array).all()),
                    "minimum_observed_joint_limit_margin_rad": min_limit_margin,
                    "maximum_command_step_jump_rad": command_jump,
                    "maximum_observed_joint_step_jump_rad": observed_jump,
                    "replan_count": int(len(latency_array)),
                    "inference_latency_median_seconds": float(np.median(latency_array)),
                    "inference_latency_p95_seconds": float(np.percentile(latency_array, 95)),
                    "inference_latency_max_seconds": float(np.max(latency_array)),
                },
            }
            (case_dir / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            summaries.append(summary)
            print(
                f"用例结束: success={success}, 步数={len(source_positions)}, "
                f"最终XY={final_xy:.3f}m, 最终实际夹爪={observed_array[-1]:.2f}, "
                f"耗时={elapsed:.1f}s",
                flush=True,
            )

    report = {
        "policy": "pi05_droid_jointpos_polaris",
        "checkpoint": "gs://openpi-assets/checkpoints/pi05_droid_jointpos",
        "scene": args.scene,
        "task": asdict(task),
        "suite": args.suite,
        "success_definition": {
            "xy_threshold_m": task.success_xy_m,
            "relative_z_range_m": [task.success_z_min_m, task.success_z_max_m],
            "minimum_source_displacement_m": 0.05,
            "observed_gripper_open_below": OPEN_GRIPPER_THRESHOLD,
            "stable_radius_m": STABLE_RADIUS_METERS,
            "stable_steps": STABLE_STEPS,
        },
        "cases_total": len(summaries),
        "cases_successful": sum(int(item["success"]) for item in summaries),
        "cases": summaries,
    }
    (run_dir / "scene_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"\n场景 {args.scene} 完成: {report['cases_successful']}/{report['cases_total']} 严格成功",
        flush=True,
    )
    print(f"RUN_DIR={run_dir.resolve()}", flush=True)
    env.close()


try:
    main()
except BaseException:
    traceback.print_exc()
    raise
finally:
    simulation_app.close()
