#!/usr/bin/env python3
"""Run or resume a machine-readable scripted-expert collection plan on Linux."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.expert_episode import validate_episode


def completed_episode(
    directory: Path, case_id: str, expected_simulation_seed: int | None = None
) -> bool:
    if not (directory / "metadata.json").is_file() or not (
        directory / "task_report.json"
    ).is_file():
        return False
    validation = validate_episode(directory, require_images=True)
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    task = json.loads((directory / "task_report.json").read_text(encoding="utf-8"))
    return bool(
        validation["status"] == "pass"
        and metadata.get("metadata", {}).get("task_success") is True
        and metadata.get("metadata", {}).get("collection_case_id") == case_id
        and (
            expected_simulation_seed is None
            or metadata.get("metadata", {}).get("collection_simulation_seed")
            == expected_simulation_seed
        )
        and task.get("status") == "pass"
        and task.get("unassisted_full_task_complete") is True
    )


def build_command(case: dict, directory: Path) -> list[str]:
    command = [
        "bash",
        str(PROJECT_ROOT / "scripts/run_recorded_expert_demo.sh"),
        str(directory),
        str(case["transfer_joint_1_rad"]),
        str(case["source_offset_x_m"]),
        str(case["source_offset_y_m"]),
        case["prompt"],
    ]
    simulation_seed = case.get("simulation_seed")
    if simulation_seed is not None:
        if not isinstance(simulation_seed, int) or simulation_seed < 0:
            raise ValueError(f"invalid simulation_seed for {case.get('case_id')}")
        command.append(str(simulation_seed))
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "validation", "all"), default="all")
    parser.add_argument("--max-cases", type=int)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan.get("format") != "rm65_expert_collection_plan_v1":
        raise ValueError("unsupported collection plan")
    cases = [
        item for item in plan["cases"] if args.split == "all" or item["split"] == args.split
    ]
    if args.max_cases is not None:
        if args.max_cases <= 0:
            raise ValueError("--max-cases must be positive")
        cases = cases[: args.max_cases]
    args.dataset_root.mkdir(parents=True, exist_ok=True)
    completed = 0
    skipped = 0
    for case in cases:
        directory = args.dataset_root / f"episode_{case['episode_index']:06d}"
        if completed_episode(directory, case["case_id"], case.get("simulation_seed")):
            skipped += 1
            continue
        if directory.exists():
            raise RuntimeError(
                f"existing episode is incomplete or belongs to another case: {directory}"
            )
        command = build_command(case, directory)
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        manifest_path = directory / "metadata.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        collection_metadata = {
            "collection_case_id": case["case_id"],
            "collection_split": case["split"],
        }
        for key in (
            "simulation_seed",
            "physical_group_id",
            "physical_variant",
            "render_repeat_index",
            "render_repeat_count",
            "source_evaluation_case_id",
            "source_outcome_pattern",
        ):
            if key in case:
                metadata_key = (
                    "collection_simulation_seed" if key == "simulation_seed" else key
                )
                collection_metadata[metadata_key] = case[key]
        manifest["metadata"].update(collection_metadata)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if not completed_episode(
            directory, case["case_id"], case.get("simulation_seed")
        ):
            raise RuntimeError(f"recorded episode failed post-run validation: {directory}")
        completed += 1
    report = {
        "status": "pass",
        "plan": str(args.plan.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "requested_case_count": len(cases),
        "newly_completed_count": completed,
        "already_completed_count": skipped,
        "simulation_only": True,
        "expert": "scripted",
        "pi05_used": False,
        "real_robot_command_sent": False,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
