"""在 sim-evals 的 DROID scene 1 中评测 pi0.5 joint-position 策略。"""

from __future__ import annotations

import argparse
import json
import math
import time
import traceback
from datetime import datetime
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description="pi0.5 DROID scene 1 闭环评测")
parser.add_argument("--episodes", type=int, default=3)
parser.add_argument("--open-loop-horizon", type=int, default=8)
parser.add_argument("--output-root", type=Path, default=Path("runs/pi05_jointpos_scene1"))
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


INSTRUCTION = "put the cube in the bowl"
CAMERA_HEIGHT = 180
CAMERA_WIDTH = 320
FPS = 15
SUCCESS_XY_METERS = 0.10
SUCCESS_Z_MIN_METERS = -0.02
SUCCESS_Z_MAX_METERS = 0.16
SUCCESS_HOLD_STEPS = 15


class DroidJointPosClient:
    """与 sim-evals 官方 DroidJointPosClient 等价，去掉未使用的 tyro 依赖。"""

    def __init__(self, open_loop_horizon: int) -> None:
        self.open_loop_horizon = open_loop_horizon
        self.client = websocket_client_policy.WebsocketClientPolicy("localhost", 8000)
        self.reset()

    def reset(self) -> None:
        self.action_index = 0
        self.action_chunk = None

    def infer(self, obs: dict, instruction: str) -> dict:
        policy = obs["policy"]
        external = policy["external_cam"][0].detach().cpu().numpy()
        wrist = policy["wrist_cam"][0].detach().cpu().numpy()
        external_224 = image_tools.resize_with_pad(external, 224, 224)
        wrist_224 = image_tools.resize_with_pad(wrist, 224, 224)

        if self.action_index == 0 or self.action_index >= self.open_loop_horizon:
            request = {
                "observation/exterior_image_1_left": external_224,
                "observation/wrist_image_left": wrist_224,
                "observation/joint_position": policy["arm_joint_pos"].detach().cpu().numpy(),
                "observation/gripper_position": policy["gripper_pos"].detach().cpu().numpy(),
                "prompt": instruction,
            }
            self.action_chunk = np.asarray(self.client.infer(request)["actions"])
            self.action_index = 0

        action = np.asarray(self.action_chunk[self.action_index], dtype=np.float32).copy()
        self.action_index += 1
        action[-1] = 1.0 if action[-1] > 0.5 else 0.0
        return {"action": action, "viz": np.concatenate((external_224, wrist_224), axis=1)}


def vec3(asset) -> np.ndarray:
    return asset.data.root_pos_w[0, :3].detach().cpu().numpy().astype(np.float64)


def write_video(path: Path, frames: list[np.ndarray]) -> None:
    writer = imageio.get_writer(path, fps=FPS, codec="libx264", quality=7)
    try:
        for frame in frames:
            writer.append_data(frame)
    finally:
        writer.close()


def main() -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_root / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    cfg = parse_env_cfg("DROID", device=args.device, num_envs=1, use_fabric=True)
    cfg.set_scene(1)
    for camera_name in ("external_cam", "external_cam_2", "wrist_cam"):
        camera = getattr(cfg.scene, camera_name)
        camera.height = CAMERA_HEIGHT
        camera.width = CAMERA_WIDTH

    env = gym.make("DROID", cfg=cfg)
    obs, _ = env.reset()
    obs, _ = env.reset()  # 第二次渲染后材质才完整
    client = DroidJointPosClient(open_loop_horizon=args.open_loop_horizon)
    max_steps = int(env.unwrapped.max_episode_length)
    device = env.unwrapped.device

    cube = env.unwrapped.scene["rubiks_cube"]
    bowl = env.unwrapped.scene["_24_bowl"]
    all_summaries: list[dict] = []

    print(f"任务指令: {INSTRUCTION}", flush=True)
    print(f"每回合最多步数: {max_steps}（{max_steps / FPS:.1f} 秒）", flush=True)
    print(f"结果目录: {run_dir.resolve()}", flush=True)

    with torch.inference_mode():
        for episode in range(1, args.episodes + 1):
            if episode > 1:
                obs, _ = env.reset()
                obs, _ = env.reset()
            client.reset()

            initial_cube = vec3(cube)
            initial_bowl = vec3(bowl)
            frames: list[np.ndarray] = []
            cube_positions: list[np.ndarray] = []
            bowl_positions: list[np.ndarray] = []
            commanded_gripper: list[float] = []
            consecutive_inside = 0
            success = False
            start = time.perf_counter()

            print(
                f"\n回合 {episode}/{args.episodes} 开始 | "
                f"魔方={np.round(initial_cube, 4)} | 碗={np.round(initial_bowl, 4)}",
                flush=True,
            )

            for step in range(max_steps):
                ret = client.infer(obs, INSTRUCTION)
                frames.append(np.asarray(ret["viz"], dtype=np.uint8))
                action_np = np.asarray(ret["action"], dtype=np.float32)
                commanded_gripper.append(float(action_np[-1]))
                action = torch.as_tensor(action_np, dtype=torch.float32, device=device).unsqueeze(0)
                obs, _, terminated, truncated, _ = env.step(action)

                cube_pos = vec3(cube)
                bowl_pos = vec3(bowl)
                cube_positions.append(cube_pos.copy())
                bowl_positions.append(bowl_pos.copy())
                xy_distance = float(np.linalg.norm(cube_pos[:2] - bowl_pos[:2]))
                relative_z = float(cube_pos[2] - bowl_pos[2])
                inside_now = (
                    xy_distance <= SUCCESS_XY_METERS
                    and SUCCESS_Z_MIN_METERS <= relative_z <= SUCCESS_Z_MAX_METERS
                )
                consecutive_inside = consecutive_inside + 1 if inside_now else 0

                if step == 0 or (step + 1) % 30 == 0:
                    moved = float(np.linalg.norm(cube_pos - initial_cube))
                    print(
                        f"  步 {step + 1:3d}: 魔方移动={moved:.3f}m, "
                        f"距碗中心XY={xy_distance:.3f}m, "
                        f"夹爪命令={action_np[-1]:.0f}",
                        flush=True,
                    )

                if consecutive_inside >= SUCCESS_HOLD_STEPS:
                    success = True
                    print(f"  成功条件连续保持 {SUCCESS_HOLD_STEPS} 步。", flush=True)
                    break
                if bool(torch.as_tensor(terminated).any()) or bool(torch.as_tensor(truncated).any()):
                    break

            elapsed = time.perf_counter() - start
            cube_array = np.asarray(cube_positions)
            bowl_array = np.asarray(bowl_positions)
            final_cube = cube_array[-1]
            final_bowl = bowl_array[-1]
            final_xy = float(np.linalg.norm(final_cube[:2] - final_bowl[:2]))
            cube_displacement = float(np.linalg.norm(final_cube - initial_cube))
            gripper_array = np.asarray(commanded_gripper, dtype=np.float32)

            ep_dir = run_dir / f"episode_{episode:02d}"
            ep_dir.mkdir(parents=True, exist_ok=True)
            write_video(ep_dir / "policy_views.mp4", frames)
            imageio.imwrite(ep_dir / "final_policy_view.png", frames[-1])
            imageio.imwrite(
                ep_dir / "final_external_camera.png",
                obs["policy"]["external_cam"][0].detach().cpu().numpy(),
            )
            imageio.imwrite(
                ep_dir / "final_wrist_camera.png",
                obs["policy"]["wrist_cam"][0].detach().cpu().numpy(),
            )
            np.savez_compressed(
                ep_dir / "trajectory.npz",
                cube_position=cube_array,
                bowl_position=bowl_array,
                gripper_command=gripper_array,
            )

            summary = {
                "episode": episode,
                "instruction": INSTRUCTION,
                "success": success,
                "steps": len(cube_positions),
                "elapsed_seconds": round(elapsed, 3),
                "initial_cube_xyz": initial_cube.tolist(),
                "initial_bowl_xyz": initial_bowl.tolist(),
                "final_cube_xyz": final_cube.tolist(),
                "final_bowl_xyz": final_bowl.tolist(),
                "cube_displacement_m": cube_displacement,
                "final_cube_bowl_xy_distance_m": final_xy,
                "closed_gripper_fraction": float(np.mean(gripper_array > 0.5)),
            }
            (ep_dir / "summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            all_summaries.append(summary)
            print(
                f"回合 {episode} 结束: success={success}, 步数={len(cube_positions)}, "
                f"魔方总位移={cube_displacement:.3f}m, 最终XY距离={final_xy:.3f}m, "
                f"耗时={elapsed:.1f}s",
                flush=True,
            )

    overall = {
        "policy": "pi05_droid_jointpos_polaris",
        "checkpoint": "gs://openpi-assets/checkpoints/pi05_droid_jointpos",
        "environment": "sim-evals DROID scene 1",
        "camera_resolution": [CAMERA_HEIGHT, CAMERA_WIDTH],
        "open_loop_horizon": args.open_loop_horizon,
        "episodes_requested": args.episodes,
        "episodes_successful": sum(int(x["success"]) for x in all_summaries),
        "episodes": all_summaries,
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"\n完整评测结束: {overall['episodes_successful']}/{args.episodes} 回合成功",
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
