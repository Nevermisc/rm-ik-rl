#!/usr/bin/env python3
"""Unit-check the staged RM65 v4 pipeline gate."""

from __future__ import annotations

from check_rm65_v4_pipeline_gate import EXPECTED_REPO_ID, validate_contracts


def fixtures():
    backup = {"status": "pass", "verified_copy_count": 2, "checks": {"all": True}}
    plans = {
        "status": "pass",
        "real_robot_command_sent": False,
        "correction": {"status": "pass", "case_count": 36, "physical_group_count": 9},
        "confirmation": {
            "status": "pass",
            "case_count": 20,
            "checks": {"expected_v4_checkpoint": True},
        },
    }
    summary = {
        "status": "pass",
        "episode_count": 36,
        "passed_episode_count": 36,
        "collection_plan_coverage": {"status": "pass"},
        "real_robot_command_sent": False,
    }
    render = {
        "status": "pass",
        "physical_group_count": 9,
        "passed_physical_group_count": 9,
        "real_robot_command_sent": False,
    }
    conversion = {
        "status": "pass",
        "repo_id": EXPECTED_REPO_ID,
        "episode_count": 102,
        "episode_count_by_dataset_root": {
            "/data/rm65_scripted_v1": 36,
            "/data/rm65_pi05_failure_correction_expert_v1": 30,
            "/data/rm65_pi05_failure_correction_v4_expert_v1": 36,
        },
        "policy_window": True,
    }
    norm = {"status": "pass", "repo_id": EXPECTED_REPO_ID, "sha256": "a" * 64}
    validation = {
        "status": "pass",
        "repo_id": EXPECTED_REPO_ID,
        "expected_rm65_state_dim": 7,
        "expected_rm65_action_dim_before_padding": 7,
    }
    return backup, plans, summary, render, conversion, norm, validation


def main() -> int:
    backup, plans, summary, render, conversion, norm, validation = fixtures()
    collection = validate_contracts(stage="collection", backup=backup, plans=plans)
    prepare = validate_contracts(
        stage="prepare",
        backup=backup,
        plans=plans,
        summary=summary,
        render_groups=render,
    )
    train = validate_contracts(
        stage="train",
        backup=backup,
        plans=plans,
        summary=summary,
        render_groups=render,
        conversion=conversion,
        norm=norm,
        openpi_validation=validation,
    )
    damaged = dict(conversion)
    damaged["episode_count_by_dataset_root"] = dict(
        conversion["episode_count_by_dataset_root"]
    )
    damaged["episode_count_by_dataset_root"][
        "/data/rm65_pi05_failure_correction_expert_v1"
    ] = 29
    rejected = validate_contracts(
        stage="train",
        backup=backup,
        plans=plans,
        summary=summary,
        render_groups=render,
        conversion=damaged,
        norm=norm,
        openpi_validation=validation,
    )
    passed = bool(
        collection["status"] == "pass"
        and prepare["status"] == "pass"
        and train["status"] == "pass"
        and train["training_contract"]["num_train_steps"] == 6000
        and train["training_contract"]["peak_lr"] == 2e-6
        and rejected["status"] == "fail"
        and rejected["checks"]["conversion_source_counts"] is False
    )
    print(f"RM65_V4_PIPELINE_GATE={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
