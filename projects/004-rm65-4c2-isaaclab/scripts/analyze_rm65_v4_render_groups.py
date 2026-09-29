#!/usr/bin/env python3
"""Audit same-seed physical repeatability and RTX diversity in RM65 v4 data."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.expert_episode import validate_episode


ARRAY_KEYS = ("action", "observation_state", "cube_pose_wxyz")
IMAGE_VIEWS = ("external", "wrist")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def array_sha256(array: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("utf-8"))
    digest.update(json.dumps(list(array.shape)).encode("utf-8"))
    digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def maximum_absolute_difference(reference: np.ndarray, candidate: np.ndarray) -> float | None:
    if reference.shape != candidate.shape:
        return None
    if reference.size == 0:
        return 0.0
    return float(np.max(np.abs(reference.astype(np.float64) - candidate.astype(np.float64))))


def load_episode(directory: Path) -> dict[str, Any]:
    manifest = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    task_path = directory / "task_report.json"
    task = json.loads(task_path.read_text(encoding="utf-8")) if task_path.is_file() else {}
    with np.load(directory / "episode.npz") as archive:
        arrays = {key: np.asarray(archive[key]) for key in ARRAY_KEYS}
    image_hashes = {}
    for view in IMAGE_VIEWS:
        paths = manifest.get("image_paths", {}).get(view, [])
        image_hashes[view] = [sha256_bytes((directory / path).read_bytes()) for path in paths]
    metadata = manifest.get("metadata", {})
    validation = validate_episode(directory, require_images=True)
    healthy = bool(
        validation["status"] == "pass"
        and metadata.get("task_success") is True
        and task.get("status") == "pass"
        and task.get("unassisted_full_task_complete") is True
        and task.get("real_robot_command_sent") is not True
    )
    return {
        "name": directory.name,
        "directory": directory,
        "manifest": manifest,
        "metadata": metadata,
        "task": task,
        "validation": validation,
        "healthy": healthy,
        "arrays": arrays,
        "image_hashes": image_hashes,
    }


def image_diversity(episodes: list[dict[str, Any]], view: str) -> dict[str, Any]:
    sequences = [episode["image_hashes"][view] for episode in episodes]
    counts = [len(sequence) for sequence in sequences]
    consistent_frame_count = bool(counts and len(set(counts)) == 1 and counts[0] > 0)
    corresponding_unique_counts: list[int] = []
    if consistent_frame_count:
        corresponding_unique_counts = [
            len({sequence[index] for sequence in sequences}) for index in range(counts[0])
        ]
    sequence_hashes = [
        sha256_bytes("\n".join(sequence).encode("ascii")) for sequence in sequences
    ]
    diverse_frame_count = sum(value > 1 for value in corresponding_unique_counts)
    return {
        "status": "pass" if consistent_frame_count and diverse_frame_count > 0 else "fail",
        "frame_counts": counts,
        "consistent_frame_count": consistent_frame_count,
        "unique_sequence_count": len(set(sequence_hashes)),
        "diverse_corresponding_frame_count": diverse_frame_count,
        "diverse_corresponding_frame_ratio": (
            diverse_frame_count / counts[0] if consistent_frame_count else 0.0
        ),
        "maximum_unique_render_count_per_frame": (
            max(corresponding_unique_counts) if corresponding_unique_counts else 0
        ),
        "sequence_sha256": sequence_hashes,
    }


def consistent_physical_condition(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("transfer_joint_1_rad", "source_offset_xy_m", "physical_variant")
    values = {key: [episode["metadata"].get(key) for episode in episodes] for key in keys}
    prompt_values = [episode["manifest"].get("prompt") for episode in episodes]
    matches = len(set(prompt_values)) == 1
    for candidates in values.values():
        reference = candidates[0]
        for candidate in candidates[1:]:
            try:
                equal = bool(np.allclose(reference, candidate, rtol=0.0, atol=0.0))
            except (TypeError, ValueError):
                equal = reference == candidate
            matches = matches and equal
    return {
        "status": "pass" if matches else "fail",
        "prompt": prompt_values[0] if len(set(prompt_values)) == 1 else prompt_values,
        **{key: candidates[0] if all(item == candidates[0] for item in candidates) else candidates for key, candidates in values.items()},
    }


def analyze_group(
    group_id: str,
    episodes: list[dict[str, Any]],
    *,
    action_atol: float,
    initial_atol: float,
    physical_atol: float,
) -> dict[str, Any]:
    episodes = sorted(episodes, key=lambda item: item["metadata"].get("render_repeat_index", -1))
    metadata = [episode["metadata"] for episode in episodes]
    repeat_counts = [item.get("render_repeat_count") for item in metadata]
    expected_repeat_count = repeat_counts[0] if repeat_counts else None
    repeat_count_valid = bool(
        isinstance(expected_repeat_count, int)
        and expected_repeat_count > 1
        and len(set(repeat_counts)) == 1
        and len(episodes) == expected_repeat_count
    )
    indices = [item.get("render_repeat_index") for item in metadata]
    indices_valid = bool(
        repeat_count_valid and indices == list(range(expected_repeat_count))
    )
    seeds = [item.get("collection_simulation_seed") for item in metadata]
    seed_valid = bool(seeds and seeds[0] is not None and len(set(seeds)) == 1)
    health_valid = all(episode["healthy"] for episode in episodes)

    reference = episodes[0]["arrays"] if episodes else {}
    action_differences = [
        maximum_absolute_difference(reference["action"], episode["arrays"]["action"])
        for episode in episodes
    ]
    initial_state_differences = [
        maximum_absolute_difference(
            reference["observation_state"][:1], episode["arrays"]["observation_state"][:1]
        )
        for episode in episodes
    ]
    initial_cube_differences = [
        maximum_absolute_difference(
            reference["cube_pose_wxyz"][:1], episode["arrays"]["cube_pose_wxyz"][:1]
        )
        for episode in episodes
    ]
    state_trajectory_differences = [
        maximum_absolute_difference(
            reference["observation_state"], episode["arrays"]["observation_state"]
        )
        for episode in episodes
    ]
    cube_trajectory_differences = [
        maximum_absolute_difference(
            reference["cube_pose_wxyz"], episode["arrays"]["cube_pose_wxyz"]
        )
        for episode in episodes
    ]

    def differences_pass(values: list[float | None], tolerance: float) -> bool:
        return bool(values and all(value is not None and value <= tolerance for value in values))

    action_passed = differences_pass(action_differences, action_atol)
    initial_passed = differences_pass(initial_state_differences, initial_atol) and differences_pass(
        initial_cube_differences, initial_atol
    )
    trajectory_passed = differences_pass(
        state_trajectory_differences, physical_atol
    ) and differences_pass(cube_trajectory_differences, physical_atol)
    condition = consistent_physical_condition(episodes)
    images = {view: image_diversity(episodes, view) for view in IMAGE_VIEWS}
    passed = bool(
        repeat_count_valid
        and indices_valid
        and seed_valid
        and health_valid
        and condition["status"] == "pass"
        and action_passed
        and initial_passed
        and trajectory_passed
        and all(item["status"] == "pass" for item in images.values())
    )
    return {
        "physical_group_id": group_id,
        "status": "pass" if passed else "fail",
        "episode_count": len(episodes),
        "expected_render_repeat_count": expected_repeat_count,
        "render_repeat_indices": indices,
        "render_repeat_count_valid": repeat_count_valid,
        "render_repeat_indices_valid": indices_valid,
        "simulation_seed": seeds[0] if seed_valid else seeds,
        "simulation_seed_valid": seed_valid,
        "episode_health_valid": health_valid,
        "physical_condition": condition,
        "command_action_consistency": {
            "status": "pass" if action_passed else "fail",
            "absolute_tolerance": action_atol,
            "maximum_absolute_difference_by_repeat": action_differences,
            "array_sha256": [array_sha256(episode["arrays"]["action"]) for episode in episodes],
        },
        "initial_physical_state_consistency": {
            "status": "pass" if initial_passed else "fail",
            "absolute_tolerance": initial_atol,
            "observation_state_max_abs_difference_by_repeat": initial_state_differences,
            "cube_pose_max_abs_difference_by_repeat": initial_cube_differences,
        },
        "physical_trajectory_consistency": {
            "status": "pass" if trajectory_passed else "fail",
            "absolute_tolerance": physical_atol,
            "observation_state_max_abs_difference_by_repeat": state_trajectory_differences,
            "cube_pose_max_abs_difference_by_repeat": cube_trajectory_differences,
        },
        "rtx_image_diversity": images,
        "episodes": [
            {
                "episode": episode["name"],
                "collection_case_id": episode["metadata"].get("collection_case_id"),
                "render_repeat_index": episode["metadata"].get("render_repeat_index"),
                "validation_status": episode["validation"]["status"],
                "task_status": episode["task"].get("status", "missing"),
                "frame_count": episode["validation"].get("frame_count"),
            }
            for episode in episodes
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--group", action="append", dest="groups")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--action-atol", type=float, default=0.0)
    parser.add_argument("--initial-atol", type=float, default=1e-7)
    parser.add_argument("--physical-atol", type=float, default=1e-5)
    args = parser.parse_args()
    for name in ("action_atol", "initial_atol", "physical_atol"):
        if getattr(args, name) < 0.0:
            raise ValueError(f"--{name.replace('_', '-')} must be non-negative")

    directories = sorted(path.parent for path in args.dataset_root.glob("episode_*/metadata.json"))
    episodes = [load_episode(directory) for directory in directories]
    if args.groups:
        selected = set(args.groups)
        episodes = [
            episode
            for episode in episodes
            if episode["metadata"].get("physical_group_id") in selected
        ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    ungrouped = []
    for episode in episodes:
        group_id = episode["metadata"].get("physical_group_id")
        if not isinstance(group_id, str) or not group_id:
            ungrouped.append(episode["name"])
            continue
        grouped.setdefault(group_id, []).append(episode)

    group_reports = [
        analyze_group(
            group_id,
            items,
            action_atol=args.action_atol,
            initial_atol=args.initial_atol,
            physical_atol=args.physical_atol,
        )
        for group_id, items in sorted(grouped.items())
    ]

    coverage = {
        "requested": args.plan is not None,
        "status": "not_checked",
        "missing_case_ids": [],
        "unexpected_case_ids": [],
        "metadata_mismatch_case_ids": [],
    }
    if args.plan is not None:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if plan.get("format") != "rm65_expert_collection_plan_v1":
            raise ValueError("unsupported collection plan")
        expected_cases = plan["cases"]
        if args.groups:
            selected = set(args.groups)
            expected_cases = [
                case for case in expected_cases if case.get("physical_group_id") in selected
            ]
        expected = {case["case_id"]: case for case in expected_cases}
        observed = {
            episode["metadata"].get("collection_case_id"): episode
            for episode in episodes
            if episode["metadata"].get("collection_case_id") is not None
        }
        coverage["missing_case_ids"] = sorted(expected.keys() - observed.keys())
        coverage["unexpected_case_ids"] = sorted(observed.keys() - expected.keys())
        for case_id in sorted(expected.keys() & observed.keys()):
            case = expected[case_id]
            metadata = observed[case_id]["metadata"]
            mappings = {
                "simulation_seed": "collection_simulation_seed",
                "physical_group_id": "physical_group_id",
                "render_repeat_index": "render_repeat_index",
                "render_repeat_count": "render_repeat_count",
            }
            if any(metadata.get(target) != case.get(source) for source, target in mappings.items()):
                coverage["metadata_mismatch_case_ids"].append(case_id)
        coverage["status"] = (
            "pass"
            if not any(
                coverage[key]
                for key in (
                    "missing_case_ids",
                    "unexpected_case_ids",
                    "metadata_mismatch_case_ids",
                )
            )
            else "fail"
        )

    passed = bool(
        group_reports
        and not ungrouped
        and all(group["status"] == "pass" for group in group_reports)
        and (args.plan is None or coverage["status"] == "pass")
    )
    report = {
        "format": "rm65_v4_render_group_analysis_v1",
        "status": "pass" if passed else "fail",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "dataset_root": str(args.dataset_root.resolve()),
        "selected_groups": args.groups,
        "episode_count": len(episodes),
        "physical_group_count": len(group_reports),
        "passed_physical_group_count": sum(group["status"] == "pass" for group in group_reports),
        "ungrouped_episodes": ungrouped,
        "tolerances": {
            "action_atol": args.action_atol,
            "initial_atol": args.initial_atol,
            "physical_atol": args.physical_atol,
        },
        "collection_plan_coverage": coverage,
        "groups": group_reports,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
