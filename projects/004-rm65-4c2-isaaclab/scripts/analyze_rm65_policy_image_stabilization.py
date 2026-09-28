#!/usr/bin/env python3
"""Screen deterministic image transforms against exact RM65 policy observations."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image, ImageFilter

from analyze_rm65_exact_policy_observation_repeatability import exact_policy_image


VIEWS = ("external", "wrist")


@dataclass(frozen=True)
class Candidate:
    name: str
    filter_name: str = "identity"
    quantum: int = 1
    phase: int = 0


CANDIDATES = (
    Candidate("identity"),
    Candidate("quantize_q2", quantum=2),
    Candidate("quantize_q4", quantum=4),
    Candidate("quantize_q4_phase2", quantum=4, phase=2),
    Candidate("quantize_q8", quantum=8),
    Candidate("quantize_q8_phase4", quantum=8, phase=4),
    Candidate("quantize_q16", quantum=16),
    Candidate("median3", filter_name="median3"),
    Candidate("median5", filter_name="median5"),
    Candidate("box1", filter_name="box1"),
    Candidate("gaussian1", filter_name="gaussian1"),
    Candidate("median3_q4", filter_name="median3", quantum=4),
    Candidate("box1_q4", filter_name="box1", quantum=4),
    Candidate("gaussian1_q4", filter_name="gaussian1", quantum=4),
)


def apply_candidate(image: np.ndarray, candidate: Candidate) -> np.ndarray:
    value = Image.fromarray(image, mode="RGB")
    if candidate.filter_name == "median3":
        value = value.filter(ImageFilter.MedianFilter(size=3))
    elif candidate.filter_name == "median5":
        value = value.filter(ImageFilter.MedianFilter(size=5))
    elif candidate.filter_name == "box1":
        value = value.filter(ImageFilter.BoxBlur(radius=1))
    elif candidate.filter_name == "gaussian1":
        value = value.filter(ImageFilter.GaussianBlur(radius=1))
    elif candidate.filter_name != "identity":
        raise ValueError(f"unsupported image filter: {candidate.filter_name}")
    array = np.asarray(value, dtype=np.uint8)
    if candidate.quantum == 1:
        return array
    values = array.astype(np.int32)
    quantized = (
        ((values - candidate.phase + candidate.quantum // 2) // candidate.quantum)
        * candidate.quantum
        + candidate.phase
    )
    return np.clip(quantized, 0, 255).astype(np.uint8)


def pair_difference(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    difference = np.abs(reference.astype(np.int16) - candidate.astype(np.int16))
    changed = difference.max(axis=2) > 0
    return {
        "exact": bool(np.array_equal(reference, candidate)),
        "changed_pixel_count": int(changed.sum()),
        "changed_pixel_fraction": float(changed.mean()),
        "maximum_absolute_channel_difference": int(difference.max()),
    }


def build_analysis(
    plan: dict[str, Any],
    run_roots: list[Path],
    preprocess: Callable[[np.ndarray], np.ndarray],
    candidates: tuple[Candidate, ...] = CANDIDATES,
) -> dict[str, Any]:
    cases = plan.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("repeatability plan has no cases")
    if len(run_roots) < 2:
        raise ValueError("at least two run roots are required")

    candidate_totals = {
        candidate.name: {
            "candidate": {
                "filter": candidate.filter_name,
                "quantum": candidate.quantum,
                "phase": candidate.phase,
            },
            "exact_external_case_count": 0,
            "exact_wrist_case_count": 0,
            "exact_both_view_case_count": 0,
            "pair_comparison_count": 0,
            "changed_pixel_count": 0,
            "changed_pixel_fraction_sum": 0.0,
            "maximum_absolute_channel_difference": 0,
            "distortion_absolute_channel_sum": 0,
            "distortion_channel_count": 0,
            "maximum_distortion_absolute_channel_difference": 0,
        }
        for candidate in candidates
    }
    case_results: list[dict[str, Any]] = []

    for case in cases:
        reports = []
        raw_images: dict[str, list[np.ndarray]] = {view: [] for view in VIEWS}
        for root in run_roots:
            episode = root / case["case_id"]
            report = json.loads((episode / "task_report.json").read_text(encoding="utf-8"))
            if report.get("simulation_only") is not True:
                raise ValueError(f"report is not simulation-only: {episode}")
            if report.get("real_robot_command_sent") is not False:
                raise ValueError(f"report sent a real-robot command: {episode}")
            reports.append(report)
            for view in VIEWS:
                image, _ = exact_policy_image(episode, report, view)
                raw_images[view].append(image)

        baseline = {
            view: [preprocess(image) for image in raw_images[view]] for view in VIEWS
        }
        per_candidate: dict[str, Any] = {}
        for transform in candidates:
            view_exact: dict[str, bool] = {}
            per_view: dict[str, Any] = {}
            for view in VIEWS:
                processed = [
                    preprocess(apply_candidate(image, transform))
                    for image in raw_images[view]
                ]
                comparisons = [
                    pair_difference(processed[0], processed[index])
                    for index in range(1, len(processed))
                ]
                exact = all(item["exact"] for item in comparisons)
                view_exact[view] = exact
                total = candidate_totals[transform.name]
                total[f"exact_{view}_case_count"] += int(exact)
                for comparison in comparisons:
                    total["pair_comparison_count"] += 1
                    total["changed_pixel_count"] += comparison["changed_pixel_count"]
                    total["changed_pixel_fraction_sum"] += comparison[
                        "changed_pixel_fraction"
                    ]
                    total["maximum_absolute_channel_difference"] = max(
                        total["maximum_absolute_channel_difference"],
                        comparison["maximum_absolute_channel_difference"],
                    )
                distortions = []
                for original, transformed in zip(baseline[view], processed, strict=True):
                    difference = np.abs(
                        original.astype(np.int16) - transformed.astype(np.int16)
                    )
                    total["distortion_absolute_channel_sum"] += int(difference.sum())
                    total["distortion_channel_count"] += int(difference.size)
                    maximum = int(difference.max())
                    total["maximum_distortion_absolute_channel_difference"] = max(
                        total["maximum_distortion_absolute_channel_difference"], maximum
                    )
                    distortions.append(float(difference.mean()))
                per_view[view] = {
                    "exact_across_runs": exact,
                    "comparisons_to_run_zero": comparisons,
                    "mean_absolute_channel_distortion": float(np.mean(distortions)),
                }
            both_exact = all(view_exact.values())
            candidate_totals[transform.name]["exact_both_view_case_count"] += int(
                both_exact
            )
            per_candidate[transform.name] = {
                "exact_both_views_across_runs": both_exact,
                "views": per_view,
            }
        case_results.append(
            {
                "case_id": case["case_id"],
                "statuses": [report.get("status") for report in reports],
                "candidates": per_candidate,
            }
        )

    summaries = []
    for name, total in candidate_totals.items():
        pair_count = total.pop("pair_comparison_count")
        changed_fraction_sum = total.pop("changed_pixel_fraction_sum")
        distortion_sum = total.pop("distortion_absolute_channel_sum")
        distortion_count = total.pop("distortion_channel_count")
        summaries.append(
            {
                "name": name,
                **total,
                "pair_comparison_count": pair_count,
                "mean_changed_pixel_fraction": (
                    changed_fraction_sum / pair_count if pair_count else 0.0
                ),
                "mean_absolute_channel_distortion": (
                    distortion_sum / distortion_count if distortion_count else 0.0
                ),
            }
        )
    summaries.sort(
        key=lambda item: (
            -item["exact_both_view_case_count"],
            item["mean_changed_pixel_fraction"],
            item["mean_absolute_channel_distortion"],
        )
    )
    exact_candidates = [
        item
        for item in summaries
        if item["exact_both_view_case_count"] == len(cases)
    ]
    return {
        "status": "pass",
        "analysis_kind": "rm65_pi05_exact_policy_image_stabilization_screen_v1",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "case_count": len(cases),
        "run_count": len(run_roots),
        "candidate_count": len(candidates),
        "all_case_both_view_exact_candidate_count": len(exact_candidates),
        "recommended_candidate": exact_candidates[0]["name"] if exact_candidates else None,
        "candidate_summaries": summaries,
        "cases": case_results,
        "interpretation": (
            "This is an offline screen over the exact chunk-zero policy images. A transform "
            "must still pass live closed-loop A/B testing and distribution-shift checks before "
            "it can change the controller."
        ),
    }


def openpi_preprocessor(openpi_root: Path) -> Callable[[np.ndarray], np.ndarray]:
    sys.path.insert(0, str((openpi_root / "src").resolve()))
    from openpi.shared.image_tools import resize_with_pad

    return lambda image: np.asarray(resize_with_pad(image, 224, 224))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, action="append", required=True)
    parser.add_argument("--openpi-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    analysis = build_analysis(
        plan,
        args.run_root,
        openpi_preprocessor(args.openpi_root),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in analysis.items() if key != "cases"},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
