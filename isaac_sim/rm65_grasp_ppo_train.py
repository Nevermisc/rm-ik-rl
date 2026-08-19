import os
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Normal

from rm65_grasp_task_skeleton import (
    CUBE_INITIAL_Z,
    SimpleGraspTask,
    create_simulation_context_with_rm65,
    simulation_app,
)


@dataclass
class PPOConfig:
    seed: int = int(os.environ.get("ISAAC_PPO_SEED", "11"))
    updates: int = int(os.environ.get("ISAAC_PPO_UPDATES", "4"))
    rollout_steps: int = int(os.environ.get("ISAAC_PPO_ROLLOUT_STEPS", "256"))
    episode_steps: int = int(os.environ.get("ISAAC_PPO_EPISODE_STEPS", "360"))
    gamma: float = float(os.environ.get("ISAAC_PPO_GAMMA", "0.98"))
    gae_lambda: float = float(os.environ.get("ISAAC_PPO_GAE_LAMBDA", "0.95"))
    clip_ratio: float = float(os.environ.get("ISAAC_PPO_CLIP_RATIO", "0.2"))
    policy_lr: float = float(os.environ.get("ISAAC_PPO_POLICY_LR", "3e-4"))
    value_lr: float = float(os.environ.get("ISAAC_PPO_VALUE_LR", "1e-3"))
    train_epochs: int = int(os.environ.get("ISAAC_PPO_TRAIN_EPOCHS", "4"))
    minibatch_size: int = int(os.environ.get("ISAAC_PPO_MINIBATCH_SIZE", "64"))
    entropy_coef: float = float(os.environ.get("ISAAC_PPO_ENTROPY_COEF", "0.01"))
    value_coef: float = float(os.environ.get("ISAAC_PPO_VALUE_COEF", "0.5"))
    bc_epochs: int = int(os.environ.get("ISAAC_PPO_BC_EPOCHS", "0"))
    bc_steps: int = int(os.environ.get("ISAAC_PPO_BC_STEPS", "720"))
    model_path: str = os.environ.get(
        "ISAAC_PPO_MODEL_PATH",
        "/home/iot22/robot-learning/rm-ik-rl/rm65_grasp_ppo_policy.pt",
    )


class ActorCritic(nn.Module):
    def __init__(self, obs_dim, action_dim):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
        )
        self.actor_mean = nn.Linear(64, action_dim)
        self.critic = nn.Linear(64, 1)
        self.log_std = nn.Parameter(torch.full((action_dim,), -0.4))

    def forward(self, obs):
        features = self.shared(obs)
        mean = torch.tanh(self.actor_mean(features))
        value = self.critic(features).squeeze(-1)
        std = torch.exp(self.log_std).expand_as(mean)
        return mean, std, value

    def act(self, obs):
        mean, std, value = self.forward(obs)
        dist = Normal(mean, std)
        raw_action = dist.rsample()
        action = torch.clamp(raw_action, -1.0, 1.0)
        log_prob = dist.log_prob(raw_action).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        return action, log_prob, entropy, value

    def deterministic_action(self, obs):
        mean, _, value = self.forward(obs)
        return torch.clamp(mean, -1.0, 1.0), value

    def evaluate_actions(self, obs, actions):
        mean, std, value = self.forward(obs)
        dist = Normal(mean, std)
        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)
        return log_prob, entropy, value


def behavior_clone_from_scripted_policy(model, task, cfg):
    if cfg.bc_epochs <= 0:
        return

    obs_examples = []
    action_examples = []

    obs_dict = task.reset()
    for step_index in range(cfg.bc_steps):
        action = task.scripted_action(step_index)
        obs_examples.append(obs_to_vector(obs_dict, step_index, cfg.episode_steps))
        action_examples.append(action.astype(np.float32))
        obs_dict, _, done, _ = task.step(action)
        if done:
            break

    obs_tensor = torch.as_tensor(np.asarray(obs_examples), dtype=torch.float32)
    action_tensor = torch.as_tensor(np.asarray(action_examples), dtype=torch.float32)

    bc_optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(cfg.bc_epochs):
        mean, _, _ = model.forward(obs_tensor)
        loss = nn.functional.mse_loss(mean, action_tensor)
        bc_optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
        bc_optimizer.step()

        if epoch == 0 or epoch == cfg.bc_epochs - 1:
            print(
                f"BC epoch={epoch:03d} loss={loss.item():.6f} examples={len(obs_examples)}",
                flush=True,
            )


def obs_to_vector(obs, step_in_episode, episode_steps):
    """Convert the task dictionary observation into a small numeric vector."""
    cube_pos = obs["cube_pos"]
    left_pos = obs["left_finger_pos"]
    right_pos = obs["right_finger_pos"]

    finger_center = 0.5 * (left_pos + right_pos)
    cube_relative_to_finger = cube_pos - finger_center

    return np.array(
        [
            obs["cube_z"],
            obs["cube_z"] - CUBE_INITIAL_Z,
            obs["opening"],
            obs["finger_z"],
            cube_relative_to_finger[0],
            cube_relative_to_finger[1],
            cube_relative_to_finger[2],
            step_in_episode / max(1, episode_steps),
        ],
        dtype=np.float32,
    )


def compute_gae(rewards, values, dones, last_value, gamma, gae_lambda):
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = 0.0

    for t in reversed(range(len(rewards))):
        if t == len(rewards) - 1:
            next_non_terminal = 1.0 - dones[t]
            next_value = last_value
        else:
            next_non_terminal = 1.0 - dones[t + 1]
            next_value = values[t + 1]

        delta = rewards[t] + gamma * next_value * next_non_terminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_non_terminal * last_gae
        advantages[t] = last_gae

    returns = advantages + values
    return advantages, returns


def run_ppo_training():
    cfg = PPOConfig()
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    simulation_context = create_simulation_context_with_rm65()
    task = SimpleGraspTask(simulation_context)

    simulation_context.initialize_physics()
    simulation_context.play()

    obs_dict = task.reset()
    step_in_episode = 0
    episode_index = 0
    episode_return = 0.0
    episode_success = False

    obs_dim = len(obs_to_vector(obs_dict, step_in_episode, cfg.episode_steps))
    action_dim = 2
    model = ActorCritic(obs_dim, action_dim)

    optimizer = torch.optim.Adam(
        [
            {"params": model.shared.parameters(), "lr": cfg.policy_lr},
            {"params": model.actor_mean.parameters(), "lr": cfg.policy_lr},
            {"params": [model.log_std], "lr": cfg.policy_lr},
            {"params": model.critic.parameters(), "lr": cfg.value_lr},
        ]
    )

    print("RM65 PPO grasp training started.", flush=True)
    print(
        f"updates={cfg.updates} rollout_steps={cfg.rollout_steps} "
        f"episode_steps={cfg.episode_steps} seed={cfg.seed} "
        f"bc_epochs={cfg.bc_epochs}",
        flush=True,
    )

    behavior_clone_from_scripted_policy(model, task, cfg)
    obs_dict = task.reset()
    step_in_episode = 0
    episode_return = 0.0
    episode_success = False

    for update_index in range(cfg.updates):
        obs_buffer = []
        action_buffer = []
        log_prob_buffer = []
        reward_buffer = []
        done_buffer = []
        value_buffer = []

        rollout_episode_returns = []
        rollout_success_count = 0

        for rollout_step in range(cfg.rollout_steps):
            obs_vec = obs_to_vector(obs_dict, step_in_episode, cfg.episode_steps)
            obs_tensor = torch.as_tensor(obs_vec, dtype=torch.float32).unsqueeze(0)

            with torch.no_grad():
                action_tensor, log_prob_tensor, _, value_tensor = model.act(obs_tensor)

            action = action_tensor.squeeze(0).cpu().numpy()
            next_obs_dict, reward, done, info = task.step(action)

            episode_return += reward
            episode_success = episode_success or bool(info["success"])
            step_in_episode += 1

            timeout = step_in_episode >= cfg.episode_steps
            terminal = bool(done or timeout)

            obs_buffer.append(obs_vec)
            action_buffer.append(action)
            log_prob_buffer.append(float(log_prob_tensor.item()))
            reward_buffer.append(float(reward))
            done_buffer.append(float(terminal))
            value_buffer.append(float(value_tensor.item()))

            obs_dict = next_obs_dict

            if terminal:
                rollout_episode_returns.append(episode_return)
                rollout_success_count += int(episode_success)
                print(
                    f"episode={episode_index:03d} "
                    f"return={episode_return:.4f} "
                    f"max_cube_z={info['max_cube_z']:.4f} "
                    f"success={episode_success} "
                    f"steps={step_in_episode}",
                    flush=True,
                )
                episode_index += 1
                episode_return = 0.0
                episode_success = False
                step_in_episode = 0
                obs_dict = task.reset()

        last_obs_vec = obs_to_vector(obs_dict, step_in_episode, cfg.episode_steps)
        last_obs_tensor = torch.as_tensor(last_obs_vec, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            _, _, last_value_tensor = model.forward(last_obs_tensor)
        last_value = float(last_value_tensor.item())

        rewards = np.asarray(reward_buffer, dtype=np.float32)
        values = np.asarray(value_buffer, dtype=np.float32)
        dones = np.asarray(done_buffer, dtype=np.float32)

        advantages, returns = compute_gae(
            rewards,
            values,
            dones,
            last_value,
            cfg.gamma,
            cfg.gae_lambda,
        )

        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        obs_tensor = torch.as_tensor(np.asarray(obs_buffer), dtype=torch.float32)
        action_tensor = torch.as_tensor(np.asarray(action_buffer), dtype=torch.float32)
        old_log_prob_tensor = torch.as_tensor(np.asarray(log_prob_buffer), dtype=torch.float32)
        advantage_tensor = torch.as_tensor(advantages, dtype=torch.float32)
        return_tensor = torch.as_tensor(returns, dtype=torch.float32)

        num_samples = obs_tensor.shape[0]
        indices = np.arange(num_samples)

        last_policy_loss = 0.0
        last_value_loss = 0.0
        last_entropy = 0.0

        for _ in range(cfg.train_epochs):
            np.random.shuffle(indices)
            for start in range(0, num_samples, cfg.minibatch_size):
                batch_idx = indices[start:start + cfg.minibatch_size]

                batch_obs = obs_tensor[batch_idx]
                batch_actions = action_tensor[batch_idx]
                batch_old_log_probs = old_log_prob_tensor[batch_idx]
                batch_advantages = advantage_tensor[batch_idx]
                batch_returns = return_tensor[batch_idx]

                new_log_probs, entropy, values_pred = model.evaluate_actions(batch_obs, batch_actions)
                ratio = torch.exp(new_log_probs - batch_old_log_probs)

                unclipped = ratio * batch_advantages
                clipped = torch.clamp(ratio, 1.0 - cfg.clip_ratio, 1.0 + cfg.clip_ratio) * batch_advantages
                policy_loss = -torch.min(unclipped, clipped).mean()

                value_loss = nn.functional.mse_loss(values_pred, batch_returns)
                entropy_loss = -entropy.mean()

                loss = (
                    policy_loss
                    + cfg.value_coef * value_loss
                    + cfg.entropy_coef * entropy_loss
                )

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
                optimizer.step()

                last_policy_loss = float(policy_loss.item())
                last_value_loss = float(value_loss.item())
                last_entropy = float(entropy.mean().item())

        mean_rollout_return = float(np.mean(rollout_episode_returns)) if rollout_episode_returns else episode_return
        print(
            f"UPDATE {update_index:03d} "
            f"mean_episode_return={mean_rollout_return:.4f} "
            f"rollout_success_count={rollout_success_count} "
            f"policy_loss={last_policy_loss:.4f} "
            f"value_loss={last_value_loss:.4f} "
            f"entropy={last_entropy:.4f}",
            flush=True,
        )

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "obs_dim": obs_dim,
            "action_dim": action_dim,
            "config": cfg.__dict__,
        },
        cfg.model_path,
    )
    print(f"SAVED_MODEL path={cfg.model_path}", flush=True)

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    run_ppo_training()
