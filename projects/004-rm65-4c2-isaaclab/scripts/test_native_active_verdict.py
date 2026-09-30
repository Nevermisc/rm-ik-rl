"""Synthetic contracts, not evidence of simulated or physical task success."""
import copy
import json
import math

import pytest

from native_active_verdict import ACTIVE_PHASES, PHASE_COUNTS, PHYSICS_DT, evaluate_active_trial


def trial():
    rows = []
    for phase, count in PHASE_COUNTS:
        for index in range(count):
            f = (index + 1) / count
            lift = f if phase == 'active_lift' else float(phase in ('hold_lift', 'active_transport', 'hold_transport', 'reopen', 'settle_released'))
            travel = f if phase == 'active_transport' else float(phase in ('hold_transport', 'reopen', 'settle_released'))
            released = phase in ('reopen', 'settle_released')
            supported = phase in ('settle_open', 'close', 'hold_supported')
            contact = phase not in ('settle_open', 'reopen', 'settle_released')
            angle = .15 * lift
            q = [math.cos(angle / 2), 0., math.sin(angle / 2), 0.]
            held_position = [.06 * travel, 0., 1. + .04 * lift]
            palm_position = [held_position[0] - .14 * math.cos(angle), 0., held_position[2] + .14 * math.sin(angle)]
            position = list(held_position)
            if released:
                position[2] -= .2
            rows.append(dict(
                step=len(rows) + 1, physics_time_s=(len(rows) + 1) * PHYSICS_DT,
                phase=phase, finite=True, bilateral_native_face_contact=contact,
                other_robot_contact_N=0., support_contact_N=.2 if supported else 0.,
                object_pos_m=position, object_quat_wxyz=list(q), object_speed_m_s=0.,
                palm_pose_world=dict(position_m=palm_position, quat_wxyz=list(q)),
                gripper_q_rad=[0. if released or phase == 'settle_open' else .5] * 6,
                mimic_error_rad=.001, joint_limit_violation_rad=0.,
                support_clearance_m=0. if supported else .10,
                all_robot_contact_N=.5 if contact else 0., contact_buffer_saturated=False,
                contact_pairs_N={'Catch': .2 if released else 0.},
            ))
    return rows


def phase_rows(rows, phase):
    return [row for row in rows if row['phase'] == phase]


def validate_json(result):
    json.dumps(result, allow_nan=False)
    assert result['simulation_only'] is True
    assert result['scripted_active_lift_transport_diagnostic'] is True
    assert result['pi05_used'] is False
    assert result['training_ready'] is False
    assert result['deployment_accepted'] is False


def test_actual_rigid_carry_lift_transport_release_passes_only_scripted_diagnostic():
    rows = trial()
    original = copy.deepcopy(rows)
    result = evaluate_active_trial(rows)
    assert result['status'] == 'pass'
    assert result['diagnostic_success'] and result['gate_passed']
    assert result['active_lift_validated'] and result['transport_validated']
    assert all(result['checks'].values()) and not result['failure_reasons']
    assert result['metrics']['sample_count'] == 3360
    assert result['metrics']['active_phase_total_frames'] == 720
    assert result['metrics']['minimum_hold_lift_height_change_m'] == pytest.approx(.04)
    assert result['metrics']['minimum_hold_transport_xy_displacement_m'] == pytest.approx(.06)
    assert result['metrics']['max_palm_relative_translation_drift_m'] < 1e-14
    assert rows == original
    validate_json(result)


@pytest.mark.parametrize('phase', ACTIVE_PHASES)
@pytest.mark.parametrize('field,value,check', [
    ('bilateral_native_face_contact', False, 'continuous_active_native_retention'),
    ('other_robot_contact_N', .01, 'continuous_active_native_retention'),
    ('support_contact_N', .01, 'continuous_active_native_retention'),
    ('support_clearance_m', .03, 'continuous_active_native_retention'),
])
def test_every_active_frame_requires_native_contact_without_other_support(phase, field, value, check):
    rows = trial()
    phase_rows(rows, phase)[0][field] = value
    result = evaluate_active_trial(rows)
    assert result['gate_passed'] and result['checks'][check] is False
    assert not result['diagnostic_success']


def test_empty_hand_motion_and_command_targets_cannot_stand_in_for_object_motion():
    rows = trial()
    for row in rows:
        row['all_joint_target_rad'] = [0, 0, 0, 0, 1.42, .23]
        if row['phase'] in ACTIVE_PHASES:
            row['object_pos_m'] = [0., 0., 1.]
            row['bilateral_native_face_contact'] = False
    result = evaluate_active_trial(rows)
    assert not result['checks']['actual_lift_held']
    assert not result['checks']['actual_xy_transport_held']
    assert not result['checks']['continuous_active_native_retention']
    assert not result['diagnostic_success']


@pytest.mark.parametrize('phase', ('hold_unsupported', *ACTIVE_PHASES))
def test_catch_cannot_support_object_even_if_planned_position_is_far_below(phase):
    rows = trial()
    phase_rows(rows, phase)[-1]['contact_pairs_N']['Catch'] = .01
    result = evaluate_active_trial(rows)
    assert not result['diagnostic_success']
    assert any('catch_contact_persists' in reason for reason in result['failure_reasons'])


@pytest.mark.parametrize('pairs', [None, {}, {'Catch': math.nan}, {'Catch': -.01}])
def test_catch_contact_evidence_must_be_present_and_finite(pairs):
    rows = trial()
    rows[0]['contact_pairs_N'] = pairs
    result = evaluate_active_trial(rows)
    assert not result['gate_passed']
    validate_json(result)


def test_false_contact_bit_cannot_conceal_object_left_behind():
    rows = trial()
    for row in rows:
        if row['phase'] in ACTIVE_PHASES:
            row['object_pos_m'] = [0., 0., 1.]
    result = evaluate_active_trial(rows)
    assert result['checks']['continuous_active_native_retention']
    assert not result['checks']['object_translation_fixed_to_actual_palm']
    assert not result['checks']['actual_lift_held']
    assert not result['diagnostic_success']


def test_horizontal_motion_during_lift_cannot_count_as_second_stage_transport():
    rows = trial()
    # The object and palm move rigidly together by 6 cm during lift. They then
    # remain at exactly the same XY position throughout transport and its hold.
    for phase in ACTIVE_PHASES:
        group = phase_rows(rows, phase)
        for index, row in enumerate(group):
            new_x = .06 * (index + 1) / len(group) if phase == 'active_lift' else .06
            shift = new_x - row['object_pos_m'][0]
            row['object_pos_m'][0] += shift
            row['palm_pose_world']['position_m'][0] += shift
    result = evaluate_active_trial(rows)
    assert result['gate_passed'] and result['outcome_evaluated']
    assert result['failure_reasons'] == ['actual_xy_transport_held']
    assert result['metrics']['transport_reference_phase'] == 'hold_lift_last_frame'
    assert result['metrics']['transport_reference_object_position_m'][0] == pytest.approx(.06)
    assert result['metrics']['minimum_hold_transport_xy_displacement_m'] == pytest.approx(0.)
    assert not result['diagnostic_success']
    assert not result['active_lift_validated'] and not result['transport_validated']


@pytest.mark.parametrize('phase', ACTIVE_PHASES)
def test_single_frame_palm_relative_slip_fails_even_when_hold_endpoints_look_good(phase):
    rows = trial()
    phase_rows(rows, phase)[12]['object_pos_m'][1] += .005001
    result = evaluate_active_trial(rows)
    assert not result['checks']['object_translation_fixed_to_actual_palm']
    assert not result['diagnostic_success']


@pytest.mark.parametrize('phase', ACTIVE_PHASES)
def test_single_frame_object_rotation_relative_to_palm_fails(phase):
    rows = trial()
    row = phase_rows(rows, phase)[12]
    angle = 2 * math.atan2(row['object_quat_wxyz'][2], row['object_quat_wxyz'][0]) + math.radians(5.01)
    row['object_quat_wxyz'] = [math.cos(angle / 2), 0., math.sin(angle / 2), 0.]
    result = evaluate_active_trial(rows)
    assert not result['checks']['object_rotation_fixed_to_actual_palm']
    assert not result['diagnostic_success']


def test_quaternion_sign_changes_are_not_object_rotation():
    rows = trial()
    for index, row in enumerate(rows):
        if index % 2:
            row['object_quat_wxyz'] = [-v for v in row['object_quat_wxyz']]
        if index % 3:
            row['palm_pose_world']['quat_wxyz'] = [-v for v in row['palm_pose_world']['quat_wxyz']]
    assert evaluate_active_trial(rows)['diagnostic_success']


def test_translation_invariance_of_actual_palm_relative_evidence():
    rows = trial()
    for row in rows:
        for key in ('object_pos_m',):
            row[key] = [v + off for v, off in zip(row[key], [1., -2., .5])]
        palm = row['palm_pose_world']
        palm['position_m'] = [v + off for v, off in zip(palm['position_m'], [1., -2., .5])]
    assert evaluate_active_trial(rows)['diagnostic_success']


def test_early_drop_before_reopen_is_not_natural_release_success():
    rows = trial()
    row = phase_rows(rows, 'hold_transport')[-1]
    row['bilateral_native_face_contact'] = False
    row['object_pos_m'][2] -= .2
    result = evaluate_active_trial(rows)
    assert not result['checks']['continuous_active_native_retention']
    assert not result['checks']['late_reopen_drop']
    assert not result['diagnostic_success']


def test_drop_before_withdrawal_cannot_be_rebased_into_retention():
    rows = trial()
    for row in rows:
        if row['phase'] in ('hold_supported', 'withdraw_support', 'hold_unsupported'):
            row['object_pos_m'][2] -= .2
            row['bilateral_native_face_contact'] = False
    result = evaluate_active_trial(rows)
    assert not result['checks']['continuous_unsupported_retention']
    assert not result['diagnostic_success']


@pytest.mark.parametrize('field,value', [
    ('bilateral_native_face_contact', False), ('other_robot_contact_N', .01),
    ('support_contact_N', .01), ('support_clearance_m', .03),
    ('object_pos_m', [0., 0., .99]), ('object_speed_m_s', .05),
])
def test_last_two_seconds_unsupported_must_be_continuously_valid(field, value):
    rows = trial()
    phase_rows(rows, 'hold_unsupported')[-240][field] = value
    result = evaluate_active_trial(rows)
    assert not result['checks']['continuous_unsupported_retention']
    assert result['metrics']['terminal_valid_unsupported_duration_s'] < 2


def test_earlier_unsupported_contact_failure_can_recover_for_full_final_two_seconds():
    rows = trial()
    phase_rows(rows, 'hold_unsupported')[0]['bilateral_native_face_contact'] = False
    assert evaluate_active_trial(rows)['diagnostic_success']


@pytest.mark.parametrize('phase,field,value,check', [
    ('hold_lift', 'object_pos_m', [0., 0., 1.029], 'actual_lift_held'),
    ('hold_transport', 'object_pos_m', [.049, 0., 1.04], 'actual_xy_transport_held'),
    ('reopen', 'object_pos_m', [.06, 0., 1.], 'late_reopen_drop'),
    ('settle_released', 'object_pos_m', [.06, 0., 1.], 'released_tail_drop'),
    ('settle_released', 'all_robot_contact_N', .01, 'released_tail_no_robot_contact'),
    ('settle_released', 'object_speed_m_s', .05, 'released_tail_stable'),
    ('settle_released', 'gripper_q_rad', [.03] * 6, 'actual_gripper_reopened'),
    ('settle_released', 'gripper_q_rad', [-.03] * 6, 'actual_gripper_reopened'),
])
def test_hold_and_release_conditions_apply_to_entire_required_interval(phase, field, value, check):
    rows = trial()
    phase_rows(rows, phase)[-1][field] = value
    result = evaluate_active_trial(rows)
    assert not result['checks'][check]
    assert not result['diagnostic_success']


def test_palm_must_actually_rotate_during_hold_lift():
    rows = trial()
    phase_rows(rows, 'hold_lift')[0]['palm_pose_world']['quat_wxyz'] = [1., 0., 0., 0.]
    result = evaluate_active_trial(rows)
    assert not result['checks']['actual_palm_rotation_held']


@pytest.mark.parametrize('phase', [p for p, _ in PHASE_COUNTS])
def test_missing_one_frame_fails_even_after_renumbering_and_retiming(phase):
    rows = trial()
    del rows[next(i for i, row in enumerate(rows) if row['phase'] == phase)]
    for i, row in enumerate(rows):
        row.update(step=i+1, physics_time_s=(i+1)*PHYSICS_DT)
    result = evaluate_active_trial(rows)
    assert not result['gate_passed'] and not result['outcome_evaluated']
    assert 'exact_phase_counts' in result['failure_reasons']


def test_missing_entire_phase_fails():
    result = evaluate_active_trial([r for r in trial() if r['phase'] != 'active_transport'])
    assert not result['gate_passed']
    assert 'complete_ordered_phases' in result['failure_reasons']


def test_out_of_order_phases_with_right_counts_fail():
    rows = trial()
    lift = phase_rows(rows, 'active_lift')[0]
    hold = phase_rows(rows, 'hold_lift')[0]
    lift['phase'], hold['phase'] = hold['phase'], lift['phase']
    result = evaluate_active_trial(rows)
    assert result['gates']['exact_phase_counts']
    assert not result['gates']['complete_ordered_phases']


@pytest.mark.parametrize('field,value', [
    ('step', 1), ('physics_time_s', 123.), ('finite', False),
    ('contact_buffer_saturated', True), ('mimic_error_rad', .03),
    ('joint_limit_violation_rad', .00501),
])
def test_runtime_gates_fail_before_behavior(field, value):
    rows = trial()
    rows[300][field] = value
    result = evaluate_active_trial(rows)
    assert not result['gate_passed'] and not result['outcome_evaluated']
    assert all(v is None for v in result['checks'].values())
    validate_json(result)


@pytest.mark.parametrize('field,value', [
    ('physics_time_s', math.nan), ('physics_time_s', -1),
    ('object_pos_m', [math.inf, 0., 0.]), ('object_quat_wxyz', [0., 0., 0., 0.]),
    ('object_quat_wxyz', [2., 0., 0., 0.]), ('object_speed_m_s', True),
    ('support_contact_N', -.1), ('gripper_q_rad', [0.] * 5),
    ('finite', 1), ('palm_pose_world', None), ('step', 1.2),
])
def test_invalid_schema_and_nonfinite_values_are_json_safe(field, value):
    rows = trial()
    rows[0][field] = value
    result = evaluate_active_trial(rows)
    assert not result['gate_passed']
    validate_json(result)


@pytest.mark.parametrize('field', ['physics_time_s', 'palm_pose_world', 'object_quat_wxyz'])
def test_missing_pose_or_timestamp_is_never_optional(field):
    rows = trial()
    del rows[0][field]
    assert not evaluate_active_trial(rows)['gate_passed']


def test_invalid_palm_unit_quaternion_rejected():
    rows = trial()
    rows[0]['palm_pose_world']['quat_wxyz'] = [math.nan, 0., 0., 0.]
    result = evaluate_active_trial(rows)
    assert not result['gate_passed']
    validate_json(result)


@pytest.mark.parametrize('dt', [0, -PHYSICS_DT, math.nan, math.inf, True, '0.01', 1 / 240])
def test_protocol_dt_is_frozen(dt):
    result = evaluate_active_trial(trial(), dt=dt)
    assert not result['gate_passed']
    validate_json(result)


@pytest.mark.parametrize('rows', [None, [], [None], [1]])
def test_empty_and_nonrecord_input(rows):
    result = evaluate_active_trial(rows)
    assert not result['gate_passed']
    validate_json(result)


def test_derived_pose_overflow_fails_without_nan_in_output():
    rows = trial()
    row = phase_rows(rows, 'active_lift')[0]
    row['object_pos_m'] = [1e308, 0., 0.]
    row['palm_pose_world']['position_m'] = [-1e308, 0., 0.]
    result = evaluate_active_trial(rows)
    assert not result['gate_passed']
    assert 'nonfinite_derived_pose_evidence' in result['failure_reasons']
    validate_json(result)


def test_open_settle_and_close_contact_requirements_remain():
    rows = trial()
    for row in phase_rows(rows, 'close'):
        row['bilateral_native_face_contact'] = False
    phase_rows(rows, 'settle_open')[-1]['object_speed_m_s'] = .05
    result = evaluate_active_trial(rows)
    assert not result['checks']['settle_open_stable']
    assert not result['checks']['bilateral_contact_during_close']
