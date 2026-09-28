#!/usr/bin/env python3
"""Diagnose release timing in deterministic RM65 pi0.5 evaluation failures."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ACTUAL_GRIPPER_THRESHOLDS = (0.12, 0.15, 0.20, 0.25, 0.30)
REQUIRED_CANDIDATE_STREAKS = (1, 2, 3)


def load_chunks(log_path: Path) -> list[dict]:
    chunks = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("PI05_CHUNK="):
            chunks.append(json.loads(line.removeprefix("PI05_CHUNK=")))
    return chunks


def minimum_with_location(chunks: list[dict], key: str) -> tuple[float | None, int | None]:
    candidates = [
        (float(chunk[key]), int(chunk["index"]))
        for chunk in chunks
        if isinstance(chunk.get(key), (int, float))
    ]
    return min(candidates) if candidates else (None, None)


def maximum_candidate_streak(
    chunks: list[dict], actual_threshold: float, command_threshold: float
) -> int:
    maximum = 0
    current = 0
    for chunk in chunks:
        candidate = bool(
            chunk.get("lifted") is True
            and isinstance(chunk.get("target_error_m"), (int, float))
            and float(chunk["target_error_m"]) < 0.05
            and isinstance(chunk.get("actual_gripper_normalized"), (int, float))
            and float(chunk["actual_gripper_normalized"]) < actual_threshold
            and isinstance(chunk.get("last_executed_gripper_target"), (int, float))
            and float(chunk["last_executed_gripper_target"]) < command_threshold
        )
        current = current + 1 if candidate else 0
        maximum = max(maximum, current)
    return maximum


def classify_failure(report: dict, chunks: list[dict], threshold: float) -> tuple[str, dict]:
    preflight = report.get("preflight_failure")
    if isinstance(preflight, dict):
        return "preflight_safety_rejection", {
            "preflight_failure": preflight,
            "minimum_target_error_m": None,
            "minimum_target_error_chunk": None,
            "near_target_chunk_count": 0,
            "maximum_consecutive_release_candidate_chunks": 0,
            "release_signals_near_target": [],
        }
    minimum_target_error, minimum_target_error_chunk = minimum_with_location(
        chunks, "target_error_m"
    )
    near_target = [
        chunk
        for chunk in chunks
        if isinstance(chunk.get("target_error_m"), (int, float))
        and float(chunk["target_error_m"]) < 0.05
    ]
    release_signals = []
    for chunk in near_target:
        sampling = chunk.get("policy_sampling", {})
        safe_targets = sampling.get("safe_gripper_targets", [])
        execute_count = int(sampling.get("executed_action_count", 0))
        executed = safe_targets[:execute_count]
        unexecuted = safe_targets[execute_count:]
        release_signals.append(
            {
                "chunk_index": chunk.get("index"),
                "target_error_m": chunk.get("target_error_m"),
                "executed_min_gripper_target": min(executed) if executed else None,
                "unexecuted_min_gripper_target": min(unexecuted) if unexecuted else None,
                "executed_release_signal": any(value < threshold for value in executed),
                "unexecuted_release_signal": any(value < threshold for value in unexecuted),
            }
        )

    maximum_release_streak = maximum_candidate_streak(chunks, threshold, threshold)

    lifted = float(report.get("block_lift_height_m", 0.0)) > 0.02
    if not lifted:
        category = "insufficient_lift"
    elif minimum_target_error is None or minimum_target_error >= 0.05:
        category = "never_reached_target"
    elif maximum_release_streak == 2:
        category = "two_chunk_release_candidate_not_latched"
    elif maximum_release_streak == 1:
        category = "one_chunk_release_candidate_not_latched"
    elif any(item["executed_release_signal"] for item in release_signals):
        category = "executed_release_not_verified"
    elif any(item["unexecuted_release_signal"] for item in release_signals):
        category = "release_only_in_unexecuted_tail"
    else:
        category = "no_release_signal_near_target"

    return category, {
        "minimum_target_error_m": minimum_target_error,
        "minimum_target_error_chunk": minimum_target_error_chunk,
        "near_target_chunk_count": len(near_target),
        "maximum_consecutive_release_candidate_chunks": maximum_release_streak,
        "release_signals_near_target": release_signals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--episode-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gripper-open-threshold", type=float, default=0.12)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    safety_aborts: Counter[str] = Counter()
    gate_sweep_counts = {
        f"actual_lt_{actual_threshold:.2f}": {
            f"required_{required}": 0 for required in REQUIRED_CANDIDATE_STREAKS
        }
        for actual_threshold in ACTUAL_GRIPPER_THRESHOLDS
    }
    cases = []
    for case in plan["cases"]:
        case_dir = args.episode_root / case["case_id"]
        report = json.loads((case_dir / "task_report.json").read_text(encoding="utf-8"))
        chunks = load_chunks(case_dir / "runner.log")
        for actual_threshold in ACTUAL_GRIPPER_THRESHOLDS:
            streak = maximum_candidate_streak(
                chunks, actual_threshold, args.gripper_open_threshold
            )
            for required in REQUIRED_CANDIDATE_STREAKS:
                if streak >= required:
                    gate_sweep_counts[f"actual_lt_{actual_threshold:.2f}"][
                        f"required_{required}"
                    ] += 1
        if report.get("status") == "pass":
            category = "pass"
            detail = {}
        else:
            category, detail = classify_failure(
                report, chunks, args.gripper_open_threshold
            )
        counts[category] += 1
        abort_reason = report.get("simulation_safety_abort_reason")
        if abort_reason is not None:
            safety_aborts[str(abort_reason)] += 1
        cases.append(
            {
                "case_id": case["case_id"],
                "status": report.get("status"),
                "category": category,
                "simulation_safety_abort_reason": abort_reason,
                "action_chunks": report.get("action_chunks"),
                "block_lift_height_m": report.get("block_lift_height_m"),
                **detail,
            }
        )

    result = {
        "status": "pass",
        "analysis_kind": "rm65_pi05_deterministic_release_failure_analysis",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "planned_case_count": len(plan["cases"]),
        "analyzed_case_count": len(cases),
        "gripper_open_threshold": args.gripper_open_threshold,
        "category_counts": dict(sorted(counts.items())),
        "simulation_safety_abort_counts": dict(sorted(safety_aborts.items())),
        "release_gate_candidate_case_counts": gate_sweep_counts,
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
