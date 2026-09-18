#!/usr/bin/env python3
"""Verify that incomplete and wrong-robot policies fail closed."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.execution_gate import validate_policy_artifact


def main() -> int:
    template = json.loads(
        (PROJECT_ROOT / "config/rm65_policy_artifact_template.json").read_text(
            encoding="utf-8"
        )
    )
    incomplete = validate_policy_artifact(template, target="simulation")
    trained = copy.deepcopy(template)
    trained["training"] = {"status": "complete", "dataset_repo_id": "local/rm65_sim"}
    trained["checkpoint"] = {"path": "checkpoint", "sha256": "a" * 64}
    trained["norm_stats"] = {"path": "norm_stats.json", "sha256": "b" * 64}
    simulation = validate_policy_artifact(trained, target="simulation")
    real_before_eval = validate_policy_artifact(trained, target="real_robot")
    trained["simulation_evaluation"] = {
        "status": "pass",
        "episode_count": 25,
        "success_rate": 0.84,
    }
    trained["hardware_readiness"] = {
        "emergency_stop_verified": True,
        "low_speed_limit_configured": True,
        "empty_workspace_test_passed": True,
        "human_supervisor_required": True,
    }
    real_ready = validate_policy_artifact(trained, target="real_robot")
    droid = copy.deepcopy(trained)
    droid["robot_model"] = "Franka"
    droid_rejected = validate_policy_artifact(droid, target="simulation")
    passed = (
        incomplete["status"] == "blocked"
        and simulation["execution_allowed"] is True
        and real_before_eval["execution_allowed"] is False
        and real_ready["execution_allowed"] is True
        and droid_rejected["execution_allowed"] is False
    )
    print(
        json.dumps(
            {
                "status": "pass" if passed else "fail",
                "incomplete_manifest_blocked": incomplete["status"] == "blocked",
                "rm65_simulation_manifest_allowed": simulation["execution_allowed"],
                "real_robot_blocked_before_evaluation": not real_before_eval[
                    "execution_allowed"
                ],
                "complete_real_robot_manifest_allowed": real_ready["execution_allowed"],
                "franka_manifest_blocked": not droid_rejected["execution_allowed"],
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
