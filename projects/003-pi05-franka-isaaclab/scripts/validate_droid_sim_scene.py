"""验证sim-evals的DROID场景能在现有Isaac Lab中加载并输出正确观测。"""

from pathlib import Path
import traceback

from isaaclab.app import AppLauncher


app_launcher = AppLauncher(headless=True, enable_cameras=True)
simulation_app = app_launcher.app

import gymnasium as gym
import imageio.v3 as iio
import torch

import sim_evals.environments  # noqa: F401
from isaaclab_tasks.utils import parse_env_cfg


OUTPUT_DIR = Path("runs/scene_validation")


def main() -> None:
    cfg = parse_env_cfg("DROID", device="cuda:0", num_envs=1, use_fabric=True)
    cfg.set_scene(1)
    # DROID发布给策略的图像是180x320；保持16:9视场并减少RTX初始化和显存开销。
    for camera_name in ("external_cam", "external_cam_2", "wrist_cam"):
        camera = getattr(cfg.scene, camera_name)
        camera.height = 180
        camera.width = 320
    env = gym.make("DROID", cfg=cfg)
    observations, _ = env.reset()
    observations, _ = env.reset()

    policy = observations["policy"]
    arm = policy["arm_joint_pos"]
    gripper = policy["gripper_pos"]
    action = torch.cat((arm, gripper), dim=-1).unsqueeze(0).to(env.unwrapped.device)
    for _ in range(5):
        observations, _, _, _, _ = env.step(action)

    policy = observations["policy"]
    external = policy["external_cam"][0].detach().cpu().numpy()
    wrist = policy["wrist_cam"][0].detach().cpu().numpy()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    iio.imwrite(OUTPUT_DIR / "external_cam.png", external)
    iio.imwrite(OUTPUT_DIR / "wrist_cam.png", wrist)

    print(f"arm_joint_pos={tuple(policy['arm_joint_pos'].shape)}")
    print(f"gripper_pos={tuple(policy['gripper_pos'].shape)}")
    print(f"external_cam={external.shape} {external.dtype}")
    print(f"wrist_cam={wrist.shape} {wrist.dtype}")
    print(f"输出目录={OUTPUT_DIR.resolve()}")
    print("DROID_SIM_SCENE_VALIDATION=PASS", flush=True)
    env.close()


try:
    main()
except BaseException:
    traceback.print_exc()
    raise
finally:
    simulation_app.close()
