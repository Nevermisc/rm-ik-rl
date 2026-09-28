#!/usr/bin/env python3
"""Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_POLICY_MAX_ACTION_CHUNKS = 120


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.5)
        return client.connect_ex(("127.0.0.1", port)) == 0


def report_gripper_open_threshold(report: dict) -> float | None:
    configured = report.get("controller_config", {}).get("policy_gripper_open_threshold")
    if isinstance(configured, (int, float)):
        return float(configured)
    historical = report.get("criteria", {}).get("final_gripper_normalized_lt")
    if isinstance(historical, (int, float)):
        return float(historical)
    return None


def report_gripper_actual_open_threshold(report: dict) -> float | None:
    configured = report.get("controller_config", {}).get(
        "policy_gripper_actual_open_threshold"
    )
    return float(configured) if isinstance(configured, (int, float)) else None


def report_policy_noise_seed(report: dict) -> int | None:
    top_level = report.get("policy_noise_seed")
    sampling = report.get("deterministic_sampling", {})
    nested = sampling.get("case_seed") if isinstance(sampling, dict) else None
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested)):
        return None
    if top_level < 0 or nested < 0 or top_level != nested:
        return None
    return top_level


def report_simulation_seed(report: dict) -> int | None:
    top_level = report.get("simulation_seed")
    determinism = report.get("simulation_determinism", {})
    nested = determinism.get("seed") if isinstance(determinism, dict) else None
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (top_level, nested)):
        return None
    if top_level < 0 or nested < 0 or top_level != nested:
        return None
    return top_level


def validate_evaluation_cases(cases: list[dict]) -> None:
    if not cases:
        raise ValueError("evaluation plan has no cases")
    case_ids = [case.get("case_id") for case in cases]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ValueError("every evaluation case must have a non-empty case_id")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("evaluation case ids must be unique")
    seeds = [case.get("policy_noise_seed") for case in cases]
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds):
        raise ValueError("every evaluation case must have a non-negative integer policy_noise_seed")
    if len(set(seeds)) != len(seeds):
        raise ValueError("evaluation policy_noise_seed values must be unique")
    simulation_seeds = [case.get("simulation_seed") for case in cases]
    if any(
        isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
        for seed in simulation_seeds
    ):
        raise ValueError("every evaluation case must have a non-negative integer simulation_seed")
    if len(set(simulation_seeds)) != len(simulation_seeds):
        raise ValueError("evaluation simulation_seed values must be unique")


def load_existing_report(
    path: Path,
    checkpoint_id: str,
    gripper_open_threshold: float,
    gripper_actual_open_threshold: float,
    policy_max_action_chunks: int,
    policy_noise_seed: int,
    simulation_seed: int,
) -> dict | None:
    if not path.is_file():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if report.get("policy_checkpoint_id") != checkpoint_id:
        return None
    if report.get("pi05_used") is not True or report.get("simulation_only") is not True:
        return None
    existing_threshold = report_gripper_open_threshold(report)
    if existing_threshold is None or abs(existing_threshold - gripper_open_threshold) > 1e-9:
        return None
    existing_actual_threshold = report_gripper_actual_open_threshold(report)
    if (
        existing_actual_threshold is None
        or abs(existing_actual_threshold - gripper_actual_open_threshold) > 1e-9
    ):
        return None
    if (
        report.get("controller_config", {}).get("policy_max_action_chunks")
        != policy_max_action_chunks
    ):
        return None
    if report_policy_noise_seed(report) != policy_noise_seed:
        return None
    if report_simulation_seed(report) != simulation_seed:
        return None
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--plan",
        type=Path,
        default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_deterministic_v1.json",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "datasets" / "rm65_pi05_eval_v1",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=PROJECT_ROOT / "results" / "rm65_pi05_eval_v1_summary.json",
    )
    parser.add_argument("--policy-port", type=int, default=8000)
    parser.add_argument(
        "--gripper-open-threshold",
        type=float,
        default=0.12,
        help="Normalized 4C2 threshold used for in-loop release verification.",
    )
    parser.add_argument(
        "--gripper-actual-open-threshold",
        type=float,
        default=0.20,
        help="Normalized actual 4C2 feedback threshold for release detection.",
    )
    parser.add_argument(
        "--repo-id",
        default=os.environ.get("RM65_REPO_ID", "local/rm65_sim_train"),
        help="LeRobot repository id whose normalization statistics belong to the checkpoint.",
    )
    parser.add_argument("--case-timeout-seconds", type=int, default=1200)
    parser.add_argument(
        "--policy-max-action-chunks",
        type=int,
        default=EVALUATION_POLICY_MAX_ACTION_CHUNKS,
        help=(
            f"Use {EVALUATION_POLICY_MAX_ACTION_CHUNKS} for evaluation; other values "
            "are diagnostic-only."
        ),
    )
    parser.add_argument(
        "--infrastructure-retries",
        type=int,
        default=1,
        help="Retry only cases that fail to produce a valid task report.",
    )
    parser.add_argument("--max-cases", type=int)
    args = parser.parse_args()

    if args.infrastructure_retries < 0:
        raise ValueError("--infrastructure-retries must be non-negative")
    if args.policy_max_action_chunks < 1:
        raise ValueError("--policy-max-action-chunks must be positive")
    if not 0.0 < args.gripper_open_threshold < 1.0:
        raise ValueError("--gripper-open-threshold must be between 0 and 1")
    if not args.gripper_open_threshold <= args.gripper_actual_open_threshold < 1.0:
        raise ValueError(
            "--gripper-actual-open-threshold must be at least the target threshold and below 1"
        )

    checkpoint = args.checkpoint.expanduser().resolve()
    if not checkpoint.is_dir():
        raise FileNotFoundError(checkpoint)
    plan_path = args.plan.expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("format") != "rm65_pi05_sim_evaluation_plan_deterministic_v1":
        raise ValueError("unsupported evaluation plan format")
    cases = plan.get("cases", [])
    if args.max_cases is not None:
        cases = cases[: args.max_cases]
    validate_evaluation_cases(cases)
    if port_open(args.policy_port):
        raise RuntimeError(f"policy port {args.policy_port} is already in use")

    output_root = args.output_root.expanduser().resolve()
    summary_path = args.summary.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    openpi_root = Path.home() / "robot-learning" / "openpi"
    checkpoint_id = f"{checkpoint.parent.name}/{checkpoint.name}"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [
            str(PROJECT_ROOT),
            str(openpi_root / "packages" / "openpi-client" / "src"),
            environment.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    environment["XLA_PYTHON_CLIENT_MEM_FRACTION"] = environment.get(
        "XLA_PYTHON_CLIENT_MEM_FRACTION", "0.50"
    )
    environment["RM65_REPO_ID"] = args.repo_id
    environment["POLICY_GRIPPER_OPEN_THRESHOLD"] = str(args.gripper_open_threshold)
    environment["POLICY_GRIPPER_ACTUAL_OPEN_THRESHOLD"] = str(
        args.gripper_actual_open_threshold
    )
    environment["POLICY_MAX_ACTION_CHUNKS"] = str(args.policy_max_action_chunks)
    server_log_path = PROJECT_ROOT / "outputs" / "rm65_pi05_policy_server_suite.log"
    server_log_path.parent.mkdir(parents=True, exist_ok=True)
    with server_log_path.open("w", encoding="utf-8") as server_log:
        server = subprocess.Popen(
            [
                str(openpi_root / ".venv" / "bin" / "python"),
                "-u",
                str(PROJECT_ROOT / "scripts" / "serve_rm65_policy.py"),
                "--checkpoint",
                str(checkpoint),
                "--repo-id",
                args.repo_id,
                "--port",
                str(args.policy_port),
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            stdout=server_log,
            stderr=subprocess.STDOUT,
        )
        try:
            for _ in range(180):
                if server.poll() is not None:
                    raise RuntimeError(
                        f"policy server stopped during startup; see {server_log_path}"
                    )
                if port_open(args.policy_port):
                    break
                time.sleep(1)
            else:
                raise TimeoutError("policy server did not listen within 180 seconds")

            case_results = []
            for position, case in enumerate(cases, start=1):
                case_id = case["case_id"]
                case_seed = case["policy_noise_seed"]
                simulation_seed = case["simulation_seed"]
                episode_dir = output_root / case_id
                report_path = episode_dir / "task_report.json"
                existing = load_existing_report(
                    report_path,
                    checkpoint_id,
                    args.gripper_open_threshold,
                    args.gripper_actual_open_threshold,
                    args.policy_max_action_chunks,
                    case_seed,
                    simulation_seed,
                )
                if existing is not None:
                    print(f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True)
                    case_results.append(
                        {
                            "case_id": case_id,
                            "policy_noise_seed": case_seed,
                            "simulation_seed": simulation_seed,
                            "runner_returncode": 0,
                            "report": existing,
                            "reused": True,
                        }
                    )
                    continue
                episode_dir.mkdir(parents=True, exist_ok=True)
                case_environment = environment.copy()
                case_environment["POLICY_SERVER_MODE"] = "external"
                case_environment["POLICY_PORT"] = str(args.policy_port)
                command = [
                    "bash",
                    str(PROJECT_ROOT / "scripts" / "run_pi05_rm65_closed_loop.sh"),
                    str(checkpoint),
                    str(episode_dir),
                    str(case["transfer_joint_1_rad"]),
                    str(case["source_offset_x_m"]),
                    str(case["source_offset_y_m"]),
                    case["prompt"],
                    str(case_seed),
                    str(simulation_seed),
                ]
                print(f"[{position}/{len(cases)}] {case_id}: run", flush=True)
                attempt_results = []
                report = None
                for attempt in range(args.infrastructure_retries + 1):
                    log_name = "runner.log" if attempt == 0 else f"runner_retry_{attempt}.log"
                    case_log_path = episode_dir / log_name
                    with case_log_path.open("w", encoding="utf-8") as case_log:
                        try:
                            completed = subprocess.run(
                                command,
                                cwd=PROJECT_ROOT,
                                env=case_environment,
                                stdout=case_log,
                                stderr=subprocess.STDOUT,
                                timeout=args.case_timeout_seconds,
                                check=False,
                            )
                            returncode = completed.returncode
                            timed_out = False
                        except subprocess.TimeoutExpired:
                            returncode = 124
                            timed_out = True
                    attempt_results.append(
                        {
                            "attempt": attempt + 1,
                            "runner_returncode": returncode,
                            "timed_out": timed_out,
                            "log": str(case_log_path),
                        }
                    )
                    report = load_existing_report(
                        report_path,
                        checkpoint_id,
                        args.gripper_open_threshold,
                        args.gripper_actual_open_threshold,
                        args.policy_max_action_chunks,
                        case_seed,
                        simulation_seed,
                    )
                    if report is not None:
                        break
                    if attempt < args.infrastructure_retries:
                        print(
                            f"[{position}/{len(cases)}] {case_id}: missing_report; "
                            f"retry infrastructure attempt {attempt + 2}",
                            flush=True,
                        )
                case_results.append(
                    {
                        "case_id": case_id,
                        "policy_noise_seed": case_seed,
                        "simulation_seed": simulation_seed,
                        "runner_returncode": returncode,
                        "timed_out": timed_out,
                        "report": report,
                        "reused": False,
                        "log": str(case_log_path),
                        "infrastructure_attempts": attempt_results,
                    }
                )
                status = report.get("status") if report else "missing_report"
                print(f"[{position}/{len(cases)}] {case_id}: {status}", flush=True)
        finally:
            server.terminate()
            try:
                server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=20)

    valid_reports = [item["report"] for item in case_results if item.get("report") is not None]
    successes = sum(report.get("status") == "pass" for report in valid_reports)
    episode_count = len(valid_reports)
    success_rate = successes / episode_count if episode_count else 0.0
    passed = episode_count >= 20 and success_rate >= 0.8
    summary = {
        "status": "pass" if passed else "fail",
        "evaluation_kind": "isaaclab_pi0.5_closed_loop",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "plan": str(plan_path),
        "checkpoint": str(checkpoint),
        "policy_checkpoint_id": checkpoint_id,
        "repo_id": args.repo_id,
        "gripper_open_threshold_normalized": args.gripper_open_threshold,
        "gripper_actual_open_threshold_normalized": (
            args.gripper_actual_open_threshold
        ),
        "policy_max_action_chunks": args.policy_max_action_chunks,
        "diagnostic_only": (
            args.policy_max_action_chunks != EVALUATION_POLICY_MAX_ACTION_CHUNKS
        ),
        "deterministic_sampling": {
            "mode": "explicit_numpy_gaussian_noise_v1",
            "case_seed_source": "evaluation_plan",
            "chunk_seed_rule": "case_seed + chunk_index",
            "resume_requires_matching_seed": True,
            "simulation_seed_source": "evaluation_plan",
            "resume_requires_matching_simulation_seed": True,
        },
        "planned_case_count": len(cases),
        "episode_count": episode_count,
        "success_count": successes,
        "success_rate": success_rate,
        "gate": {"minimum_episode_count": 20, "minimum_success_rate": 0.8},
        "cases": case_results,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
