import os

import numpy as np
import torch

from rm65_grasp_ppo_train import ActorCritic, obs_to_vector
from rm65_grasp_task_skeleton import (
    SimpleGraspTask,
    create_simulation_context_with_rm65,
    simulation_app,
)


MODEL_PATH = os.environ.get(
    "ISAAC_PPO_MODEL_PATH",
    "/home/iot22/robot-learning/rm-ik-rl/rm65_grasp_ppo_policy.pt",
)
EVAL_EPISODES = int(os.environ.get("ISAAC_EVAL_EPISODES", "3"))
EVAL_STEPS = int(os.environ.get("ISAAC_EVAL_STEPS", "360"))


def run_policy_eval():
    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    model = ActorCritic(checkpoint["obs_dim"], checkpoint["action_dim"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    simulation_context = create_simulation_context_with_rm65()
    task = SimpleGraspTask(simulation_context)

    simulation_context.initialize_physics()
    simulation_context.play()

    print(f"RM65 grasp policy eval started. model={MODEL_PATH}", flush=True)

    success_count = 0

    for episode_index in range(EVAL_EPISODES):
        obs = task.reset()
        episode_return = 0.0
        info = {"max_cube_z": task.max_cube_z, "success": False}

        for step_index in range(EVAL_STEPS):
            obs_vec = obs_to_vector(obs, step_index, EVAL_STEPS)
            obs_tensor = torch.as_tensor(obs_vec, dtype=torch.float32).unsqueeze(0)

            with torch.no_grad():
                action_tensor, _ = model.deterministic_action(obs_tensor)

            action = action_tensor.squeeze(0).cpu().numpy()
            obs, reward, done, info = task.step(action)
            episode_return += reward

            if step_index % 60 == 0 or done:
                print(
                    f"episode={episode_index:02d} "
                    f"step={step_index:04d} "
                    f"action=[{action[0]:+.3f},{action[1]:+.3f}] "
                    f"cube_z={obs['cube_z']:.4f} "
                    f"opening={obs['opening']:.4f} "
                    f"reward={reward:.4f} "
                    f"success={obs['success']}",
                    flush=True,
                )

            if done:
                break

        success_count += int(bool(info["success"]))
        print(
            f"EVAL_EPISODE_FINAL episode={episode_index:02d} "
            f"return={episode_return:.4f} "
            f"max_cube_z={info['max_cube_z']:.4f} "
            f"success={info['success']} "
            f"steps={step_index + 1}",
            flush=True,
        )

    print(
        f"EVAL_FINAL success_count={success_count}/{EVAL_EPISODES}",
        flush=True,
    )

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    run_policy_eval()
