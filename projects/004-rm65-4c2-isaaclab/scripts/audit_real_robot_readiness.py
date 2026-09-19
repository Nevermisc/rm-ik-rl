#!/usr/bin/env python3
"""Read-only RM65-B + 4C2 deployment prerequisite audit."""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def yaml_scalar(text: str, name: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(name)}:\s*[\"']?([^\"'#\s]+)", text, re.MULTILINE)
    return match.group(1) if match else None


def yaml_list(text: str, name: str) -> list[str] | None:
    match = re.search(rf"^\s*{re.escape(name)}:\s*\[([^]]+)]", text, re.MULTILINE)
    if not match:
        return None
    return [item.strip().strip("\"'") for item in match.group(1).split(",")]


def main() -> int:
    home = Path.home()
    default_project = home / "robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=default_project)
    parser.add_argument(
        "--driver-config",
        type=Path,
        default=home
        / "robot-learning/third_party/ros2_rm_robot_jazzy/rm_driver/config/rm_65_config.yaml",
    )
    parser.add_argument("--network-interface", default="enp4s0")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve()
    sys.path.insert(0, str(project_root))
    from openpi_extension.real_robot_adapter import (  # noqa: PLC0415
        validate_gripper_calibration,
    )

    driver_config = args.driver_config.expanduser().resolve()
    driver_text = driver_config.read_text(encoding="utf-8")
    arm_ip = yaml_scalar(driver_text, "arm_ip")
    udp_ip = yaml_scalar(driver_text, "udp_ip")
    arm_joints = yaml_list(driver_text, "arm_joints")

    ip_result = run(["ip", "-j", "address", "show", "dev", args.network_interface])
    interface_data: dict[str, Any] | None = None
    if ip_result["returncode"] == 0:
        parsed = json.loads(ip_result["stdout"] or "[]")
        interface_data = parsed[0] if parsed else None
    ipv4_addresses = [
        entry["local"]
        for entry in (interface_data or {}).get("addr_info", [])
        if entry.get("family") == "inet"
    ]
    expected_network = (
        ipaddress.ip_network(f"{udp_ip}/24", strict=False) if udp_ip is not None else None
    )
    ipv4_in_expected_subnet = bool(
        expected_network
        and any(ipaddress.ip_address(address) in expected_network for address in ipv4_addresses)
    )
    ping_result: dict[str, Any] | None = None
    controller_reachable = False
    if arm_ip and ipv4_in_expected_subnet:
        ping_result = run(["ping", "-c", "1", "-W", "1", arm_ip])
        controller_reachable = ping_result["returncode"] == 0

    usb_result = run(["lsusb"])
    video_devices = sorted(str(path) for path in Path("/dev").glob("video*"))
    realsense_detected = "RealSense" in usb_result["stdout"]
    rm_driver_prefix = home / "robot-learning/rm_moveit2_jazzy_ws/install/rm_driver"
    calibration_path = project_root / "config/rm65_4c2_gripper_calibration_template.json"
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    calibration_report = validate_gripper_calibration(calibration)

    checks = {
        "driver_config_exists": driver_config.is_file(),
        "driver_arm_type_rm65": yaml_scalar(driver_text, "arm_type") == "RM_65",
        "driver_six_dof": yaml_scalar(driver_text, "arm_dof") == "6",
        "joint_order_exact": arm_joints
        == ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"],
        "ros2_rm_driver_installed": rm_driver_prefix.is_dir(),
        "wired_interface_exists": interface_data is not None,
        "wired_interface_up": "UP" in (interface_data or {}).get("flags", []),
        "wired_ipv4_configured": bool(ipv4_addresses),
        "wired_ipv4_matches_udp_subnet": ipv4_in_expected_subnet,
        "controller_ping_reachable": controller_reachable,
        "realsense_usb_detected": realsense_detected,
        "video_devices_present": bool(video_devices),
        "gripper_calibration_verified": calibration_report["status"] == "pass",
        "external_camera_calibrated": False,
        "wrist_camera_calibrated": False,
        "physical_emergency_stop_verified": False,
        "human_supervisor_ready": False,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    report = {
        "format": "rm65_real_robot_readiness_audit_v1",
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "pass" if not blockers else "blocked",
        "read_only": True,
        "real_robot_command_sent": False,
        "checks": checks,
        "blockers": blockers,
        "driver": {
            "config": str(driver_config),
            "arm_ip": arm_ip,
            "udp_ip": udp_ip,
            "arm_joints": arm_joints,
            "ros2_prefix": str(rm_driver_prefix),
        },
        "network": {
            "interface": args.network_interface,
            "flags": (interface_data or {}).get("flags", []),
            "ipv4_addresses": ipv4_addresses,
            "expected_subnet": str(expected_network) if expected_network else None,
            "ping": ping_result,
        },
        "vision": {
            "video_devices": video_devices,
            "lsusb": usb_result,
            "note": "Two calibrated RGB streams are required by the current policy contract.",
        },
        "gripper": {
            "calibration_path": str(calibration_path),
            "validation": calibration_report,
        },
        "manual_checks": {
            "external_camera_calibrated": "Must be measured on the physical installation.",
            "wrist_camera_calibrated": "Must be measured on the physical installation.",
            "physical_emergency_stop_verified": "Must be demonstrated before motion.",
            "human_supervisor_ready": "Must be confirmed immediately before first motion.",
        },
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
