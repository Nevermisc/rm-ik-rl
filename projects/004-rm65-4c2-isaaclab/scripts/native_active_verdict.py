"""Frozen, fail-closed CPU verdict for scripted native-finger active motion.

Consumes actual post-physics object and palm poses, never command targets.
The runner must independently verify source assets, dynamics and raw native-face
contacts. Passing this bounded bench diagnostic admits neither data nor a policy.
"""
import math
from numbers import Integral, Real


PHYSICS_DT = 1 / 120
PHASE_COUNTS = (
    ('settle_open', 240), ('close', 480), ('hold_supported', 240),
    ('withdraw_support', 240), ('hold_unsupported', 480),
    ('active_lift', 240), ('hold_lift', 120),
    ('active_transport', 240), ('hold_transport', 120),
    ('reopen', 480), ('settle_released', 480),
)
# Public runner contract: the complete active protocol, including preparation/release.
ACTIVE_PHASE_COUNTS = PHASE_COUNTS
PHASES = tuple(phase for phase, _ in PHASE_COUNTS)
ACTIVE_PHASES = ('active_lift', 'hold_lift', 'active_transport', 'hold_transport')
THRESHOLDS = dict(
    physics_dt_s=PHYSICS_DT, unsupported_duration_s=2.0, open_settle_tail_s=0.5,
    late_reopen_tail_s=0.25, released_tail_s=1.0,
    support_clearance_m=0.03, forbidden_contact_N=0.01,
    retained_vertical_drift_m=0.005, settled_speed_m_s=0.05,
    relative_translation_drift_m=0.005, relative_rotation_drift_rad=math.radians(5),
    actual_lift_m=0.03, actual_transport_xy_m=0.05,
    actual_palm_rotation_rad=0.10, release_drop_m=0.05,
    joint_limit_tolerance_rad=0.005, mimic_error_rad=0.03,
    reopened_absolute_joint_rad=0.03, quaternion_norm_tolerance=0.001,
)
_SCALARS = (
    'other_robot_contact_N', 'support_contact_N', 'object_speed_m_s',
    'mimic_error_rad', 'joint_limit_violation_rad', 'support_clearance_m',
    'all_robot_contact_N', 'physics_time_s',
)
_BOOLS = ('finite', 'bilateral_native_face_contact', 'contact_buffer_saturated')
_CHECKS = (
    'settle_open_stable', 'bilateral_contact_during_close',
    'continuous_unsupported_retention', 'continuous_active_native_retention',
    'object_translation_fixed_to_actual_palm', 'object_rotation_fixed_to_actual_palm',
    'actual_lift_held', 'actual_palm_rotation_held', 'actual_xy_transport_held',
    'late_reopen_drop', 'released_tail_drop', 'released_tail_no_robot_contact',
    'released_tail_stable', 'actual_gripper_reopened',
)


def _number(value):
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (ValueError, OverflowError):
        return False


def _vector(values, size):
    return (isinstance(values, (list, tuple)) and len(values) == size
            and all(_number(value) for value in values))


def _quaternion(values):
    return (_vector(values, 4)
            and abs(math.hypot(*values) - 1) <= THRESHOLDS['quaternion_norm_tolerance'])


def _schema_valid(row):
    if not isinstance(row, dict):
        return False
    if not isinstance(row.get('step'), Integral) or isinstance(row['step'], bool) or row['step'] < 0:
        return False
    if row.get('phase') not in PHASES or any(not isinstance(row.get(k), bool) for k in _BOOLS):
        return False
    if any(not _number(row.get(k)) for k in _SCALARS):
        return False
    if any(row[k] < 0 for k in _SCALARS if k != 'support_clearance_m'):
        return False
    pairs = row.get('contact_pairs_N')
    if not isinstance(pairs, dict) or not _number(pairs.get('Catch')) or pairs['Catch'] < 0:
        return False
    palm = row.get('palm_pose_world')
    return (_vector(row.get('object_pos_m'), 3) and _quaternion(row.get('object_quat_wxyz'))
            and _vector(row.get('gripper_q_rad'), 6) and isinstance(palm, dict)
            and _vector(palm.get('position_m'), 3) and _quaternion(palm.get('quat_wxyz')))


def _unit(q):
    norm = math.hypot(*q)
    return tuple(float(v) / norm for v in q)


def _multiply(a, b):
    w, x, y, z = a
    s, u, v, t = b
    return (w*s-x*u-y*v-z*t, w*u+x*s+y*t-z*v,
            w*v-x*t+y*s+z*u, w*t+x*v-y*u+z*s)


def _conjugate(q):
    return (q[0], -q[1], -q[2], -q[3])


def _angle(a, b):
    # q and -q represent the same orientation. atan2 remains stable near zero.
    delta = _multiply(_conjugate(_unit(a)), _unit(b))
    return 2 * math.atan2(math.hypot(*delta[1:]), abs(delta[0]))


def _relative_pose(row):
    palm = row['palm_pose_world']
    inverse = _conjugate(_unit(palm['quat_wxyz']))
    delta = tuple(float(a) - float(b) for a, b in zip(row['object_pos_m'], palm['position_m']))
    position = _multiply(_multiply(inverse, (0., *delta)), _conjugate(inverse))[1:]
    orientation = _multiply(inverse, _unit(row['object_quat_wxyz']))
    return position, orientation


def _run_lengths(flags):
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest, current


def evaluate_active_trial(samples, dt=PHYSICS_DT):
    """Evaluate the fixed 3,360-step protocol; return JSON-safe evidence only.

    Missing rows, timestamps, poses, complete phases or runtime checks fail before
    behavior evaluation. Actual palm-relative object pose is compared throughout
    every active phase with the final unsupported frame. The second-stage XY
    transport is measured from the final hold_lift frame. All thresholds are fixed.
    """
    result = dict(
        schema='rm65_native_active_verdict_v1', status='fail', diagnostic_success=False,
        gate_passed=False, outcome_evaluated=False, simulation_only=True,
        scripted_active_lift_transport_diagnostic=True, pi05_used=False,
        training_ready=False, deployment_accepted=False,
        active_lift_validated=False, transport_validated=False,
        scope='scripted_native_face_active_lift_transport_and_natural_release_bench_only',
        gates={}, checks={k: None for k in _CHECKS}, failure_reasons=[], metrics={},
        thresholds=dict(THRESHOLDS), expected_phase_counts=dict(PHASE_COUNTS),
        limitations=[
            'Runner must independently verify assets, runtime physics and raw source-face contacts.',
            'Actual pose evidence is required; command targets are never motion evidence.',
            'Passing this scripted bench does not validate household generalization or pi0.5.',
            'These diagnostic samples are not training-admitted.',
        ],
    )
    gates, reasons = result['gates'], result['failure_reasons']
    gates['frozen_physics_dt'] = _number(dt) and math.isclose(float(dt), PHYSICS_DT, rel_tol=0, abs_tol=1e-15)
    if not gates['frozen_physics_dt']:
        reasons.append('invalid_or_noncontract_physics_dt')
        return result
    try:
        rows = list(samples)
    except (TypeError, ValueError):
        rows = []
    result['metrics']['sample_count'] = len(rows)
    gates['sample_schema_and_numbers_valid'] = bool(rows) and all(_schema_valid(row) for row in rows)
    if not gates['sample_schema_and_numbers_valid']:
        reasons.append('empty_or_invalid_sample_schema_or_nonfinite_number')
        return result
    groups = {phase: [row for row in rows if row['phase'] == phase] for phase in PHASES}
    observed = []
    for row in rows:
        if not observed or observed[-1] != row['phase']:
            observed.append(row['phase'])
    gates.update(
        complete_ordered_phases=observed == list(PHASES),
        exact_phase_counts=all(len(groups[p]) == count for p, count in PHASE_COUNTS),
        contiguous_physics_steps=all(b['step'] == a['step'] + 1 for a, b in zip(rows, rows[1:])),
        recorded_physics_time_consistent=all(
            math.isclose(b['physics_time_s'] - a['physics_time_s'], PHYSICS_DT, rel_tol=1e-8, abs_tol=1e-9)
            for a, b in zip(rows, rows[1:])),
        all_finite_flags=all(row['finite'] for row in rows),
        no_contact_buffer_saturation=not any(row['contact_buffer_saturated'] for row in rows),
        joint_limits_respected=all(row['joint_limit_violation_rad'] <= 0.005 for row in rows),
        mimic_tracking_valid=all(row['mimic_error_rad'] < 0.03 for row in rows),
    )
    result['metrics'].update(
        physics_dt_s=PHYSICS_DT, phase_sample_counts={p: len(g) for p, g in groups.items()},
        max_mimic_error_rad=float(max(r['mimic_error_rad'] for r in rows)),
        max_joint_limit_violation_rad=float(max(r['joint_limit_violation_rad'] for r in rows)),
    )
    reasons.extend(name for name, passed in gates.items() if not passed)
    result['gate_passed'] = all(gates.values())
    if not result['gate_passed']:
        return result

    reference = groups['hold_unsupported'][-1]
    transport_reference = groups['hold_lift'][-1]
    supported_z = float(groups['hold_supported'][-1]['object_pos_m'][2])
    release_z = float(groups['hold_transport'][-1]['object_pos_m'][2])
    active = [row for row in rows if row['phase'] in ACTIVE_PHASES]
    try:
        reference_position, reference_orientation = _relative_pose(reference)
        relative_poses = [_relative_pose(row) for row in active]
        translation_drifts = [math.dist(pos, reference_position) for pos, _ in relative_poses]
        rotation_drifts = [_angle(q, reference_orientation) for _, q in relative_poses]
        lift_heights = [float(r['object_pos_m'][2]) - float(reference['object_pos_m'][2])
                        for r in groups['hold_lift']]
        palm_rotations = [_angle(r['palm_pose_world']['quat_wxyz'], reference['palm_pose_world']['quat_wxyz'])
                          for r in groups['hold_lift']]
        transport_distances = [math.dist(r['object_pos_m'][:2], transport_reference['object_pos_m'][:2])
                               for r in groups['hold_transport']]
        vertical_drifts = [abs(float(r['object_pos_m'][2]) - supported_z) for r in groups['hold_unsupported']]
        open_heights = [float(r['object_pos_m'][2]) for r in groups['settle_open'][-60:]]
        open_span = max(open_heights) - min(open_heights)
        reopen_drops = [release_z - float(r['object_pos_m'][2]) for r in groups['reopen'][-30:]]
        released_drops = [release_z - float(r['object_pos_m'][2]) for r in groups['settle_released'][-120:]]
        derived = (translation_drifts + rotation_drifts + lift_heights + palm_rotations
                   + transport_distances + vertical_drifts + reopen_drops + released_drops + [open_span])
        finite_derived = all(math.isfinite(value) for value in derived)
    except (OverflowError, ValueError, ZeroDivisionError):
        finite_derived = False
    gates['finite_derived_pose_evidence'] = finite_derived
    if not finite_derived:
        result['gate_passed'] = False
        reasons.append('nonfinite_derived_pose_evidence')
        return result

    result['outcome_evaluated'] = True
    retention_predicates = {
        'native_face_contact_unproven': lambda r: r['bilateral_native_face_contact'],
        'unintended_robot_support': lambda r: r['other_robot_contact_N'] < 0.01,
        'support_contact_persists': lambda r: r['support_contact_N'] < 0.01,
        'catch_contact_persists': lambda r: r['contact_pairs_N']['Catch'] < 0.01,
        'support_clearance_insufficient': lambda r: r['support_clearance_m'] > 0.03,
    }
    active_flags = [all(test(r) for test in retention_predicates.values()) for r in active]
    unsupported_flags = [all(test(r) for test in retention_predicates.values())
                         and drift <= 0.005 and r['object_speed_m_s'] < 0.05
                         for r, drift in zip(groups['hold_unsupported'], vertical_drifts)]
    longest, terminal = _run_lengths(unsupported_flags)
    released = groups['settle_released'][-120:]
    checks = result['checks']
    checks.update(
        settle_open_stable=open_span <= 0.005 and all(r['object_speed_m_s'] < 0.05 for r in groups['settle_open'][-60:]),
        bilateral_contact_during_close=any(r['bilateral_native_face_contact'] for r in groups['close']),
        continuous_unsupported_retention=terminal >= 240,
        continuous_active_native_retention=all(active_flags),
        object_translation_fixed_to_actual_palm=max(translation_drifts) <= 0.005,
        object_rotation_fixed_to_actual_palm=max(rotation_drifts) <= math.radians(5),
        actual_lift_held=min(lift_heights) >= 0.03,
        actual_palm_rotation_held=min(palm_rotations) >= 0.10,
        actual_xy_transport_held=min(transport_distances) >= 0.05,
        late_reopen_drop=min(reopen_drops) >= 0.05,
        released_tail_drop=min(released_drops) >= 0.05,
        released_tail_no_robot_contact=all(r['all_robot_contact_N'] < 0.01 for r in released),
        released_tail_stable=all(r['object_speed_m_s'] < 0.05 for r in released),
        actual_gripper_reopened=all(abs(q) < 0.03 for r in released for q in r['gripper_q_rad']),
    )
    result['metrics'].update(
        supported_reference_z_m=supported_z,
        unsupported_reference_object_position_m=[float(v) for v in reference['object_pos_m']],
        transport_reference_phase='hold_lift_last_frame',
        transport_reference_object_position_m=[float(v) for v in transport_reference['object_pos_m']],
        pre_release_reference_z_m=release_z,
        longest_valid_unsupported_duration_s=longest * PHYSICS_DT,
        terminal_valid_unsupported_duration_s=terminal * PHYSICS_DT,
        max_unsupported_vertical_drift_m=max(vertical_drifts),
        active_phase_valid_contact_frames=sum(active_flags), active_phase_total_frames=len(active),
        max_active_catch_contact_N=float(max(r['contact_pairs_N']['Catch'] for r in active)),
        max_palm_relative_translation_drift_m=max(translation_drifts),
        max_palm_relative_rotation_drift_rad=max(rotation_drifts),
        minimum_hold_lift_height_change_m=min(lift_heights),
        minimum_hold_lift_actual_palm_rotation_rad=min(palm_rotations),
        minimum_hold_transport_xy_displacement_m=min(transport_distances),
        minimum_late_reopen_drop_m=min(reopen_drops), minimum_released_tail_drop_m=min(released_drops),
        first_invalid_active_retention_step=next((r['step'] for r, ok in zip(active, active_flags) if not ok), None),
    )
    reasons.extend(name for name, passed in checks.items() if not passed)
    if not all(active_flags):
        reasons.extend('active_' + name for name, test in retention_predicates.items() if not all(test(r) for r in active))
    if terminal < 240:
        reasons.extend('unsupported_' + name for name, test in retention_predicates.items()
                       if not all(test(r) for r in groups['hold_unsupported'][-240:]))
    passed = all(checks.values())
    result.update(status='pass' if passed else 'fail', diagnostic_success=passed,
                  active_lift_validated=passed, transport_validated=passed)
    return result
