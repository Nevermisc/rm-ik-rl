#!/usr/bin/env python3
"""Build a fail-closed RM65 pi0.5 policy artifact manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.execution_gate import ACTION_SEMANTICS, FORMAT_NAME, validate_policy_artifact


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tree(path: Path) -> tuple[str, int, int]:
    """Hash relative names, sizes, and contents in deterministic order."""

    digest = hashlib.sha256()
    files = [candidate for candidate in path.rglob("*") if candidate.is_file()]
    total_bytes = 0
    for candidate in sorted(files, key=lambda item: item.relative_to(path).as_posix()):
        relative = candidate.relative_to(path).as_posix().encode("utf-8")
        size = candidate.stat().st_size
        total_bytes += size
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(size.to_bytes(8, "big"))
        with candidate.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest(), len(files), total_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-report", type=Path, required=True)
    parser.add_argument("--norm-stats", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--simulation-summary", type=Path)
    parser.add_argument("--hardware-readiness", type=Path)
    args = parser.parse_args()

    training_report_path = args.training_report.expanduser().resolve()
    training_report = json.loads(training_report_path.read_text(encoding="utf-8"))
    if training_report.get("status") != "pass":
        raise ValueError("training report does not have status=pass")
    checkpoint = Path(training_report["latest_checkpoint"]).expanduser().resolve()
    if not checkpoint.is_dir():
        raise FileNotFoundError(f"checkpoint directory not found: {checkpoint}")
    norm_stats = args.norm_stats.expanduser().resolve()
    if not norm_stats.is_file():
        raise FileNotFoundError(f"norm stats not found: {norm_stats}")

    checkpoint_hash, checkpoint_file_count, checkpoint_bytes = sha256_tree(checkpoint)
    simulation_evaluation = {
        "status": "not_started",
        "episode_count": 0,
        "success_rate": 0.0,
    }
    if args.simulation_summary is not None:
        summary_path = args.simulation_summary.expanduser().resolve()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        simulation_evaluation = {
            "status": summary.get("status", "unknown"),
            "episode_count": summary.get("episode_count", 0),
            "success_rate": summary.get("success_rate", 0.0),
            "source": str(summary_path),
        }
    hardware_readiness = {
        "controller_address_verified": False,
        "joint_order_verified": False,
        "joint_feedback_read_only_passed": False,
        "policy_shadow_passed": False,
        "emergency_stop_verified": False,
        "software_stop_verified": False,
        "low_speed_limit_configured": False,
        "workspace_bounds_configured": False,
        "empty_workspace_test_passed": False,
        "gripper_command_mapping_verified": False,
        "external_camera_calibrated": False,
        "wrist_camera_calibrated": False,
        "watchdog_stop_verified": False,
        "human_supervisor_required": True,
        "human_supervisor_present": False,
    }
    if args.hardware_readiness is not None:
        readiness_path = args.hardware_readiness.expanduser().resolve()
        supplied = json.loads(readiness_path.read_text(encoding="utf-8"))
        hardware_readiness.update(supplied)
        hardware_readiness["source"] = str(readiness_path)

    manifest = {
        "format": FORMAT_NAME,
        "model_family": "pi0.5",
        "robot_model": "RM65-B",
        "gripper_model": "4C2",
        "action_horizon": 10,
        "action_dimension": 7,
        "action_semantics": ACTION_SEMANTICS,
        "training": {
            "status": "complete",
            "dataset_repo_id": training_report["repo_id"],
            "config_name": training_report.get("config_name"),
            "steps": training_report.get("num_train_steps"),
            "report": str(training_report_path),
        },
        "checkpoint": {
            "path": str(checkpoint),
            "sha256": checkpoint_hash,
            "hash_algorithm": "sha256_tree_v1",
            "file_count": checkpoint_file_count,
            "total_bytes": checkpoint_bytes,
        },
        "norm_stats": {
            "path": str(norm_stats),
            "sha256": sha256_file(norm_stats),
            "hash_algorithm": "sha256_file",
        },
        "simulation_evaluation": simulation_evaluation,
        "hardware_readiness": hardware_readiness,
    }
    manifest["simulation_gate"] = validate_policy_artifact(manifest, target="simulation")
    manifest["real_robot_gate"] = validate_policy_artifact(manifest, target="real_robot")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
