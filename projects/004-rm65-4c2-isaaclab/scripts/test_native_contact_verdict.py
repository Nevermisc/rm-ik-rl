import copy
import json
import math

import pytest

from native_contact_verdict import PHASES, evaluate_trial


DT = 1 / 120


def trial():
    rows = []
    counts = [120, 120, 120, 120, 360, 120, 240]
    for phase, count in zip(PHASES, counts):
        for _ in range(count):
            released = phase in ('reopen', 'settle_released')
            supported = phase in ('settle_open', 'close', 'hold_supported')
            contact = phase in ('close', 'hold_supported', 'withdraw_support', 'hold_unsupported')
            rows.append(dict(step=len(rows) + 1, phase=phase, finite=True,
                bilateral_native_face_contact=contact, other_robot_contact_N=0.0,
                support_contact_N=0.2 if supported else 0.0,
                object_pos_m=[0.0, 0.0, 0.8 if released else 1.0], object_speed_m_s=0.0,
                gripper_q_rad=[0.0 if released or phase == 'settle_open' else 0.5] * 6,
                mimic_error_rad=0.001, joint_limit_violation_rad=0.0,
                support_clearance_m=0.1 if not supported else 0.0,
                all_robot_contact_N=0.5 if contact else 0.0, contact_buffer_saturated=False))
    return rows


def phase_rows(rows, phase):
    return [row for row in rows if row['phase'] == phase]


def check_json(result):
    json.dumps(result, allow_nan=False)
    assert result['pi05_used'] is False
    assert result['training_ready'] is False
    assert result['deployment_accepted'] is False
    assert result['active_lift_validated'] is False
    assert result['transport_validated'] is False


def test_valid_bench_diagnostic_is_never_policy_or_active_lift():
    rows = trial()
    before = copy.deepcopy(rows)
    result = evaluate_trial(rows)
    assert result['status'] == 'pass'
    assert result['diagnostic_success'] and result['gate_passed']
    assert all(result['checks'].values())
    assert result['metrics']['terminal_valid_unsupported_duration_s'] == pytest.approx(3.0)
    assert not result['failure_reasons']
    assert rows == before
    check_json(result)


@pytest.mark.parametrize('field,value,reason', [
    ('bilateral_native_face_contact', False, 'native_face_contact_unproven'),
    ('other_robot_contact_N', 0.1, 'unintended_robot_support'),
    ('support_contact_N', 0.1, 'support_contact_persists'),
    ('support_clearance_m', 0.03, 'support_clearance_insufficient'),
    ('object_pos_m', [0.0, 0.0, 0.99], 'retention_vertical_drift'),
    ('object_speed_m_s', 0.05, 'retention_not_stable'),
])
def test_retention_rejects_unproven_face_palm_support_and_slip(field, value, reason):
    rows = trial()
    for row in phase_rows(rows, 'hold_unsupported'):
        row[field] = value
    result = evaluate_trial(rows)
    assert result['gate_passed'] and not result['diagnostic_success']
    assert reason in result['failure_reasons']
    check_json(result)


def test_single_contact_frame_is_not_sustained_retention():
    rows = trial()
    unsupported = phase_rows(rows, 'hold_unsupported')
    for row in unsupported:
        row['bilateral_native_face_contact'] = False
    unsupported[-1]['bilateral_native_face_contact'] = True
    result = evaluate_trial(rows)
    assert not result['diagnostic_success']
    assert result['metrics']['terminal_valid_unsupported_duration_s'] == pytest.approx(DT)


def test_disjoint_contact_periods_cannot_be_added_together():
    rows = trial()
    unsupported = phase_rows(rows, 'hold_unsupported')
    unsupported[179]['bilateral_native_face_contact'] = False
    result = evaluate_trial(rows)
    assert not result['diagnostic_success']
    assert result['metrics']['longest_valid_unsupported_duration_s'] == pytest.approx(1.5)


def test_late_drop_cannot_be_hidden_by_earlier_two_second_success():
    rows = trial()
    phase_rows(rows, 'hold_unsupported')[-1]['object_pos_m'][2] = 0.98
    result = evaluate_trial(rows)
    assert result['metrics']['longest_valid_unsupported_duration_s'] > 2
    assert not result['diagnostic_success']


def test_bad_conditions_cannot_be_satisfied_at_different_times():
    rows = trial()
    unsupported = phase_rows(rows, 'hold_unsupported')
    for row in unsupported[:180]:
        row['support_contact_N'] = 0.2
    for row in unsupported[180:]:
        row['bilateral_native_face_contact'] = False
    result = evaluate_trial(rows)
    assert result['metrics']['longest_valid_unsupported_duration_s'] == 0
    assert not result['diagnostic_success']


@pytest.mark.parametrize('field,value,check', [
    ('object_pos_m', [0.0, 0.0, 1.0], 'released_tail_drop'),
    ('all_robot_contact_N', 0.01, 'released_tail_no_robot_contact'),
    ('object_speed_m_s', 0.05, 'released_tail_stable'),
    ('gripper_q_rad', [0.04] * 6, 'actual_gripper_reopened'),
    ('gripper_q_rad', [-0.5] * 6, 'actual_gripper_reopened'),
])
def test_release_needs_actual_drop_no_robot_contact_settling_and_open_joints(field, value, check):
    rows = trial()
    for row in phase_rows(rows, 'settle_released'):
        row[field] = value
    result = evaluate_trial(rows)
    assert result['checks'][check] is False
    assert not result['diagnostic_success']


def test_release_must_start_during_late_reopen_not_appear_only_at_final_pose():
    rows = trial()
    for row in phase_rows(rows, 'reopen'):
        row['object_pos_m'][2] = 1.0
    result = evaluate_trial(rows)
    assert result['checks']['late_reopen_drop'] is False
    assert not result['diagnostic_success']


@pytest.mark.parametrize('field,value,reason', [
    ('finite', False, 'nonfinite_dynamics_flag'),
    ('contact_buffer_saturated', True, 'contact_buffer_saturated'),
    ('mimic_error_rad', 0.03, 'mimic_tracking_failure'),
    ('joint_limit_violation_rad', 0.00501, 'joint_limit_violation'),
])
def test_gates_fail_before_behavior_evaluation(field, value, reason):
    rows = trial()
    rows[0][field] = value
    result = evaluate_trial(rows)
    assert not result['gate_passed'] and not result['outcome_evaluated']
    assert all(value is None for value in result['checks'].values())
    assert reason in result['failure_reasons']
    check_json(result)


@pytest.mark.parametrize('field,value', [
    ('object_pos_m', [0.0, 0.0, math.nan]),
    ('gripper_q_rad', [0.0] * 5 + [math.inf]),
    ('other_robot_contact_N', math.nan),
    ('support_contact_N', -0.01),
    ('object_speed_m_s', True),
    ('finite', 1),
    ('step', 1.5),
])
def test_nonfinite_and_malformed_data_are_rejected_without_nonfinite_output(field, value):
    rows = trial()
    rows[0][field] = value
    result = evaluate_trial(rows)
    assert not result['gate_passed']
    check_json(result)


@pytest.mark.parametrize('dt', [0, -DT, math.nan, math.inf, True, '0.01'])
def test_invalid_dt_is_rejected_and_json_safe(dt):
    result = evaluate_trial(trial(), dt=dt)
    assert result['failure_reasons'] == ['invalid_physics_dt']
    check_json(result)


@pytest.mark.parametrize('kind', ['missing', 'duplicate', 'reverse', 'omitted_phase', 'repeat_phase', 'truncated_final', 'short_hold'])
def test_truncated_disordered_and_missing_step_records_rejected(kind):
    rows = trial()
    if kind == 'missing':
        del rows[300]
    elif kind == 'duplicate':
        rows.insert(300, copy.deepcopy(rows[300]))
    elif kind == 'reverse':
        rows[300], rows[301] = rows[301], rows[300]
    elif kind == 'omitted_phase':
        rows = [row for row in rows if row['phase'] != 'withdraw_support']
        for index, row in enumerate(rows):
            row['step'] = index + 1
    elif kind == 'repeat_phase':
        rows[800]['phase'] = 'hold_supported'
    elif kind == 'truncated_final':
        rows = rows[:-121]
    else:
        unsupported = phase_rows(rows, 'hold_unsupported')
        remove = {row['step'] for row in unsupported[:121]}
        rows = [row for row in rows if row['step'] not in remove]
        for index, row in enumerate(rows):
            row['step'] = index + 1
    result = evaluate_trial(rows)
    assert not result['gate_passed'] and not result['outcome_evaluated']
    check_json(result)


def test_unsettled_open_is_rejected():
    rows = trial()
    phase_rows(rows, 'settle_open')[-1]['object_speed_m_s'] = 0.1
    assert not evaluate_trial(rows)['checks']['settle_open_stable']


def test_actual_sample_rate_controls_duration():
    rows = trial()
    result = evaluate_trial(rows, dt=1 / 240)
    assert not result['gate_passed']
    assert 'truncated_evidence_duration' in result['failure_reasons']


@pytest.mark.parametrize('samples', [None, [], [{}], 'invalid'])
def test_missing_samples_never_pass(samples):
    result = evaluate_trial(samples)
    assert not result['diagnostic_success']
    check_json(result)


def test_global_consecutive_step_numbers_are_supported():
    rows = trial()
    for row in rows:
        row['step'] += 10000
    assert evaluate_trial(rows)['diagnostic_success']


def test_recorded_physics_time_catches_gap_even_if_steps_were_renumbered():
    rows = trial()
    for row in rows:
        row['physics_time_s'] = row['step'] * DT
    assert evaluate_trial(rows)['diagnostic_success']
    for row in rows[500:]:
        row['physics_time_s'] += DT
    result = evaluate_trial(rows)
    assert not result['gate_passed']
    assert 'recorded_physics_time_gap_or_invalid' in result['failure_reasons']


@pytest.mark.parametrize('kind', ['partial', 'nan'])
def test_partial_or_nonfinite_recorded_timestamp_is_invalid(kind):
    rows = trial()
    rows[0]['physics_time_s'] = DT if kind == 'partial' else math.nan
    result = evaluate_trial(rows)
    assert not result['gate_passed']
    check_json(result)


@pytest.mark.parametrize('dt', [1e-320, 1e308])
def test_extreme_finite_dt_fails_without_nonfinite_output(dt):
    result = evaluate_trial(trial(), dt=dt)
    assert not result['gate_passed']
    check_json(result)


def test_overflowing_derived_distance_does_not_escape_to_report():
    rows = trial()
    phase_rows(rows, 'hold_supported')[-1]['object_pos_m'][2] = 1e308
    phase_rows(rows, 'hold_unsupported')[-1]['object_pos_m'][2] = -1e308
    result = evaluate_trial(rows)
    assert not result['gate_passed']
    check_json(result)
