"""Fail-closed policy artifact checks before RM65 simulation or hardware use."""

from __future__ import annotations

import re
from typing import Any


FORMAT_NAME = "rm65_pi05_policy_artifact_v1"
ACTION_SEMANTICS = [
    *(f"joint_{index}_absolute_target_rad" for index in range(1, 7)),
    "gripper_normalized_target",
]
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _at_least(value: Any, minimum: float) -> bool:
    try:
        return float(value) >= minimum
    except (TypeError, ValueError):
        return False


def validate_policy_artifact(manifest: dict[str, Any], *, target: str) -> dict[str, Any]:
    """Return a machine-readable readiness report; never infer missing evidence."""

    if target not in {"simulation", "real_robot"}:
        raise ValueError("target must be 'simulation' or 'real_robot'")
    checks = {
        "format": manifest.get("format") == FORMAT_NAME,
        "model_family": manifest.get("model_family") == "pi0.5",
        "robot_model": manifest.get("robot_model") == "RM65-B",
        "gripper_model": manifest.get("gripper_model") == "4C2",
        "action_horizon": manifest.get("action_horizon") == 10,
        "action_dimension": manifest.get("action_dimension") == 7,
        "action_semantics": manifest.get("action_semantics") == ACTION_SEMANTICS,
        "training_complete": manifest.get("training", {}).get("status") == "complete",
        "rm65_dataset_declared": bool(
            manifest.get("training", {}).get("dataset_repo_id")
        ),
        "checkpoint_sha256": bool(
            _SHA256.fullmatch(str(manifest.get("checkpoint", {}).get("sha256", "")))
        ),
        "norm_stats_sha256": bool(
            _SHA256.fullmatch(str(manifest.get("norm_stats", {}).get("sha256", "")))
        ),
    }
    if target == "real_robot":
        evaluation = manifest.get("simulation_evaluation", {})
        hardware = manifest.get("hardware_readiness", {})
        checks.update(
            {
                "simulation_evaluation_passed": evaluation.get("status") == "pass",
                "simulation_episode_count": _at_least(
                    evaluation.get("episode_count"), 20
                ),
                "simulation_success_rate": _at_least(
                    evaluation.get("success_rate"), 0.8
                ),
                "emergency_stop_verified": hardware.get("emergency_stop_verified") is True,
                "low_speed_limit_configured": hardware.get("low_speed_limit_configured") is True,
                "empty_workspace_test_passed": hardware.get("empty_workspace_test_passed") is True,
                "human_supervisor_required": hardware.get("human_supervisor_required") is True,
            }
        )
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "status": "pass" if not failed else "blocked",
        "target": target,
        "execution_allowed": not failed,
        "checks": checks,
        "failed_checks": failed,
    }
