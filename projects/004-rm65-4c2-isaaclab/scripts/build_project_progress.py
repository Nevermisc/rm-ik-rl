#!/usr/bin/env python3
"""Build a conservative machine-readable RM65 + pi0.5 project progress report."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def load_optional(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "exists": path.is_file(), "sha256": sha256(path)}


def training_step(log_path: Path) -> int | None:
    if not log_path.is_file():
        return None
    maximum = None
    pattern = re.compile(r"Step\s+(\d+):")
    with log_path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = pattern.search(line)
            if match:
                maximum = max(maximum or 0, int(match.group(1)))
    return maximum


def stage(status: str, claim: str, path: Path, details: dict[str, Any] | None = None) -> dict:
    result = {"status": status, "claim": claim, "evidence": evidence(path)}
    if details:
        result["details"] = details
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--execution-scope",
        choices=("simulation_only", "full"),
        default="simulation_only",
    )
    args = parser.parse_args()
    project = args.project_root.expanduser().resolve()
    results = project / "results"
    outputs = project / "outputs"

    migration_path = results / "new_lab_pc_migration_audit.json"
    historical_path = results / "stage_summary.json"
    dataset_path = results / "rm65_scripted_v1_summary.json"
    contract_path = results / "rm65_sim_train_openpi_contract.json"
    norm_path = results / "rm65_sim_train_norm_stats.json"
    training_path = results / "pi05_rm65_formal_30k.json"
    training_log_path = outputs / "rm65_scripted_v1_lora_30k.log"
    offline_path = results / "pi05_rm65_formal_offline_validation.json"
    sim_v1_path = results / "rm65_pi05_eval_v1_summary.json"
    training_v2_path = results / "pi05_rm65_policy_window_v2_30k.json"
    offline_v2_path = results / "pi05_rm65_policy_window_v2_offline_validation.json"
    sim_v2_path = results / "rm65_pi05_eval_v2_summary.json"
    pipeline_v2_path = outputs / "rm65_v2_post_pipeline.status"
    readiness_path = results / "rm65_real_robot_readiness.json"
    shadow_path = results / "rm65_policy_shadow_validation.json"
    real_path = results / "rm65_pi05_real_robot_evaluation.json"

    migration = load_optional(migration_path)
    historical = load_optional(historical_path)
    dataset = load_optional(dataset_path)
    contract = load_optional(contract_path)
    norm = load_optional(norm_path)
    training = load_optional(training_path)
    offline = load_optional(offline_path)
    simulation_v1 = load_optional(sim_v1_path)
    training_v2 = load_optional(training_v2_path)
    offline_v2 = load_optional(offline_v2_path)
    simulation_v2 = load_optional(sim_v2_path)
    simulation = simulation_v2 or simulation_v1
    sim_path = sim_v2_path if simulation_v2 else sim_v1_path
    pipeline_v2_status = (
        pipeline_v2_path.read_text(encoding="utf-8", errors="replace").strip()
        if pipeline_v2_path.is_file()
        else ""
    )
    readiness = load_optional(readiness_path)
    shadow = load_optional(shadow_path)
    real = load_optional(real_path)

    migration_pass = bool(migration and migration.get("status") == "pass")
    training_pass = bool(training and training.get("status") == "pass")
    last_step = training_step(training_log_path)
    training_status = "pass" if training_pass else ("in_progress" if last_step else "not_started")
    scripted_pass = bool(
        historical
        and historical.get("checks", {})
        .get("top_down_full_gravity_scripted_expert", {})
        .get("status")
        == "pass_in_simulation"
    )
    dataset_pass = bool(
        dataset
        and dataset.get("status") == "pass"
        and dataset.get("episode_count") == 45
        and dataset.get("success_rate") == 1.0
        and dataset.get("pi05_used") is False
        and dataset.get("real_robot_command_sent") is False
    )
    data_pass = bool(
        contract
        and contract.get("status") == "pass"
        and contract.get("repo_id") == "local/rm65_sim_train"
        and norm
        and norm.get("status") == "pass"
        and norm.get("repo_id") == "local/rm65_sim_train"
    )
    offline_pass = bool(
        offline
        and offline.get("status") == "pass"
        and offline.get("evaluation_kind") == "offline_held_out_imitation"
        and offline.get("real_robot_command_sent") is False
        and offline.get("task_success_claimed") is False
    )
    simulation_pass = bool(
        simulation
        and simulation.get("status") == "pass"
        and simulation.get("evaluation_kind") == "isaaclab_pi0.5_closed_loop"
        and simulation.get("simulation_only") is True
        and simulation.get("real_robot_command_sent") is False
        and int(simulation.get("episode_count", 0)) >= 20
        and float(simulation.get("success_rate", 0.0)) >= 0.8
    )
    v2_training_pass = bool(training_v2 and training_v2.get("status") == "pass")
    v2_offline_pass = bool(
        offline_v2
        and offline_v2.get("status") == "pass"
        and offline_v2.get("policy_window") is True
    )
    v2_simulation_pass = bool(
        simulation_v2
        and simulation_v2.get("status") == "pass"
        and int(simulation_v2.get("episode_count", 0)) >= 20
        and float(simulation_v2.get("success_rate", 0.0)) >= 0.8
    )
    if simulation_v2:
        v2_status = "pass" if v2_simulation_pass else "fail"
    elif v2_training_pass:
        v2_status = "evaluating"
    elif pipeline_v2_status.startswith("waiting_for_training_pid="):
        v2_status = "training"
    else:
        v2_status = "not_started"
    if simulation_pass:
        simulation_status = "pass"
    elif v2_status in {"training", "evaluating"}:
        simulation_status = "in_progress_after_v1_failure"
    elif simulation:
        simulation_status = "fail"
    else:
        simulation_status = "not_started"
    readiness_pass = bool(
        readiness
        and readiness.get("status") == "pass"
        and readiness.get("read_only") is True
        and readiness.get("real_robot_command_sent") is False
    )
    shadow_pass = bool(
        shadow
        and shadow.get("status") == "pass"
        and shadow.get("policy_shadow_passed") is True
        and shadow.get("read_only") is True
        and shadow.get("real_robot_command_sent") is False
        and int(shadow.get("accepted_samples", 0)) >= 20
        and int(shadow.get("rejected_samples", 1)) == 0
    )
    real_pass = bool(
        real
        and real.get("format") == "rm65_pi05_real_robot_evaluation_v1"
        and real.get("status") == "pass"
        and real.get("robot_model") == "RM65-B"
        and real.get("gripper_model") == "4C2"
        and real.get("pi05_used") is True
        and real.get("real_robot_command_sent") is True
        and real.get("task_success") is True
    )
    project_goal_complete = all(
        (
            migration_pass,
            scripted_pass,
            dataset_pass,
            data_pass,
            training_pass,
            offline_pass,
            simulation_pass,
            readiness_pass,
            shadow_pass,
            real_pass,
        )
    )

    stages = {
        "new_lab_pc_migration": stage(
            "pass" if migration_pass else "blocked",
            "项目不再依赖旧实验室电脑",
            migration_path,
        ),
        "scripted_expert_simulation": stage(
            "pass" if scripted_pass else "blocked",
            "脚本专家在 IsaacLab 完成 RM65-B + 4C2 任务；π0.5 未使用",
            historical_path,
        ),
        "expert_dataset": stage(
            "pass" if dataset_pass else "blocked",
            "45 条脚本专家轨迹全部成功并分为训练/验证集",
            dataset_path,
            {"episodes": dataset.get("episode_count") if dataset else None},
        ),
        "openpi_data_and_norm_stats": stage(
            "pass" if data_pass else "blocked",
            "RM65 数据满足 OpenPI 张量契约并有专用归一化统计",
            norm_path,
        ),
        "pi05_fine_tuning": stage(
            training_status,
            "π0.5 在 RM65 数据上完成参数微调",
            training_path,
            {"last_logged_step": last_step, "target_steps": 30000, "log": str(training_log_path)},
        ),
        "offline_checkpoint_validation": stage(
            "pass" if offline_pass else "waiting_for_training",
            "checkpoint 在留出观测上输出有限且形状正确的动作；不代表任务成功",
            offline_path,
        ),
        "pi05_isaaclab_closed_loop": stage(
            simulation_status,
            "π0.5 在 20 个留出条件的 IsaacLab 闭环中达到至少 80% 成功率",
            sim_path,
            {
                "episodes": simulation.get("episode_count") if simulation else 0,
                "success_rate": simulation.get("success_rate") if simulation else 0.0,
            },
        ),
        "pi05_policy_window_v2": stage(
            v2_status,
            "用缩短静止段的 policy-window 数据训练并复测第二个 π0.5 候选策略",
            sim_v2_path if simulation_v2 else training_v2_path,
            {
                "training_report_pass": v2_training_pass,
                "offline_validation_pass": v2_offline_pass,
                "closed_loop_pass": v2_simulation_pass,
                "pipeline_status": pipeline_v2_status,
            },
        ),
        "real_robot_readiness": stage(
            (
                "deferred_by_user"
                if args.execution_scope == "simulation_only"
                else ("pass" if readiness_pass else "blocked")
            ),
            "只读硬件、网络、相机、标定和现场安全准备齐全",
            readiness_path,
            {"blockers": readiness.get("blockers", []) if readiness else ["report_missing"]},
        ),
        "real_sensor_policy_shadow": stage(
            (
                "deferred_by_user"
                if args.execution_scope == "simulation_only"
                else ("pass" if shadow_pass else "not_started")
            ),
            "真实传感器运行 π0.5 影子模式，零发布、零真机命令",
            shadow_path,
        ),
        "pi05_real_robot_task": stage(
            (
                "deferred_by_user"
                if args.execution_scope == "simulation_only"
                else ("pass" if real_pass else "not_started")
            ),
            "π0.5 实际控制 RM65-B + 4C2 成功完成任务",
            real_path,
        ),
    }
    report = {
        "format": "rm65_pi05_project_progress_v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "active_execution_scope": args.execution_scope,
        "project_goal_complete": project_goal_complete,
        "claims": {
            "scripted_expert_simulation_complete": scripted_pass,
            "pi05_fine_tuning_complete": training_pass,
            "pi05_isaaclab_closed_loop_complete": simulation_pass,
            "pi05_real_robot_task_complete": real_pass,
        },
        "stages": stages,
        "interpretation": (
            "Each claim requires its own evidence file. Scripted-expert success, offline action "
            "validation, pi0.5 simulation closed loop, and real-robot success are not interchangeable."
        ),
    }
    output = (args.output or results / "project_progress.json").expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
