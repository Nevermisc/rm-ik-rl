#!/usr/bin/env python3
"""Find a light deterministic transform that removes RTX pixel jitter."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


SIZES = ((640, 480), (320, 240), (224, 168), (160, 120), (80, 60), (40, 30))
QUANTA = (1, 2, 4, 8, 16, 32, 64)
BLUR_RADII = (0, 1, 2, 4)


def read_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.uint8)


def canonicalize(
    image: np.ndarray, size: tuple[int, int], quantum: int, blur_radius: int
) -> np.ndarray:
    source = Image.fromarray(image, mode="RGB")
    if blur_radius:
        source = source.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    resized = np.asarray(source.resize(size, Image.Resampling.BOX), dtype=np.uint8)
    if quantum == 1:
        return resized
    values = resized.astype(np.uint16)
    quantized = ((values + quantum // 2) // quantum) * quantum
    return np.minimum(quantized, 255).astype(np.uint8)


def sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    first_dir = args.first.expanduser().resolve()
    second_dir = args.second.expanduser().resolve()
    first_metadata = json.loads((first_dir / "metadata.json").read_text(encoding="utf-8"))
    second_metadata = json.loads((second_dir / "metadata.json").read_text(encoding="utf-8"))

    cameras = {}
    joint_exact_candidates: set[tuple[int, int, int, int]] | None = None
    for camera in ("external", "wrist"):
        first = read_rgb(
            first_dir / first_metadata["image_paths"][camera][args.frame_index]
        )
        second = read_rgb(
            second_dir / second_metadata["image_paths"][camera][args.frame_index]
        )
        candidates = []
        exact_candidates = set()
        for width, height in SIZES:
            for blur_radius in BLUR_RADII:
                for quantum in QUANTA:
                    left = canonicalize(first, (width, height), quantum, blur_radius)
                    right = canonicalize(second, (width, height), quantum, blur_radius)
                    difference = np.abs(left.astype(np.int16) - right.astype(np.int16))
                    exact = bool(np.array_equal(left, right))
                    key = (width, height, quantum, blur_radius)
                    if exact:
                        exact_candidates.add(key)
                    candidates.append(
                        {
                            "width": width,
                            "height": height,
                            "quantum": quantum,
                            "blur_radius": blur_radius,
                            "exact_match": exact,
                            "different_element_count": int(np.count_nonzero(left != right)),
                            "maximum_absolute_difference": int(np.max(difference)),
                            "first_sha256": sha256(left),
                            "second_sha256": sha256(right),
                        }
                    )
        cameras[camera] = candidates
        joint_exact_candidates = (
            exact_candidates
            if joint_exact_candidates is None
            else joint_exact_candidates & exact_candidates
        )

    shared = sorted(
        joint_exact_candidates or set(),
        key=lambda item: (-item[0] * item[1], item[3], item[2]),
    )
    report = {
        "status": "pass" if shared else "no_exact_candidate",
        "validation_kind": "rm65_rtx_image_canonicalization_search",
        "simulation_only": True,
        "real_robot_command_sent": False,
        "frame_index": args.frame_index,
        "shared_exact_candidates": [
            {
                "width": width,
                "height": height,
                "quantum": quantum,
                "blur_radius": blur_radius,
            }
            for width, height, quantum, blur_radius in shared
        ],
        "cameras": cameras,
    }
    text = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cameras"}, indent=2))
    return 0 if shared else 1


if __name__ == "__main__":
    raise SystemExit(main())
