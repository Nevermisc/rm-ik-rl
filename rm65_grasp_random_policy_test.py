import os

import numpy as np

from rm65_grasp_task_skeleton import (
    MAX_STEPS,
    SimpleGraspTask,
    create_simulation_context_with_rm65,
    simulation_app,
)


NUM_EPISODES = int(os.environ.get("ISAAC_NUM_EPISODES", "3"))
EPISODE_STEPS = int(os.environ.get("ISAAC_EPISODE_STEPS", str(min(MAX_STEPS, 360))))
RANDOM_SEED = int(os.environ.get("ISAAC_RANDOM_SEED", "7"))


def sample_random_action(rng):
    """Sample one random action in the same format expected by SimpleGraspTask.step().

    action[0]: gripper opening delta
      -1.0 closes the gripper
      +1.0 opens the gripper

    action[1]: vertical movement delta
      -1.0 moves fingers down
      +1.0 moves fingers up
    """
    return rng.uniform(low=-1.0, high=1.0, size=2)


def run_random_policy_test():
    rng = np.random.default_rng(RANDOM_SEED)

    simulation_context = create_simulation_context_with_rm65()
    task = SimpleGraspTask(simulation_context)

    simulation_context.initialize_physics()
    simulation_context.play()

    print("RM65 random policy grasp test started.", flush=True)
    print(
        f"episodes={NUM_EPISODES} episode_steps={EPISODE_STEPS} seed={RANDOM_SEED}",
        flush=True,
    )
    print("This checks whether reset/step/action/reward/done are stable before PPO.", flush=True)

    success_count = 0
    episode_returns = []

    for episode_index in range(NUM_EPISODES):
        obs = task.reset()
        episode_return = 0.0
        done = False
        info = {"max_cube_z": task.max_cube_z, "success": False}

        print(
            f"episode={episode_index:02d} reset "
            f"cube_z={obs['cube_z']:.4f} "
            f"opening={obs['opening']:.4f}",
            flush=True,
        )

        for step_index in range(EPISODE_STEPS):
            action = sample_random_action(rng)
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
                    f"done={done}",
                    flush=True,
                )

            if done:
                break

        success_count += int(bool(info["success"]))
        episode_returns.append(episode_return)

        print(
            f"EPISODE_FINAL episode={episode_index:02d} "
            f"return={episode_return:.4f} "
            f"max_cube_z={info['max_cube_z']:.4f} "
            f"success={info['success']} "
            f"steps={step_index + 1}",
            flush=True,
        )

    average_return = float(np.mean(episode_returns)) if episode_returns else 0.0
    print(
        f"RANDOM_POLICY_FINAL "
        f"success_count={success_count}/{NUM_EPISODES} "
        f"average_return={average_return:.4f}",
        flush=True,
    )

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    run_random_policy_test()
