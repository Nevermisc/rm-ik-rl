#!/usr/bin/env python3
"""Compare exact first policy observations and their downstream RM65 actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image


VIEWS = ("external", "wrist")
FINAL_METRICS = (
    "block_lift_height_m",
    "final_target_position_error_m",
    "final_gripper_normalized",
    "post_release_drift_m",
)


def array_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def load_report(episode_dir: Path) -> dict[str, Any]:
    value = json.loads((episode_dir / "task_report.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"task report must be an object: {episode_dir}")
    return value


def exact_policy_image(
    episode_dir: Path,
    report: dict[str, Any],
    view: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    evidence = report.get("initial_policy_observation")
    if not isinstance(evidence, dict) or evidence.get("chunk_index") != 0:
        raise ValueError(f"missing exact initial policy observation: {episode_dir}")
    info = evidence.get(f"{view}_image")
    if not isinstance(info, dict) or not isinstance(info.get("path"), str):
        raise ValueError(f"missing {view} image evidence: {episode_dir}")
    path = (episode_dir / info["path"]).resolve()
    root = episode_dir.resolve()
    if root not in path.parents:
        raise ValueError(f"policy observation escapes episode directory: {path}")
    image = np.asarray(Image.open(path).convert("RGB"))
    chunk_zero = report.get("deterministic_sampling", {}).get("chunks", [{}])[0]
    chunk_hash = chunk_zero.get("observation_sha256", {}).get(f"{view}_image")
    decoded_hash = array_sha256(image)
    checks = {
        "shape_matches": list(image.shape) == info.get("shape"),
        "dtype_matches": str(image.dtype) == info.get("dtype"),
        "saved_hash_matches": decoded_hash == info.get("sha256"),
        "chunk_zero_hash_matches": decoded_hash == chunk_hash,
    }
    if not all(checks.values()):
        raise ValueError(f"invalid exact {view} image evidence in {episode_dir}: {checks}")
    return image, {"path": str(path), "sha256": decoded_hash, "checks": checks}


def image_difference(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    if reference.shape != candidate.shape:
        raise ValueError(f"image shapes differ: {reference.shape} != {candidate.shape}")
    reference_i16 = reference.astype(np.int16)
    candidate_i16 = candidate.astype(np.int16)
    difference = np.abs(reference_i16 - candidate_i16)
    pixel_max = difference.max(axis=2)
    changed = pixel_max > 0
    y_indices, x_indices = np.nonzero(changed)
    bbox = (
        None
        if len(x_indices) == 0
        else [
            int(x_indices.min()),
            int(y_indices.min()),
            int(x_indices.max()),
            int(y_indices.max()),
        ]
    )
    mean_squared_error = float(
        np.mean((reference.astype(np.float64) - candidate.astype(np.float64)) ** 2)
    )
    psnr = (
        None
        if mean_squared_error == 0.0
        else 20.0 * math.log10(255.0 / math.sqrt(mean_squared_error))
    )
    return {
        "shape": list(reference.shape),
        "exact_match": bool(np.array_equal(reference, candidate)),
        "changed_pixel_count": int(changed.sum()),
        "changed_pixel_fraction": float(changed.mean()),
        "mean_absolute_channel_difference": float(difference.mean()),
        "maximum_absolute_channel_difference": int(difference.max()),
        "psnr_db": psnr,
        "pixels_with_max_channel_difference_ge_2": int((pixel_max >= 2).sum()),
        "pixels_with_max_channel_difference_ge_4": int((pixel_max >= 4).sum()),
        "pixels_with_max_channel_difference_ge_8": int((pixel_max >= 8).sum()),
        "changed_pixel_bbox_xyxy": bbox,
    }


def first_chunk_actions(episode_dir: Path) -> np.ndarray:
    metadata = json.loads((episode_dir / "metadata.json").read_text(encoding="utf-8"))
    phase_names = metadata.get("phase_names")
    if not isinstance(phase_names, list):
        raise ValueError(f"missing phase_names: {episode_dir}")
    with np.load(episode_dir / "episode.npz", allow_pickle=False) as episode:
        phase_ids = episode["phase_id"]
        action = episode["action"]
        indices = [
            index
            for index, phase_id in enumerate(phase_ids)
            if str(phase_names[int(phase_id)]).startswith("PI05_CHUNK_000_ACTION_")
        ]
        if not indices:
            raise ValueError(f"episode has no first policy action chunk: {episode_dir}")
        return np.asarray(action[indices], dtype=np.float32)


def numeric_difference(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    if reference.shape != candidate.shape:
        raise ValueError(f"numeric shapes differ: {reference.shape} != {candidate.shape}")
    difference = np.abs(reference.astype(np.float64) - candidate.astype(np.float64))
    return {
        "shape": list(reference.shape),
        "exact_match": bool(np.array_equal(reference, candidate)),
        "mean_absolute_difference": float(difference.mean()),
        "maximum_absolute_difference": float(difference.max()),
        "per_action_dimension_maximum_absolute_difference": difference.max(axis=0).tolist(),
    }


def openpi_preprocessor(openpi_root: Path | None) -> Callable[[np.ndarray], np.ndarray] | None:
    if openpi_root is None:
        return None
    source_root = (openpi_root / "src").resolve()
    sys.path.insert(0, str(source_root))
    from openpi.shared.image_tools import resize_with_pad

    def preprocess(image: np.ndarray) -> np.ndarray:
        return np.asarray(resize_with_pad(image, 224, 224))

    return preprocess


def build_analysis(
    reference_dir: Path,
    candidate_dir: Path,
    preprocess: Callable[[np.ndarray], np.ndarray] | None = None,
) -> dict[str, Any]:
    reference_report = load_report(reference_dir)
    candidate_report = load_report(candidate_dir)
    image_results: dict[str, Any] = {}
    evidence_checks: dict[str, Any] = {}
    for view in VIEWS:
        reference_image, reference_evidence = exact_policy_image(
            reference_dir, reference_report, view
        )
        candidate_image, candidate_evidence = exact_policy_image(
            candidate_dir, candidate_report, view
        )
        comparison = {"render_480x640": image_difference(reference_image, candidate_image)}
        if preprocess is not None:
            comparison["model_input_224x224"] = image_difference(
                preprocess(reference_image), preprocess(candidate_image)
            )
        image_results[view] = comparison
        evidence_checks[view] = {
            "reference": reference_evidence,
            "candidate": candidate_evidence,
        }

    reference_chunk = reference_report["deterministic_sampling"]["chunks"][0]
    candidate_chunk = candidate_report["deterministic_sampling"]["chunks"][0]
    reference_actions = first_chunk_actions(reference_dir)
    candidate_actions = first_chunk_actions(candidate_dir)
    return {
        "status": "pass",
        "analysis_kind": "rm65_pi05_exact_initial_policy_observation_repeatability",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "reference_episode": str(reference_dir.resolve()),
        "candidate_episode": str(candidate_dir.resolve()),
        "exact_capture_evidence_verified": True,
        "model_preprocessing_applied": preprocess is not None,
        "reference_status": reference_report.get("status"),
        "candidate_status": candidate_report.get("status"),
        "outcome_match": reference_report.get("status") == candidate_report.get("status"),
        "chunk_zero_noise_hash_match": (
            reference_chunk.get("noise_sha256") == candidate_chunk.get("noise_sha256")
        ),
        "chunk_zero_raw_action_hash_match": (
            reference_chunk.get("raw_action_sha256")
            == candidate_chunk.get("raw_action_sha256")
        ),
        "images": image_results,
        "executed_first_chunk_action_difference": numeric_difference(
            reference_actions, candidate_actions
        ),
        "final_metrics": {
            "reference": {key: reference_report.get(key) for key in FINAL_METRICS},
            "candidate": {key: candidate_report.get(key) for key in FINAL_METRICS},
        },
        "evidence_checks": evidence_checks,
        "interpretation": (
            "The exact policy images can differ by sparse low-amplitude pixels even when "
            "the initial proprioception and explicit noise seed match; closed-loop feedback "
            "can amplify the resulting action differences."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-episode", type=Path, required=True)
    parser.add_argument("--candidate-episode", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--openpi-root",
        type=Path,
        help="Optional OpenPI checkout; when present, apply its exact 224x224 resize_with_pad.",
    )
    args = parser.parse_args()
    analysis = build_analysis(
        args.reference_episode,
        args.candidate_episode,
        openpi_preprocessor(args.openpi_root),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in analysis.items() if key != "evidence_checks"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
