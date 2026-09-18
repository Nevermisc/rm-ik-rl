#!/usr/bin/env python3
"""Read-only acceptance audit for the migrated RM65 lab computer.

The script never connects to, enables, or commands the physical robot.  It checks
the host software stack and consumes machine-readable evidence produced by the
IsaacLab and OpenPI smoke tests.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
from typing import Any


HOME = pathlib.Path.home()
DEFAULT_OUTPUT = (
    HOME
    / "robot-learning/rm-ik-rl/projects/004-rm65-4c2-isaaclab/results"
    / "new_lab_pc_migration_audit.json"
)
MIGRATION_LOGS = HOME / "migration_logs"


def run(*command: str, timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}


def command_check(name: str, *command: str, timeout: int = 30) -> dict[str, Any]:
    result = run(*command, timeout=timeout)
    result["name"] = name
    result["command"] = list(command)
    return result


def path_check(path: pathlib.Path, *, kind: str = "any") -> dict[str, Any]:
    if kind == "dir":
        exists = path.is_dir()
    elif kind == "file":
        exists = path.is_file()
    else:
        exists = path.exists()
    return {
        "ok": exists,
        "path": str(path),
        "kind": kind,
        "is_symlink": path.is_symlink(),
        "resolved_path": str(path.resolve()) if exists else None,
    }


def evidence_check(path: pathlib.Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "ok": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        result["reported_status"] = payload.get("status")
        result["ok"] = payload.get("status") == "pass"
        for field in (
            "simulation_only",
            "dof_count",
            "all_values_finite",
            "all_joint_positions_finite",
            "bilateral_fingertip_contact_confirmed",
            "actions_shape",
            "all_actions_finite",
        ):
            if field in payload:
                result[field] = payload[field]
    except (OSError, json.JSONDecodeError) as exc:
        result["error"] = str(exc)
    return result


def text_marker(path: pathlib.Path, marker: str) -> dict[str, Any]:
    try:
        found = marker in path.read_text(encoding="utf-8", errors="replace")
        return {"ok": found, "path": str(path), "marker": marker}
    except OSError as exc:
        return {"ok": False, "path": str(path), "marker": marker, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    os_release: dict[str, str] = {}
    release_path = pathlib.Path("/etc/os-release")
    if release_path.exists():
        for line in release_path.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                os_release[key] = value.strip('"')

    paths = {
        "project_repository": path_check(HOME / "robot-learning/rm-ik-rl", kind="dir"),
        "openpi_repository": path_check(HOME / "robot-learning/openpi", kind="dir"),
        "isaaclab_repository": path_check(HOME / "robot-learning/IsaacLab", kind="dir"),
        "isaac_sim": path_check(HOME / "isaac-sim-5.1.0", kind="dir"),
        "openpi_assets": path_check(HOME / ".cache/openpi", kind="dir"),
        "openpi_virtualenv": path_check(
            HOME / "robot-learning/openpi/.venv/bin/python", kind="file"
        ),
        "huggingface_cache": path_check(HOME / ".cache/huggingface", kind="dir"),
        "ros_workspace": path_check(
            HOME / "robot-learning/rm65_project_jazzy_ws/install/setup.bash", kind="file"
        ),
        "combined_rm65_4c2_usd": path_check(
            HOME / "robot-learning/004-rm65-4c2-isaaclab/generated/rm65_4c2_software.usd",
            kind="file",
        ),
    }

    commands = {
        "ubuntu_24_04": {
            "name": "ubuntu_24_04",
            "ok": os_release.get("ID") == "ubuntu" and os_release.get("VERSION_ID") == "24.04",
            "observed": {
                "id": os_release.get("ID"),
                "version_id": os_release.get("VERSION_ID"),
            },
        },
        "ssh_active": command_check("ssh_active", "systemctl", "is-active", "ssh"),
        "ssh_enabled": command_check("ssh_enabled", "systemctl", "is-enabled", "ssh"),
        "nomachine_port": command_check("nomachine_port", "bash", "-lc", "ss -ltn | grep -q ':4000 '"),
        "nvidia_gpu": command_check(
            "nvidia_gpu",
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ),
        "docker_engine": command_check("docker_engine", "docker", "info", "--format", "{{.ServerVersion}}"),
        "vscode": command_check("vscode", "code", "--version"),
        "cpu_stability_mitigation": command_check(
            "cpu_stability_mitigation",
            "systemctl",
            "is-active",
            "disable-suspected-pcore.service",
        ),
        "robot_network_profile": command_check(
            "robot_network_profile",
            "bash",
            "-lc",
            "nmcli -t -f NAME connection show | grep -qx rm65-robot",
        ),
        "docker_gpu": command_check(
            "docker_gpu",
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            "openpi_server:latest",
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
            timeout=60,
        ),
        "ros_jazzy": command_check(
            "ros_jazzy",
            "bash",
            "-lc",
            "source /opt/ros/jazzy/setup.bash && "
            "source ~/robot-learning/rm65_project_jazzy_ws/install/setup.bash && "
            "ros2 pkg prefix rm_description",
        ),
    }

    evidence = {
        "windows_remote_access": evidence_check(
            MIGRATION_LOGS / "windows_remote_access_test.json"
        ),
        "robot_learning_files_present": evidence_check(
            MIGRATION_LOGS / "robot_learning_file_presence.json"
        ),
        "large_file_transfers": evidence_check(
            MIGRATION_LOGS / "large_file_transfer_evidence.json"
        ),
        "ros_jazzy_full_build": text_marker(
            MIGRATION_LOGS / "canonical_jazzy_build.log", "Summary: 25 packages finished"
        ),
        "ros_jazzy_changed_packages_build": text_marker(
            MIGRATION_LOGS / "jazzy_changed_packages_rebuild.log",
            "Summary: 3 packages finished",
        ),
        "isaaclab_headless": text_marker(
            MIGRATION_LOGS / "isaaclab_headless_check.log", "ISAAC_LAB_HEADLESS_CHECK=PASS"
        ),
        "rm65_4c2_articulation": evidence_check(
            MIGRATION_LOGS / "rm65_4c2_articulation_smoke.json"
        ),
        "gripper_aperture": evidence_check(MIGRATION_LOGS / "gripper_aperture_test.json"),
        "combined_ik": evidence_check(MIGRATION_LOGS / "combined_ik_test.json"),
        "gripper_close_contact": evidence_check(
            MIGRATION_LOGS / "gripper_close_stability.json"
        ),
        "rm65_policy_transform": evidence_check(
            MIGRATION_LOGS / "rm65_policy_transform_test.json"
        ),
        "openpi_inference": evidence_check(MIGRATION_LOGS / "openpi_inference_test.json"),
        "openpi_droid_inference": evidence_check(
            MIGRATION_LOGS / "openpi_droid_inference_test.json"
        ),
        "libero_container_runtime": evidence_check(
            MIGRATION_LOGS / "libero_image_smoke.json"
        ),
        "franka_pi05_isaaclab_closed_loop": evidence_check(
            MIGRATION_LOGS / "new_pc_franka_closed_loop.json"
        ),
        "file_transfer_queue": text_marker(
            MIGRATION_LOGS / "file_queue.log", "ALL_FILE_TRANSFERS_DONE"
        ),
        "docker_image_queue": text_marker(
            MIGRATION_LOGS / "docker_image_migration.log", "ALL_DOCKER_IMAGES_DONE"
        ),
    }

    all_checks = [*paths.values(), *commands.values(), *evidence.values()]
    failed = [
        item.get("name", item.get("path", "unknown"))
        for item in all_checks
        if not item.get("ok", False)
    ]
    report = {
        "status": "pass" if not failed else "incomplete",
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(),
        "safety": {
            "physical_robot_commanded": False,
            "physical_robot_network_required_for_this_audit": False,
        },
        "host": {
            "hostname": socket.gethostname(),
            "os_id": os_release.get("ID"),
            "os_version": os_release.get("VERSION_ID"),
            "python": sys.version.split()[0],
            "home": str(HOME),
        },
        "paths": paths,
        "commands": commands,
        "evidence": evidence,
        "failed_checks": failed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
