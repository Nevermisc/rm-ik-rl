"""Pure validation helpers for the read-only RM65 policy shadow runtime."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence

import numpy as np

from openpi_extension.real_robot_adapter import extract_ordered_joint_positions


@dataclass(frozen=True)
class ShadowFreshnessConfig:
    max_age_seconds: float = 0.25
    max_skew_seconds: float = 0.10
    max_future_seconds: float = 0.05


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def decode_ros_rgb_image(message: Any) -> np.ndarray:
    """Decode an uncompressed ROS Image without depending on cv_bridge."""

    height = int(message.height)
    width = int(message.width)
    step = int(message.step)
    encoding = str(message.encoding).lower()
    if height <= 0 or width <= 0:
        raise ValueError("image dimensions must be positive")
    if encoding not in {"rgb8", "bgr8"}:
        raise ValueError(f"only rgb8 and bgr8 are supported, got {encoding!r}")
    row_bytes = width * 3
    if step < row_bytes:
        raise ValueError("image step is shorter than width * 3")
    raw = np.frombuffer(message.data, dtype=np.uint8)
    required = height * step
    if raw.size < required:
        raise ValueError(f"image buffer has {raw.size} bytes, expected at least {required}")
    rgb = raw[:required].reshape(height, step)[:, :row_bytes].reshape(height, width, 3)
    if encoding == "bgr8":
        rgb = rgb[..., ::-1]
    return np.ascontiguousarray(rgb)


def build_shadow_observation(
    *,
    joint_names: Sequence[str],
    joint_positions: Sequence[float],
    external_rgb: np.ndarray,
    wrist_rgb: np.ndarray,
    joint_timestamp: float,
    external_timestamp: float,
    wrist_timestamp: float,
    now: float,
    gripper_normalized: float,
    prompt: str,
    config: ShadowFreshnessConfig = ShadowFreshnessConfig(),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate one synchronized read-only sensor snapshot for pi0.5."""

    if config.max_age_seconds <= 0 or config.max_skew_seconds < 0:
        raise ValueError("freshness limits must be positive")
    arm = extract_ordered_joint_positions(joint_names, joint_positions)
    images = {
        "external": np.asarray(external_rgb),
        "wrist": np.asarray(wrist_rgb),
    }
    for name, image in images.items():
        if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
            raise ValueError(f"{name} image must be uint8 HxWx3, got {image.dtype} {image.shape}")
        if image.shape[0] < 2 or image.shape[1] < 2:
            raise ValueError(f"{name} image is too small: {image.shape}")

    timestamps = np.asarray(
        [joint_timestamp, external_timestamp, wrist_timestamp], dtype=np.float64
    )
    if not np.isfinite(timestamps).all() or not np.isfinite(now):
        raise ValueError("sensor timestamps and now must be finite")
    ages = float(now) - timestamps
    if np.min(ages) < -config.max_future_seconds:
        raise ValueError("sensor timestamp is unexpectedly in the future")
    if np.max(ages) > config.max_age_seconds:
        raise ValueError("sensor snapshot is stale")
    skew = float(np.max(timestamps) - np.min(timestamps))
    if skew > config.max_skew_seconds:
        raise ValueError("sensor snapshot exceeds the allowed time skew")

    gripper = float(gripper_normalized)
    if not np.isfinite(gripper) or not 0.0 <= gripper <= 1.0:
        raise ValueError("gripper state must be finite and inside [0, 1]")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")

    observation = {
        "observation/joint_position": arm,
        "observation/gripper_position": np.asarray([gripper], dtype=np.float32),
        "observation/external_image": images["external"],
        "observation/wrist_image": images["wrist"],
        "prompt": prompt.strip(),
    }
    report = {
        "joint_age_seconds": float(ages[0]),
        "external_image_age_seconds": float(ages[1]),
        "wrist_image_age_seconds": float(ages[2]),
        "sensor_skew_seconds": skew,
        "joint_order": list(joint_names),
        "external_image_shape": list(images["external"].shape),
        "wrist_image_shape": list(images["wrist"].shape),
        "gripper_state_source": "operator_confirmed_static_value",
    }
    return observation, report


def validate_shadow_records(
    records: Sequence[dict[str, Any]], *, minimum_samples: int = 20
) -> dict[str, Any]:
    """Fail closed unless a complete read-only policy shadow run is valid."""

    if minimum_samples < 1:
        raise ValueError("minimum_samples must be positive")
    accepted = [record for record in records if record.get("status") == "pass"]
    rejected = [record for record in records if record.get("status") != "pass"]
    expected_indexes = list(range(len(accepted)))

    def finite_vector(value: Any, size: int) -> bool:
        try:
            array = np.asarray(value, dtype=np.float64)
        except (TypeError, ValueError):
            return False
        return array.shape == (size,) and bool(np.isfinite(array).all())

    def bounded_number(value: Any, lower: float, upper: float) -> bool:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        return bool(np.isfinite(number) and lower <= number <= upper)

    checks = {
        "minimum_sample_count": len(accepted) >= minimum_samples,
        "no_rejected_samples": not rejected,
        "sample_indexes_contiguous": [record.get("sample_index") for record in accepted]
        == expected_indexes,
        "read_only_mode": all(
            record.get("mode") == "read_only_policy_shadow" for record in accepted
        ),
        "no_real_robot_commands": all(
            record.get("real_robot_command_sent") is False for record in accepted
        ),
        "no_ros_publishers": all(
            record.get("ros_publishers_created") == 0 for record in accepted
        ),
        "action_shapes": all(
            record.get("predicted_action_shape") == [10, 7] for record in accepted
        ),
        "finite_first_actions": all(
            finite_vector(record.get("first_predicted_action"), 7)
            and finite_vector(record.get("first_guarded_action"), 7)
            for record in accepted
        ),
        "fresh_sensor_ages": all(
            bounded_number(record.get("sensor", {}).get(field), -0.050001, 0.250001)
            for record in accepted
            for field in (
                "joint_age_seconds",
                "external_image_age_seconds",
                "wrist_image_age_seconds",
            )
        ),
        "sensor_skew_bounded": all(
            bounded_number(
                record.get("sensor", {}).get("sensor_skew_seconds"), 0.0, 0.100001
            )
            for record in accepted
        ),
        "image_hashes_valid": all(
            bool(_SHA256.fullmatch(str(record.get("image_sha256", {}).get(view, ""))))
            for record in accepted
            for view in ("external", "wrist")
        ),
        "driver_stream_contract": all(
            record.get("driver_stream", {}).get("point_count") == 25
            and bounded_number(
                record.get("driver_stream", {}).get("duration_seconds"),
                0.5 - 1e-6,
                0.5 + 1e-6,
            )
            and bounded_number(
                record.get("driver_stream", {}).get("maximum_joint_step_rad"),
                0.0,
                0.0041,
            )
            for record in accepted
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "format": "rm65_policy_shadow_validation_v1",
        "status": "pass" if not failed else "blocked",
        "policy_shadow_passed": not failed,
        "read_only": True,
        "real_robot_command_sent": False,
        "minimum_samples": minimum_samples,
        "accepted_samples": len(accepted),
        "rejected_samples": len(rejected),
        "checks": checks,
        "failed_checks": failed,
    }
