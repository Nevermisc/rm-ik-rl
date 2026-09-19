#!/usr/bin/env python3
"""Run one RM65 pi0.5 server across a resumable IsaacLab evaluation plan."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.5)
        return client.connect_ex(("127.0.0.1", port)) == 0


def load_existing_report(path: Path, checkpoint_id: str) -> dict | None:
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
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--plan",
        type=Path,
        default=PROJECT_ROOT / "config" / "rm65_pi05_evaluation_plan_v1.json",
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
    parser.add_argument("--case-timeout-seconds", type=int, default=1200)
    parser.add_argument("--max-cases", type=int)
    args = parser.parse_args()

    checkpoint = args.checkpoint.expanduser().resolve()
    if not checkpoint.is_dir():
        raise FileNotFoundError(checkpoint)
    plan_path = args.plan.expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("format") != "rm65_pi05_sim_evaluation_plan_v1":
        raise ValueError("unsupported evaluation plan format")
    cases = plan.get("cases", [])
    if args.max_cases is not None:
        cases = cases[: args.max_cases]
    if not cases:
        raise ValueError("evaluation plan has no cases")
    case_ids = [case["case_id"] for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("evaluation case ids must be unique")
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
                episode_dir = output_root / case_id
                report_path = episode_dir / "task_report.json"
                existing = load_existing_report(report_path, checkpoint_id)
                if existing is not None:
                    print(f"[{position}/{len(cases)}] {case_id}: reuse {existing['status']}", flush=True)
                    case_results.append(
                        {"case_id": case_id, "runner_returncode": 0, "report": existing, "reused": True}
                    )
                    continue
                episode_dir.mkdir(parents=True, exist_ok=True)
                case_log_path = episode_dir / "runner.log"
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
                ]
                print(f"[{position}/{len(cases)}] {case_id}: run", flush=True)
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
                report = load_existing_report(report_path, checkpoint_id)
                case_results.append(
                    {
                        "case_id": case_id,
                        "runner_returncode": returncode,
                        "timed_out": timed_out,
                        "report": report,
                        "reused": False,
                        "log": str(case_log_path),
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
