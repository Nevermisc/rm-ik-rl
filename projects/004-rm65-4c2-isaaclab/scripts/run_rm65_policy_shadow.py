#!/usr/bin/env python3
"""Run pi0.5 against live RM65 sensors in read-only shadow mode.

This program deliberately creates ROS subscriptions only. It records guarded
policy suggestions but contains no actuator message type and no command path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openpi_extension.real_robot_adapter import (  # noqa: E402
    guard_real_robot_action_chunk,
    interpolate_arm_targets,
)
from openpi_extension.shadow_runtime import (  # noqa: E402
    ShadowFreshnessConfig,
    build_shadow_observation,
    decode_ros_rgb_image,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-image-topic", required=True)
    parser.add_argument("--wrist-image-topic", required=True)
    parser.add_argument("--joint-topic", default="/joint_states")
    parser.add_argument("--gripper-normalized", type=float, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--policy-host", default="127.0.0.1")
    parser.add_argument("--policy-port", type=int, default=8000)
    parser.add_argument("--sample-rate-hz", type=float, default=2.0)
    parser.add_argument("--max-samples", type=int, default=20)
    parser.add_argument("--max-rejections", type=int, default=20)
    parser.add_argument("--max-age-seconds", type=float, default=0.25)
    parser.add_argument("--max-skew-seconds", type=float, default=0.10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sample_rate_hz <= 0 or args.max_samples < 1 or args.max_rejections < 1:
        parser.error("sample rate, max samples, and max rejections must be positive")
    if not 0.0 <= args.gripper_normalized <= 1.0:
        parser.error("--gripper-normalized must be inside [0, 1]")
    return args


def message_time(message, receive_time: float) -> float:
    stamp = message.header.stamp
    timestamp = float(stamp.sec) + float(stamp.nanosec) * 1e-9
    return timestamp if timestamp > 0 else receive_time


def image_sha256(image: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()


def main() -> int:
    args = parse_args()
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from sensor_msgs.msg import Image, JointState
        import websockets.sync.client as ws
    except ImportError as error:
        raise RuntimeError("source ROS 2 Jazzy and the OpenPI environment first") from error

    original_connect = ws.connect

    def connect_without_keepalive(*connect_args, **connect_kwargs):
        connect_kwargs["ping_interval"] = None
        return original_connect(*connect_args, **connect_kwargs)

    ws.connect = connect_without_keepalive
    from openpi_client.websocket_client_policy import WebsocketClientPolicy

    class ShadowNode(Node):
        def __init__(self) -> None:
            super().__init__("rm65_pi05_shadow")
            self.joint_record = None
            self.external_record = None
            self.wrist_record = None
            self.last_snapshot_time = None
            self.sample_count = 0
            self.failures = 0
            self.busy = False
            self.client = WebsocketClientPolicy(args.policy_host, args.policy_port)
            args.output.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
            self.output_stream = args.output.expanduser().resolve().open("w", encoding="utf-8")
            self.create_subscription(JointState, args.joint_topic, self.on_joint, qos_profile_sensor_data)
            self.create_subscription(Image, args.external_image_topic, self.on_external, qos_profile_sensor_data)
            self.create_subscription(Image, args.wrist_image_topic, self.on_wrist, qos_profile_sensor_data)
            self.timer = self.create_timer(1.0 / args.sample_rate_hz, self.on_timer)

        def now_seconds(self) -> float:
            return float(self.get_clock().now().nanoseconds) * 1e-9

        def on_joint(self, message) -> None:
            received = self.now_seconds()
            self.joint_record = (message, message_time(message, received))

        def on_external(self, message) -> None:
            received = self.now_seconds()
            self.external_record = (message, message_time(message, received))

        def on_wrist(self, message) -> None:
            received = self.now_seconds()
            self.wrist_record = (message, message_time(message, received))

        def write_record(self, record: dict) -> None:
            self.output_stream.write(json.dumps(record, separators=(",", ":")) + "\n")
            self.output_stream.flush()

        def on_timer(self) -> None:
            if self.busy or None in (self.joint_record, self.external_record, self.wrist_record):
                return
            newest = max(
                self.joint_record[1], self.external_record[1], self.wrist_record[1]
            )
            if self.last_snapshot_time is not None and newest <= self.last_snapshot_time:
                return
            self.last_snapshot_time = newest
            self.busy = True
            started = time.perf_counter()
            try:
                joint_message, joint_time = self.joint_record
                external_message, external_time = self.external_record
                wrist_message, wrist_time = self.wrist_record
                external_rgb = decode_ros_rgb_image(external_message)
                wrist_rgb = decode_ros_rgb_image(wrist_message)
                observation, sensor_report = build_shadow_observation(
                    joint_names=joint_message.name,
                    joint_positions=joint_message.position,
                    external_rgb=external_rgb,
                    wrist_rgb=wrist_rgb,
                    joint_timestamp=joint_time,
                    external_timestamp=external_time,
                    wrist_timestamp=wrist_time,
                    now=self.now_seconds(),
                    gripper_normalized=args.gripper_normalized,
                    prompt=args.prompt,
                    config=ShadowFreshnessConfig(
                        max_age_seconds=args.max_age_seconds,
                        max_skew_seconds=args.max_skew_seconds,
                    ),
                )
                predicted = np.asarray(self.client.infer(observation)["actions"], dtype=np.float32)
                guarded, guard_report = guard_real_robot_action_chunk(
                    predicted, observation["observation/joint_position"]
                )
                stream_times, stream_targets = interpolate_arm_targets(
                    guarded[:, :6], observation["observation/joint_position"]
                )
                self.sample_count += 1
                self.write_record(
                    {
                        "status": "pass",
                        "mode": "read_only_policy_shadow",
                        "real_robot_command_sent": False,
                        "ros_publishers_created": 0,
                        "sample_index": self.sample_count - 1,
                        "inference_seconds": time.perf_counter() - started,
                        "sensor": sensor_report,
                        "image_sha256": {
                            "external": image_sha256(external_rgb),
                            "wrist": image_sha256(wrist_rgb),
                        },
                        "predicted_action_shape": list(predicted.shape),
                        "first_predicted_action": predicted[0].tolist(),
                        "first_guarded_action": guarded[0].tolist(),
                        "guard": guard_report,
                        "driver_stream": {
                            "point_count": len(stream_times),
                            "duration_seconds": float(stream_times[-1]),
                            "maximum_joint_step_rad": float(
                                np.max(
                                    np.abs(
                                        np.diff(
                                            np.vstack(
                                                [
                                                    observation["observation/joint_position"],
                                                    stream_targets,
                                                ]
                                            ),
                                            axis=0,
                                        )
                                    )
                                )
                            ),
                        },
                    }
                )
                if self.sample_count >= args.max_samples:
                    rclpy.shutdown()
            except Exception as error:
                self.failures += 1
                self.write_record(
                    {
                        "status": "rejected",
                        "mode": "read_only_policy_shadow",
                        "real_robot_command_sent": False,
                        "ros_publishers_created": 0,
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                )
                if self.failures >= args.max_rejections:
                    rclpy.shutdown()
            finally:
                self.busy = False

        def close(self) -> None:
            self.output_stream.close()
            self.client._ws.close()

    rclpy.init()
    node = ShadowNode()
    try:
        rclpy.spin(node)
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    print(
        json.dumps(
            {
                "status": "pass" if node.sample_count == args.max_samples else "incomplete",
                "mode": "read_only_policy_shadow",
                "real_robot_command_sent": False,
                "ros_publishers_created": 0,
                "accepted_samples": node.sample_count,
                "rejected_samples": node.failures,
                "output": str(args.output.expanduser().resolve()),
            },
            indent=2,
        )
    )
    return 0 if node.sample_count == args.max_samples else 1


if __name__ == "__main__":
    raise SystemExit(main())
