"""Fail-closed CPU verdict for a native-gripper bench contact diagnostic.

The runner supplies one post-physics record per step.  A successful verdict is
only evidence for support-withdrawal retention and release, never active pickup,
transport, a household task, or policy deployment.  Asset and source-surface
identity must additionally be checked by the runner.
"""
import math
from numbers import Integral, Real


PHASES = (
    'settle_open', 'close', 'hold_supported', 'withdraw_support',
    'hold_unsupported', 'reopen', 'settle_released',
)
_SCALARS = (
    'other_robot_contact_N', 'support_contact_N', 'object_speed_m_s',
    'mimic_error_rad', 'joint_limit_violation_rad', 'support_clearance_m',
    'all_robot_contact_N',
)
_NONNEGATIVE = tuple(name for name in _SCALARS if name != 'support_clearance_m')
_BOOLS = ('finite', 'bilateral_native_face_contact', 'contact_buffer_saturated')
_CHECKS = (
    'settle_open_stable', 'bilateral_contact_during_close',
    'continuous_unsupported_retention', 'late_reopen_drop',
    'released_tail_drop', 'released_tail_no_robot_contact',
    'released_tail_stable', 'actual_gripper_reopened',
)


def _number(value):
    if not isinstance(value, Real) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _schema_valid(sample):
    if not isinstance(sample, dict):
        return False
    if not isinstance(sample.get('step'), Integral) or isinstance(sample['step'], bool) or sample['step'] < 0:
        return False
    if sample.get('phase') not in PHASES:
        return False
    if any(not isinstance(sample.get(name), bool) for name in _BOOLS):
        return False
    if any(not _number(sample.get(name)) for name in _SCALARS):
        return False
    if any(sample[name] < 0 for name in _NONNEGATIVE):
        return False
    for name, size in (('object_pos_m', 3), ('gripper_q_rad', 6)):
        values = sample.get(name)
        if not isinstance(values, (list, tuple)) or len(values) != size or not all(_number(value) for value in values):
            return False
    return True


def _count(seconds, dt):
    ratio = seconds / dt
    # A subnormal dt cannot yield a usable evidence window; do not let infinity
    # escape into the JSON report or raise while validating malformed input.
    return max(1, math.ceil(ratio - 1e-10)) if math.isfinite(ratio) else 2 ** 63


def _tail(rows, seconds, dt):
    count = _count(seconds, dt)
    return rows[-count:] if len(rows) >= count else []


def _all(rows, predicate):
    return bool(rows) and all(predicate(row) for row in rows)


def _run_lengths(flags):
    longest = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return longest, current


def evaluate_trial(samples, dt=1 / 120):
    """Return only JSON-safe values; invalid/incomplete input never passes.

    Every phase must occur exactly once and in order.  Steps may start at any
    nonnegative global index but must be consecutive.  The final uninterrupted
    unsupported interval must last at least two seconds, so an earlier good
    interval cannot conceal a subsequent slip.  The final second of the released
    phase must show no robot contact, a settled object, and actual open joints.
    """
    result = dict(
        schema='rm65_native_contact_verdict_v1', status='fail', diagnostic_success=False,
        gate_passed=False, outcome_evaluated=False, simulation_only=True,
        pi05_used=False, training_ready=False, deployment_accepted=False,
        active_lift_validated=False, transport_validated=False,
        scope='native_surface_support_withdrawal_retention_and_natural_release_only',
        gates={}, checks={name: None for name in _CHECKS}, failure_reasons=[], metrics={},
        thresholds=dict(unsupported_duration_s=2.0, open_settle_tail_s=0.5,
            late_reopen_tail_s=0.25, released_tail_s=1.0, support_clearance_m=0.03,
            forbidden_contact_N=0.01, retained_vertical_drift_m=0.005,
            settled_speed_m_s=0.05, release_drop_m=0.05,
            joint_limit_tolerance_rad=0.005, mimic_error_rad=0.03,
            reopened_absolute_joint_rad=0.03),
        limitations=[
            'Requires independent runner asset, runtime, and raw native-face-contact validation.',
            'A fixed-arm support-withdrawal diagnostic does not validate active lift or transport.',
            'No policy was evaluated and these samples are not training-admitted.',
        ],
    )
    gates, reasons = result['gates'], result['failure_reasons']
    gates['valid_physics_dt'] = _number(dt) and float(dt) > 0
    if not gates['valid_physics_dt']:
        reasons.append('invalid_physics_dt')
        return result
    dt = float(dt)
    result['metrics']['physics_dt_s'] = dt
    try:
        rows = list(samples)
    except (TypeError, ValueError):
        rows = []
    gates['nonempty_samples'] = bool(rows)
    gates['sample_schema_and_numbers_valid'] = bool(rows) and all(_schema_valid(row) for row in rows)
    result['metrics']['sample_count'] = len(rows)
    if not gates['sample_schema_and_numbers_valid']:
        reasons.append('empty_or_invalid_sample_schema_or_nonfinite_number')
        return result

    gates['finite_trial_duration'] = math.isfinite(len(rows) * dt)
    timestamp_present = ['physics_time_s' in row for row in rows]
    if any(timestamp_present):
        gates['recorded_physics_time_consistent'] = (
            all(timestamp_present)
            and all(_number(row['physics_time_s']) for row in rows)
            and all(math.isclose(b['physics_time_s'] - a['physics_time_s'], dt,
                                 rel_tol=1e-8, abs_tol=min(dt * 1e-6, 1e-9))
                    for a, b in zip(rows, rows[1:]))
        )

    observed = []
    for row in rows:
        if not observed or observed[-1] != row['phase']:
            observed.append(row['phase'])
    groups = {phase: [row for row in rows if row['phase'] == phase] for phase in PHASES}
    gates.update(
        complete_ordered_phases=observed == list(PHASES),
        contiguous_physics_steps=all(b['step'] == a['step'] + 1 for a, b in zip(rows, rows[1:])),
        all_finite_flags=all(row['finite'] for row in rows),
        no_contact_buffer_saturation=not any(row['contact_buffer_saturated'] for row in rows),
        joint_limits_respected=all(row['joint_limit_violation_rad'] <= 0.005 for row in rows),
        mimic_tracking_valid=all(row['mimic_error_rad'] < 0.03 for row in rows),
        required_evidence_durations=(
            len(groups['settle_open']) >= _count(0.5, dt)
            and len(groups['hold_unsupported']) >= _count(2.0, dt)
            and len(groups['reopen']) >= _count(0.25, dt)
            and len(groups['settle_released']) >= _count(1.0, dt)
        ),
    )
    result['metrics'].update(
        phase_sample_counts={phase: len(group) for phase, group in groups.items()},
        max_mimic_error_rad=float(max(row['mimic_error_rad'] for row in rows)),
        max_joint_limit_violation_rad=float(max(row['joint_limit_violation_rad'] for row in rows)),
    )
    codes = {
        'finite_trial_duration': 'nonfinite_trial_duration',
        'recorded_physics_time_consistent': 'recorded_physics_time_gap_or_invalid',
        'complete_ordered_phases': 'phase_sequence_incomplete_or_out_of_order',
        'contiguous_physics_steps': 'missing_or_duplicate_physics_step',
        'all_finite_flags': 'nonfinite_dynamics_flag',
        'no_contact_buffer_saturation': 'contact_buffer_saturated',
        'joint_limits_respected': 'joint_limit_violation',
        'mimic_tracking_valid': 'mimic_tracking_failure',
        'required_evidence_durations': 'truncated_evidence_duration',
    }
    reasons.extend(codes[name] for name, passed in gates.items() if not passed and name in codes)
    result['gate_passed'] = all(gates.values())
    if not result['gate_passed']:
        return result

    result['outcome_evaluated'] = True
    reference_z = float(groups['hold_supported'][-1]['object_pos_m'][2])
    if not all(math.isfinite(float(row['object_pos_m'][2]) - reference_z) for row in rows):
        gates['finite_derived_vertical_distances'] = False
        result.update(gate_passed=False, outcome_evaluated=False)
        reasons.append('nonfinite_derived_vertical_distance')
        return result
    open_tail = _tail(groups['settle_open'], 0.5, dt)
    unsupported = groups['hold_unsupported']
    reopen_tail = _tail(groups['reopen'], 0.25, dt)
    released_tail = _tail(groups['settle_released'], 1.0, dt)
    retention_predicates = {
        'native_face_contact_unproven': lambda row: row['bilateral_native_face_contact'],
        'unintended_robot_support': lambda row: row['other_robot_contact_N'] < 0.01,
        'support_contact_persists': lambda row: row['support_contact_N'] < 0.01,
        'support_clearance_insufficient': lambda row: row['support_clearance_m'] > 0.03,
        'retention_vertical_drift': lambda row: abs(row['object_pos_m'][2] - reference_z) <= 0.005,
        'retention_not_stable': lambda row: row['object_speed_m_s'] < 0.05,
    }
    flags = [all(predicate(row) for predicate in retention_predicates.values()) for row in unsupported]
    longest, terminal = _run_lengths(flags)
    enough_retention = terminal >= _count(2.0, dt)
    checks = result['checks']
    checks.update(
        settle_open_stable=(
            _all(open_tail, lambda row: row['object_speed_m_s'] < 0.05)
            and max(row['object_pos_m'][2] for row in open_tail) - min(row['object_pos_m'][2] for row in open_tail) <= 0.005
        ),
        bilateral_contact_during_close=any(row['bilateral_native_face_contact'] for row in groups['close']),
        continuous_unsupported_retention=enough_retention,
        late_reopen_drop=_all(reopen_tail, lambda row: reference_z - row['object_pos_m'][2] >= 0.05),
        released_tail_drop=_all(released_tail, lambda row: reference_z - row['object_pos_m'][2] >= 0.05),
        released_tail_no_robot_contact=_all(released_tail, lambda row: row['all_robot_contact_N'] < 0.01),
        released_tail_stable=_all(released_tail, lambda row: row['object_speed_m_s'] < 0.05),
        actual_gripper_reopened=_all(released_tail, lambda row: all(abs(value) < 0.03 for value in row['gripper_q_rad'])),
    )
    result['metrics'].update(
        supported_reference_z_m=reference_z,
        longest_valid_unsupported_duration_s=float(longest * dt),
        terminal_valid_unsupported_duration_s=float(terminal * dt),
        max_unsupported_vertical_drift_m=float(max(abs(row['object_pos_m'][2] - reference_z) for row in unsupported)),
        minimum_late_reopen_drop_m=float(min(reference_z - row['object_pos_m'][2] for row in reopen_tail)),
        minimum_released_tail_drop_m=float(min(reference_z - row['object_pos_m'][2] for row in released_tail)),
        max_released_tail_robot_contact_N=float(max(row['all_robot_contact_N'] for row in released_tail)),
        max_released_tail_speed_m_s=float(max(row['object_speed_m_s'] for row in released_tail)),
        max_released_tail_absolute_joint_rad=float(max(abs(value) for row in released_tail for value in row['gripper_q_rad'])),
    )
    check_codes = {
        'settle_open_stable': 'object_not_settled_before_close',
        'bilateral_contact_during_close': 'no_bilateral_native_face_contact_during_close',
        'continuous_unsupported_retention': 'continuous_unsupported_retention_not_proven',
        'late_reopen_drop': 'natural_release_not_observed_during_late_reopen',
        'released_tail_drop': 'released_object_did_not_remain_below_grasp',
        'released_tail_no_robot_contact': 'released_object_still_contacts_robot',
        'released_tail_stable': 'released_object_not_settled',
        'actual_gripper_reopened': 'gripper_did_not_actually_reopen',
    }
    reasons.extend(check_codes[name] for name, passed in checks.items() if not passed)
    if not enough_retention:
        required_tail = _tail(unsupported, 2.0, dt)
        reasons.extend(code for code, predicate in retention_predicates.items() if not _all(required_tail, predicate))
    passed = all(checks.values())
    result.update(status='pass' if passed else 'fail', diagnostic_success=passed)
    return result
