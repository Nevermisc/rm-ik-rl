"""Explicit native simulation units and named-joint mapping; not a policy executor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

ARM_NAMES = tuple(f"joint_{i}" for i in range(1, 7))
MASTER = "tool_gripper_joint"
FOLLOWERS = ("tool_l_1_joint", "tool_r_3_joint", "tool_l_3_joint", "tool_l_2_joint", "tool_r_2_joint")
CONTROLLED_NAMES = (*ARM_NAMES, MASTER)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_control_contract(path, *, source_urdf):
    """Verify the actual source file, units, limits and disclosed simulation controls."""
    contract = json.loads(Path(path).read_text())
    expected = {
        "schema": "rm65_native_control_v1",
        "simulation_only": True,
        "hardware_calibrated": False,
        "policy_execution_admitted": False,
        "policy_training_admitted": False,
        "state_order": list(CONTROLLED_NAMES),
        "action_order": list(CONTROLLED_NAMES),
        "arm_units": "radian",
        "arm_action_semantics": "absolute_position_target",
        "state_source": "actual_joint_feedback_by_name",
        "gripper_mapping": "u=q_master_rad/0.865; q_target_rad=u*0.865",
        "gripper_open_u": 0.,
        "gripper_closed_limit_u": 1.,
        "gripper_master_limit_rad": .865,
        "passive_follower_names": list(FOLLOWERS),
        "follower_position_commands": False,
        "arm_drive_type": "force",
        "arm_stiffness": 1000.,
        "arm_damping": 100.,
        "arm_velocity_cap_rad_s": .5,
        "master_drive_type": "force",
        "master_stiffness": 2.,
        "master_damping": .1,
        "master_effort_cap_Nm": 1.,
        "master_velocity_cap_rad_s": 2.,
        "solve_articulation_contact_last": True,
        "physics_dt_s": 1 / 120,
        "solver_type": "TGS",
        "solver_position_iterations": 32,
        "solver_velocity_iterations": 8,
        "feedback_limit_tolerance_rad": 1e-6,
        "mimic_tolerance_rad": .03,
        "policy_control_period_s": None,
    }
    for key, value in expected.items():
        if key not in contract or contract[key] != value:
            raise ValueError(f"unsupported native control field: {key}")
    if _sha(source_urdf) != contract.get("source_urdf_sha256"):
        raise ValueError("actual source URDF identity mismatch")
    root = ET.parse(source_urdf).getroot()
    joints = {j.get("name"): j for j in root.findall("joint") if j.get("type") == "revolute"}
    names = (*CONTROLLED_NAMES, *FOLLOWERS)
    if not all(n in joints for n in names):
        raise ValueError("missing source joints")
    limits = {n: [float(joints[n].find("limit").get(k)) for k in ("lower", "upper")] for n in names}
    efforts = {n: float(joints[n].find("limit").get("effort")) for n in ARM_NAMES}
    if limits != contract.get("joint_limits_rad") or efforts != contract.get("arm_effort_caps_Nm"):
        raise ValueError("limits or effort caps differ from actual source URDF")
    if limits[MASTER] != [0., .865] or not np.isfinite(list(efforts.values())).all():
        raise ValueError("unsupported source master/arm limits")
    contract["verified_contract_sha256"] = _sha(path)
    return contract


def feedback_to_state(contract, joint_names, actual_joint_positions_rad):
    """Return measured seven-dimensional state and raw audit data without clipping."""
    names = list(joint_names)
    q = np.asarray(actual_joint_positions_rad, dtype=np.float64)
    if len(names) != len(set(names)) or q.shape != (len(names),) or not np.isfinite(q).all():
        raise ValueError("feedback must have unique names and one finite value per joint")
    required = (*CONTROLLED_NAMES, *FOLLOWERS)
    if set(names) != set(required):
        raise ValueError("feedback must contain all twelve native joints")
    measured = dict(zip(names, q.tolist(), strict=True))
    violations = {n: max(0., contract["joint_limits_rad"][n][0]-measured[n],
                            measured[n]-contract["joint_limits_rad"][n][1]) for n in required}
    if max(violations.values()) > contract["feedback_limit_tolerance_rad"]:
        raise ValueError("actual feedback outside source joint limits")
    mimic_error = max(abs(measured[n]-measured[MASTER]) for n in FOLLOWERS)
    if mimic_error >= contract["mimic_tolerance_rad"]:
        raise ValueError("actual passive mimic mismatch")
    state = np.array([*(measured[n] for n in ARM_NAMES), measured[MASTER]/.865])
    return {"state": state, "raw_joint_feedback_rad": measured,
            "limit_violation_rad": violations, "mimic_error_rad": mimic_error,
            "state_was_clipped": False}


def absolute_action_to_targets(contract, action, *, previous_targets_rad, command_interval_s):
    """Decode one action and reject jumps; return only six arm plus master commands.

    Interval is supplied by the caller because native policy sampling is not frozen.
    This checks command slope, not actual velocity or physical actuator torque.
    """
    values = np.asarray(action, dtype=np.float64)
    if values.shape != (7,) or not np.isfinite(values).all():
        raise ValueError("native action must contain exactly seven finite values")
    if not 0 <= values[-1] <= 1:
        raise ValueError("gripper action outside normalized [0,1]; no clipping")
    if isinstance(command_interval_s, bool) or not np.isfinite(command_interval_s) or command_interval_s <= 0:
        raise ValueError("positive actual command interval required")
    if set(previous_targets_rad) != set(CONTROLLED_NAMES):
        raise ValueError("previous command must name six arm joints and only the master")
    targets = dict(zip(CONTROLLED_NAMES, [*values[:6], values[-1]*.865], strict=True))
    for n, target in targets.items():
        lo, hi = contract["joint_limits_rad"][n]
        previous = previous_targets_rad[n]
        if not np.isfinite(previous) or not lo <= previous <= hi or not lo <= target <= hi:
            raise ValueError(f"absolute command outside source limits: {n}")
        cap = contract["master_velocity_cap_rad_s"] if n == MASTER else contract["arm_velocity_cap_rad_s"]
        if abs(target-previous) > cap*command_interval_s + 1e-12:
            raise ValueError(f"command slope exceeds declared velocity cap: {n}")
    return targets
