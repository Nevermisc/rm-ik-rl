#!/usr/bin/env python3
"""Fail closed on RM65 v4 collection, preparation, and training contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


EXPECTED_REPO_ID = "local/rm65_sim_failure_correction_v4_train"
EXPECTED_SOURCE_COUNTS = {
    "rm65_scripted_v1": 36,
    "rm65_pi05_failure_correction_expert_v1": 30,
    "rm65_pi05_failure_correction_v4_expert_v1": 36,
}
SHA256 = re.compile(r"[0-9a-f]{64}")


def validate_contracts(
    *,
    stage: str,
    backup: dict[str, Any],
    plans: dict[str, Any],
    summary: dict[str, Any] | None = None,
    render_groups: dict[str, Any] | None = None,
    conversion: dict[str, Any] | None = None,
    norm: dict[str, Any] | None = None,
    openpi_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if stage not in {"collection", "prepare", "train"}:
        raise ValueError(f"unsupported stage: {stage}")
    correction_plan = plans.get("correction", {})
    confirmation_plan = plans.get("confirmation", {})
    checks: dict[str, bool] = {
        "backup_gate_pass": backup.get("status") == "pass",
        "two_verified_v3_copies": backup.get("verified_copy_count") == 2,
        "backup_checks_all_pass": bool(backup.get("checks"))
        and all(backup.get("checks", {}).values()),
        "plans_validation_pass": plans.get("status") == "pass",
        "correction_plan_36_cases_9_groups": correction_plan.get("status") == "pass"
        and correction_plan.get("case_count") == 36
        and correction_plan.get("physical_group_count") == 9,
        "confirmation_plan_20_cases": confirmation_plan.get("status") == "pass"
        and confirmation_plan.get("case_count") == 20,
        "fresh_confirmation_checkpoint_frozen": confirmation_plan.get("checks", {}).get(
            "expected_v4_checkpoint"
        )
        is True,
        "plans_simulation_only": plans.get("real_robot_command_sent") is False,
    }

    if stage in {"prepare", "train"}:
        summary = summary or {}
        render_groups = render_groups or {}
        checks.update(
            {
                "v4_expert_summary_pass": summary.get("status") == "pass",
                "v4_expert_36_of_36_pass": summary.get("episode_count") == 36
                and summary.get("passed_episode_count") == 36,
                "v4_collection_plan_coverage_pass": summary.get(
                    "collection_plan_coverage", {}
                ).get("status")
                == "pass",
                "v4_render_group_analysis_pass": render_groups.get("status") == "pass",
                "v4_render_groups_9_of_9_pass": render_groups.get(
                    "physical_group_count"
                )
                == 9
                and render_groups.get("passed_physical_group_count") == 9,
                "v4_raw_data_simulation_only": summary.get("real_robot_command_sent")
                is False
                and render_groups.get("real_robot_command_sent") is False,
            }
        )

    if stage == "train":
        conversion = conversion or {}
        norm = norm or {}
        openpi_validation = openpi_validation or {}
        source_counts = {
            Path(path).name: count
            for path, count in conversion.get("episode_count_by_dataset_root", {}).items()
        }
        checks.update(
            {
                "conversion_pass": conversion.get("status") == "pass",
                "conversion_repo_id": conversion.get("repo_id") == EXPECTED_REPO_ID,
                "conversion_102_episodes": conversion.get("episode_count") == 102,
                "conversion_source_counts": source_counts == EXPECTED_SOURCE_COUNTS,
                "conversion_policy_window": conversion.get("policy_window") is True,
                "norm_stats_pass": norm.get("status") == "pass",
                "norm_stats_repo_id": norm.get("repo_id") == EXPECTED_REPO_ID,
                "norm_stats_sha256_declared": bool(
                    SHA256.fullmatch(str(norm.get("sha256", "")))
                ),
                "openpi_validation_pass": openpi_validation.get("status") == "pass",
                "openpi_validation_repo_id": openpi_validation.get("repo_id")
                == EXPECTED_REPO_ID,
                "openpi_contract_dimensions": openpi_validation.get(
                    "expected_rm65_state_dim"
                )
                == 7
                and openpi_validation.get("expected_rm65_action_dim_before_padding") == 7,
            }
        )

    return {
        "schema": "rm65_pi05_failure_correction_v4_pipeline_gate_v1",
        "stage": stage,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "training_contract": {
            "repo_id": EXPECTED_REPO_ID,
            "episode_count": 102,
            "source_episode_counts": EXPECTED_SOURCE_COUNTS,
            "initial_checkpoint": "rm65_failure_correction_v3_lora_10k/9999/params",
            "target_checkpoint": "rm65_failure_correction_v4_lora_6k/5999",
            "num_train_steps": 6000,
            "batch_size": 1,
            "warmup_steps": 300,
            "peak_lr": 2e-6,
            "decay_lr": 5e-7,
        },
        "simulation_only": True,
        "real_robot_command_sent": False,
    }


def load(path: Path | None) -> dict[str, Any] | None:
    return None if path is None else json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("collection", "prepare", "train"), required=True)
    parser.add_argument("--backup-gate", type=Path, required=True)
    parser.add_argument("--plans-validation", type=Path, required=True)
    parser.add_argument("--expert-summary", type=Path)
    parser.add_argument("--render-groups", type=Path)
    parser.add_argument("--conversion", type=Path)
    parser.add_argument("--norm", type=Path)
    parser.add_argument("--openpi-validation", type=Path)
    parser.add_argument("--norm-asset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.stage in {"prepare", "train"} and (
        args.expert_summary is None or args.render_groups is None
    ):
        parser.error("prepare/train stages require --expert-summary and --render-groups")
    if args.stage == "train" and any(
        item is None
        for item in (args.conversion, args.norm, args.openpi_validation, args.norm_asset)
    ):
        parser.error(
            "train stage requires --conversion, --norm, --openpi-validation, and --norm-asset"
        )

    report = validate_contracts(
        stage=args.stage,
        backup=load(args.backup_gate) or {},
        plans=load(args.plans_validation) or {},
        summary=load(args.expert_summary),
        render_groups=load(args.render_groups),
        conversion=load(args.conversion),
        norm=load(args.norm),
        openpi_validation=load(args.openpi_validation),
    )
    if args.stage == "train":
        norm = load(args.norm) or {}
        norm_asset = args.norm_asset.expanduser().resolve()
        declared_path = Path(norm.get("output_path", "")).expanduser().resolve()
        declared_hash = norm.get("sha256")
        actual_hash = (
            hashlib.sha256(norm_asset.read_bytes()).hexdigest()
            if norm_asset.is_file()
            else None
        )
        report["checks"].update(
            {
                "norm_asset_exists": norm_asset.is_file(),
                "norm_asset_path_matches_report": norm_asset == declared_path,
                "norm_asset_hash_matches_report": actual_hash == declared_hash,
            }
        )
        report["norm_asset"] = {
            "path": str(norm_asset),
            "sha256": actual_hash,
        }
        report["status"] = (
            "pass" if all(report["checks"].values()) else "fail"
        )
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
