#!/usr/bin/env python3
"""Static regression checks for the frozen RM65 v5 shell entry points."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def contains_all(path: str, fragments: tuple[str, ...]) -> bool:
    text = (PROJECT_ROOT / path).read_text(encoding="utf-8")
    return all(fragment in text for fragment in fragments)


def main() -> int:
    checks = {
        "collection": contains_all(
            "scripts/collect_rm65_failure_correction_v5.sh",
            (
                "check_rm65_v4_release_backup_gate.py",
                "check_rm65_v5_pipeline_gate.py",
                "--stage collection",
                "rm65_pi05_failure_correction_v5_expert_plan.json",
                "rm65_pi05_failure_correction_v5_expert_v1",
                'extra_args=(--max-cases 4)',
            ),
        ),
        "backup": contains_all(
            "scripts/verify_rm65_v5_collection_backup.sh",
            (
                "rm65_pi05_v5_collection_preservation_assets.json",
                "--location source",
                "--location backup",
                "--reference \"$source_manifest\"",
                "check_rm65_v5_collection_backup_gate.py",
            ),
        ),
        "preparation": contains_all(
            "scripts/prepare_rm65_failure_correction_v5.sh",
            (
                'repo_id="local/rm65_sim_failure_correction_v5_train"',
                "rm65_scripted_v1",
                "rm65_pi05_failure_correction_expert_v1",
                "rm65_pi05_failure_correction_v4_expert_v1",
                "rm65_pi05_failure_correction_v5_expert_v1",
                "--report-format rm65_v5_render_group_analysis_v1",
                "--stage prepare",
                "--stage train",
                "--policy-window",
            ),
        ),
        "training": contains_all(
            "scripts/train_rm65_pi05_failure_correction_v5.sh",
            (
                "rm65_failure_correction_v4_lora_6k/5999/params",
                'exp_name="rm65_failure_correction_v5_lora_4k"',
                "num_steps=4000",
                "save_interval=2000",
                "warmup_steps=200",
                "retention_args=(--keep-period 2000)",
                "--peak-lr 1e-6",
                "--decay-lr 2.5e-7",
            ),
        ),
        "evaluation": contains_all(
            "scripts/evaluate_rm65_pi05_failure_correction_v5.sh",
            (
                "check_rm65_v5_evaluation_preflight.py",
                "rm65_pi05_failure_correction_v5_confirmation_20.json",
                "rm65_pi05_failure_correction_v5_confirmation_run1",
                "rm65_pi05_failure_correction_v5_confirmation_run2",
                "rm65_pi05_failure_correction_v5_confirmation_run3",
                "analyze_rm65_repeatability_matrix.py",
            ),
        ),
    }
    passed = all(checks.values())
    print(f"RM65_V5_ENTRYPOINTS={'PASS' if passed else 'FAIL'}")
    if not passed:
        print({name: value for name, value in checks.items() if not value})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
