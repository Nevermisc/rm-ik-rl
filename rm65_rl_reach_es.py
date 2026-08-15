"""Train a tiny model-free reaching policy for RM65-B with Lula FK.

This is a deliberately small reinforcement-learning baseline. It does not use
Isaac Lab yet. Instead, it uses Isaac Sim's Lula forward kinematics as the
environment model and optimizes a linear policy with evolution strategies.

Run on the lab Linux machine with Isaac Sim's Python:
    ~/isaac-sim-5.1.0/python.sh rm65_rl_reach_es.py --iterations 40
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": True})

import numpy as np
from isaacsim.robot_motion.motion_generation import LulaKinematicsSolver


PROJECT_DIR = Path(__file__).resolve().parent
URDF_PATH = PROJECT_DIR / "assets" / "RM65-B" / "urdf" / "RM65-B.urdf"
DESCRIPTION_PATH = PROJECT_DIR / "rm65_robot_description.yaml"
OUTPUT_DIR = PROJECT_DIR / "outputs"
END_EFFECTOR_FRAME = "link_6"

HOME_Q = np.array([0.0, -0.5, 1.0, 0.0, 0.5, 0.0], dtype=np.float64)
CENTER_Q = np.array([0.2, -0.8, 1.15, 0.2, 0.65, -0.2], dtype=np.float64)
JOINT_LOW = np.array([-2.9, -2.0, -0.2, -3.0, -1.5, -3.0], dtype=np.float64)
JOINT_HIGH = np.array([2.9, 1.2, 2.3, 3.0, 1.8, 3.0], dtype=np.float64)

OBS_DIM = 11
ACTION_DIM = 6


@dataclass
class EpisodeResult:
    reward: float
    final_error_m: float
    min_error_m: float
    success: bool
    steps: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--episodes-per-policy", type=int, default=6)
    parser.add_argument("--eval-episodes", type=int, default=50)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--sigma", type=float, default=0.08)
    parser.add_argument("--learning-rate", type=float, default=0.035)
    parser.add_argument("--step-scale", type=float, default=0.055)
    parser.add_argument("--success-threshold", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def build_solver() -> LulaKinematicsSolver:
    missing = [
        str(path)
        for path in (URDF_PATH, DESCRIPTION_PATH)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(f"Missing required files: {missing}")

    solver = LulaKinematicsSolver(
        robot_description_path=str(DESCRIPTION_PATH),
        urdf_path=str(URDF_PATH),
    )
    if END_EFFECTOR_FRAME not in solver.get_all_frame_names():
        raise ValueError(f"Missing end-effector frame: {END_EFFECTOR_FRAME}")
    return solver


def fk_position(solver: LulaKinematicsSolver, q: np.ndarray) -> np.ndarray:
    position, _rotation = solver.compute_forward_kinematics(END_EFFECTOR_FRAME, q)
    return np.asarray(position, dtype=np.float64)


def policy_action(weights: np.ndarray, q: np.ndarray, delta_xyz: np.ndarray, step_scale: float) -> np.ndarray:
    distance = np.linalg.norm(delta_xyz)
    observation = np.concatenate(
        [
            q / np.pi,
            5.0 * delta_xyz,
            np.array([5.0 * distance, 1.0], dtype=np.float64),
        ]
    )
    return step_scale * np.tanh(weights @ observation)


def sample_episode(rng: np.random.Generator, solver: LulaKinematicsSolver) -> tuple[np.ndarray, np.ndarray]:
    target_q = CENTER_Q + rng.uniform(
        low=np.array([-0.35, -0.35, -0.25, -0.35, -0.25, -0.35]),
        high=np.array([0.35, 0.35, 0.25, 0.35, 0.25, 0.35]),
    )
    start_q = HOME_Q + rng.uniform(
        low=np.array([-0.25, -0.15, -0.15, -0.2, -0.1, -0.2]),
        high=np.array([0.25, 0.15, 0.15, 0.2, 0.1, 0.2]),
    )
    return np.clip(start_q, JOINT_LOW, JOINT_HIGH), fk_position(solver, target_q)


def run_episode(
    weights: np.ndarray,
    solver: LulaKinematicsSolver,
    rng: np.random.Generator,
    horizon: int,
    step_scale: float,
    success_threshold: float,
) -> EpisodeResult:
    q, target_position = sample_episode(rng, solver)
    min_error = float("inf")
    total_reward = 0.0

    for step in range(1, horizon + 1):
        current_position = fk_position(solver, q)
        delta_xyz = target_position - current_position
        error = float(np.linalg.norm(delta_xyz))
        min_error = min(min_error, error)

        action = policy_action(weights, q, delta_xyz, step_scale)
        q = np.clip(q + action, JOINT_LOW, JOINT_HIGH)

        action_penalty = 0.01 * float(np.linalg.norm(action) ** 2)
        total_reward += -error - action_penalty
        if error < success_threshold:
            total_reward += 2.0
            return EpisodeResult(total_reward, error, min_error, True, step)

    final_error = float(np.linalg.norm(target_position - fk_position(solver, q)))
    min_error = min(min_error, final_error)
    total_reward += -5.0 * final_error
    return EpisodeResult(total_reward, final_error, min_error, final_error < success_threshold, horizon)


def evaluate_policy(
    weights: np.ndarray,
    solver: LulaKinematicsSolver,
    seed: int,
    episodes: int,
    horizon: int,
    step_scale: float,
    success_threshold: float,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    results = [
        run_episode(weights, solver, rng, horizon, step_scale, success_threshold)
        for _ in range(episodes)
    ]
    return {
        "mean_reward": float(np.mean([result.reward for result in results])),
        "mean_final_error_m": float(np.mean([result.final_error_m for result in results])),
        "median_final_error_m": float(np.median([result.final_error_m for result in results])),
        "mean_min_error_m": float(np.mean([result.min_error_m for result in results])),
        "success_rate": float(np.mean([result.success for result in results])),
        "mean_steps": float(np.mean([result.steps for result in results])),
    }


def train(args: argparse.Namespace, solver: LulaKinematicsSolver) -> tuple[np.ndarray, list[dict[str, float]]]:
    rng = np.random.default_rng(args.seed)
    weights = np.zeros((ACTION_DIM, OBS_DIM), dtype=np.float64)
    history: list[dict[str, float]] = []

    for iteration in range(1, args.iterations + 1):
        noises = rng.normal(size=(args.population, ACTION_DIM, OBS_DIM))
        score_deltas = np.zeros(args.population, dtype=np.float64)

        for index, noise in enumerate(noises):
            plus_score = evaluate_policy(
                weights + args.sigma * noise,
                solver,
                seed=args.seed + iteration * 1000 + index * 2,
                episodes=args.episodes_per_policy,
                horizon=args.horizon,
                step_scale=args.step_scale,
                success_threshold=args.success_threshold,
            )["mean_reward"]
            minus_score = evaluate_policy(
                weights - args.sigma * noise,
                solver,
                seed=args.seed + iteration * 1000 + index * 2,
                episodes=args.episodes_per_policy,
                horizon=args.horizon,
                step_scale=args.step_scale,
                success_threshold=args.success_threshold,
            )["mean_reward"]
            score_deltas[index] = plus_score - minus_score

        normalized = (score_deltas - score_deltas.mean()) / (score_deltas.std() + 1e-8)
        gradient = np.einsum("p,pij->ij", normalized, noises)
        weights += args.learning_rate * gradient / (args.population * args.sigma)

        if iteration == 1 or iteration % 5 == 0 or iteration == args.iterations:
            metrics = evaluate_policy(
                weights,
                solver,
                seed=args.seed + 100_000 + iteration,
                episodes=args.eval_episodes,
                horizon=args.horizon,
                step_scale=args.step_scale,
                success_threshold=args.success_threshold,
            )
            metrics["iteration"] = iteration
            history.append(metrics)
            print(
                "[RL] iter={iteration:03d} success={success_rate:.2%} "
                "mean_final_error={mean_final_error_m:.4f} m "
                "median_final_error={median_final_error_m:.4f} m".format(**metrics),
                flush=True,
            )

    return weights, history


def main() -> int:
    args = parse_args()
    start_time = time.time()
    solver = build_solver()
    weights, history = train(args, solver)

    final_metrics = evaluate_policy(
        weights,
        solver,
        seed=args.seed + 999_999,
        episodes=max(args.eval_episodes, 100),
        horizon=args.horizon,
        step_scale=args.step_scale,
        success_threshold=args.success_threshold,
    )
    elapsed_s = time.time() - start_time

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "rm65_rl_es_metrics.json"
    weights_path = OUTPUT_DIR / "rm65_rl_es_weights.npy"
    np.save(weights_path, weights)
    output_path.write_text(
        json.dumps(
            {
                "args": vars(args),
                "final_metrics": final_metrics,
                "history": history,
                "elapsed_s": elapsed_s,
                "weights_path": str(weights_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("[RL] Final metrics:")
    print(json.dumps(final_metrics, indent=2))
    print(f"[RL] Saved metrics: {output_path}")
    print(f"[RL] Saved weights:  {weights_path}")
    print(f"[RL] Elapsed: {elapsed_s:.1f} s")
    return 0


try:
    exit_code = main()
finally:
    simulation_app.close()

raise SystemExit(exit_code)
