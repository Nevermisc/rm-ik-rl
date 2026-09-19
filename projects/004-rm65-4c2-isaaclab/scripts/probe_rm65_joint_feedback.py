#!/usr/bin/env python3
"""Subscribe to RM65 joint feedback and write a read-only validation report."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np


EXPECTED_JOINTS = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
LOWER_RAD = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])
UPPER_RAD = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])


def analyze_samples(
    samples: list[dict[str, Any]], *, minimum_samples: int, minimum_rate_hz: float
) -> dict[str, Any]:
    names_exact = bool(samples) and all(item["name"] == EXPECTED_JOINTS for item in samples)
    positions = [np.asarray(item["position"], dtype=np.float64) for item in samples]
    shape_exact = bool(positions) and all(value.shape == (6,) for value in positions)
    finite = shape_exact and all(np.isfinite(value).all() for value in positions)
    within_limits = finite and all(
        np.all(value >= LOWER_RAD) and np.all(value <= UPPER_RAD) for value in positions
    )
    arrival_times = [float(item["arrival_monotonic_s"]) for item in samples]
    monotonic = len(arrival_times) < 2 or all(
        right > left for left, right in zip(arrival_times[:-1], arrival_times[1:], strict=True)
    )
    span_s = arrival_times[-1] - arrival_times[0] if len(arrival_times) >= 2 else 0.0
    rate_hz = (len(arrival_times) - 1) / span_s if span_s > 0 else 0.0
    checks = {
        "minimum_sample_count": len(samples) >= minimum_samples,
        "joint_names_exact": names_exact,
        "six_positions_per_sample": shape_exact,
        "positions_finite": finite,
        "positions_within_rm65_limits": within_limits,
        "arrival_times_monotonic": monotonic,
        "minimum_feedback_rate": rate_hz >= minimum_rate_hz,
    }
    return {
        "status": "pass" if all(checks.values()) else "blocked",
        "read_only": True,
        "real_robot_command_sent": False,
        "topic": "/joint_states",
        "publishers_created": [],
        "sample_count": len(samples),
        "span_s": span_s,
        "estimated_rate_hz": rate_hz,
        "expected_joint_names": EXPECTED_JOINTS,
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "first_sample": samples[0] if samples else None,
        "last_sample": samples[-1] if samples else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="/joint_states")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--minimum-samples", type=int, default=20)
    parser.add_argument("--minimum-rate-hz", type=float, default=20.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.timeout_seconds <= 0 or args.minimum_samples < 2 or args.minimum_rate_hz <= 0:
        raise ValueError("timeout/rate must be positive and minimum samples must be at least two")

    try:
        import rclpy
        from rclpy.node import Node
        from sensor_msgs.msg import JointState
    except ImportError as exc:
        raise RuntimeError(
            "ROS2 Python is unavailable; source /opt/ros/jazzy/setup.bash and the RM65 workspace"
        ) from exc

    samples: list[dict[str, Any]] = []

    class FeedbackProbe(Node):
        def __init__(self) -> None:
            super().__init__("rm65_read_only_feedback_probe")
            self.subscription = self.create_subscription(
                JointState, args.topic, self.on_joint_state, 10
            )

        def on_joint_state(self, message: JointState) -> None:
            samples.append(
                {
                    "arrival_monotonic_s": time.monotonic(),
                    "name": list(message.name),
                    "position": list(message.position),
                    "header_stamp_s": float(message.header.stamp.sec)
                    + float(message.header.stamp.nanosec) * 1e-9,
                }
            )

    rclpy.init(args=None)
    node = FeedbackProbe()
    started = time.monotonic()
    try:
        while len(samples) < args.minimum_samples and time.monotonic() - started < args.timeout_seconds:
            rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        node.destroy_node()
        rclpy.shutdown()

    report = analyze_samples(
        samples,
        minimum_samples=args.minimum_samples,
        minimum_rate_hz=args.minimum_rate_hz,
    )
    report["topic"] = args.topic
    report["timeout_seconds"] = args.timeout_seconds
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
