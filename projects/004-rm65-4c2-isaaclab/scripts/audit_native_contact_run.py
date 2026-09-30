"""Read-only, hash-bound comparison of completed native-contact diagnostic logs.

Descriptive rotation/slip/drop markers never replace the frozen trial verdict.
Only a fresh analysis JSON is written; assets, protocol, and telemetry are read.
"""
import argparse
from collections import Counter, deque
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


FINGERS = ('tool_l_3', 'tool_r_3')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def norm(values):
    return math.sqrt(sum(value * value for value in values))


def rotation_deg(first, second):
    cosine = abs(sum(a * b for a, b in zip(first, second))) / (norm(first) * norm(second))
    return math.degrees(2 * math.acos(min(1.0, cosine)))


def describe(row, reference):
    delta = [a - b for a, b in zip(row['object_pos_m'], reference['object_pos_m'])]
    return dict(step=row['step'], phase=row['phase'], physics_time_s=row['physics_time_s'],
        object_pos_m=row['object_pos_m'], object_quat_wxyz=row['object_quat_wxyz'],
        delta_from_settle_open_end_m=delta, horizontal_slip_m=math.hypot(*delta[:2]),
        downward_translation_m=-delta[2],
        rotation_from_settle_open_end_deg=rotation_deg(row['object_quat_wxyz'], reference['object_quat_wxyz']),
        object_speed_m_s=row['object_speed_m_s'], master_q_rad=row['gripper_q_rad'][0],
        mimic_error_rad=row['mimic_error_rad'], arm_max_error_rad=row['arm_max_error_rad'],
        bilateral_native_face_contact=row['bilateral_native_face_contact'])


def point_description(row, body, point):
    return dict(step=row['step'], phase=row['phase'], body=body,
        signed_force_N=point['force_N'], normal_world=point['normal_world'],
        separation_m=point['separation_m'], point_world_m=point['point_world_m'],
        source_inner_face_distance_m=point.get('source_inner_face_distance_m'),
        inner_face_normal_abs_alignment=point.get('inner_face_normal_abs_alignment'))


def new_case(row, dt):
    return dict(reference=row, last_step=0, phase_counts=Counter(), phases={}, events={},
        first_face=None, last_face=None, face_count=0, current_run=0, current_run_start=None,
        longest_run=0, longest_run_span=None, body_peaks={}, native_point_stats={},
        signed_force_counts={}, max_norm_error=0.0, max_norm_error_event=None,
        vector_comparisons=0, vector_error_square_sum=0.0, max_vector_error=0.0,
        max_vector_error_event=None, vector_rows=0, pose_rows=0, linear_velocity_rows=0,
        max_mimic=0.0, max_mimic_event=None, max_arm=0.0, max_arm_event=None,
        max_joint_violation=0.0, finite=True, saturated=False, contiguous=True,
        contact_tail=deque(maxlen=max(1, math.ceil(0.25 / dt))),
        final_tail=deque(maxlen=max(1, math.ceil(1.0 / dt))), latest=None)


def process_row(case, row, dt, active_force_min):
    step, phase = row['step'], row['phase']
    case['contiguous'] &= step == case['last_step'] + 1
    case['last_step'] = step
    case['phase_counts'][phase] += 1
    if phase == 'settle_open':
        case['reference'] = row
    event = describe(row, case['reference'])
    case['latest'] = event
    case['final_tail'].append(event)
    case['finite'] &= row['finite']
    case['saturated'] |= row['contact_buffer_saturated']
    case['max_joint_violation'] = max(case['max_joint_violation'], row['joint_limit_violation_rad'])
    for short, field in (('mimic', 'mimic_error_rad'), ('arm', 'arm_max_error_rad')):
        if row[field] > case['max_' + short]:
            case['max_' + short] = row[field]
            case['max_' + short + '_event'] = dict(step=step, phase=phase)
    phase_data = case['phases'].setdefault(phase, dict(first_step=step, last_step=step,
        samples=0, native_face_samples=0, max_speed_m_s=0.0,
        min_object_z_m=row['object_pos_m'][2], max_object_z_m=row['object_pos_m'][2],
        max_rotation_from_settled_deg=0.0, max_horizontal_slip_m=0.0))
    phase_data['last_step'] = step
    phase_data['samples'] += 1
    phase_data['native_face_samples'] += int(row['bilateral_native_face_contact'])
    phase_data['max_speed_m_s'] = max(phase_data['max_speed_m_s'], row['object_speed_m_s'])
    phase_data['min_object_z_m'] = min(phase_data['min_object_z_m'], row['object_pos_m'][2])
    phase_data['max_object_z_m'] = max(phase_data['max_object_z_m'], row['object_pos_m'][2])
    phase_data['max_rotation_from_settled_deg'] = max(phase_data['max_rotation_from_settled_deg'], event['rotation_from_settle_open_end_deg'])
    phase_data['max_horizontal_slip_m'] = max(phase_data['max_horizontal_slip_m'], event['horizontal_slip_m'])
    if row['bilateral_native_face_contact']:
        if case['first_face'] is None:
            case['first_face'] = event
        case['last_face'] = event
        case['face_count'] += 1
        if case['current_run'] == 0:
            case['current_run_start'] = step
        case['current_run'] += 1
        if case['current_run'] > case['longest_run']:
            case['longest_run'] = case['current_run']
            case['longest_run_span'] = dict(first_step=case['current_run_start'], last_step=step)
    else:
        if case['first_face'] is not None:
            case['events'].setdefault('first_native_face_loss', event)
        case['current_run'] = 0
    if phase != 'settle_open':
        markers = dict(rotation_ge_1deg=event['rotation_from_settle_open_end_deg'] >= 1.0,
            horizontal_slip_ge_5mm=event['horizontal_slip_m'] >= 0.005,
            drop_ge_5mm=event['downward_translation_m'] >= 0.005,
            catch_contact_ge_0p01N=row['contact_pairs_N'].get('Catch', 0.0) >= 0.01,
            withdrawal_started=phase == 'withdraw_support', reopen_started=phase == 'reopen')
        for name, observed in markers.items():
            if observed:
                case['events'].setdefault(name, event)
    for body, magnitude in row['contact_pairs_N'].items():
        if magnitude > case['body_peaks'].get(body, {}).get('magnitude_N', 0.0):
            case['body_peaks'][body] = dict(magnitude_N=magnitude, step=step, phase=phase)

    vectors = row.get('contact_pair_net_force_world_N')
    case['vector_rows'] += int(vectors is not None)
    case['pose_rows'] += int('fingertip_pose_world' in row)
    case['linear_velocity_rows'] += int('object_linear_velocity_world_m_s' in row)
    raw_by_body = {pair['body']: pair['contacts'] for pair in row['raw_contacts']}
    # Compare every filter, including zero-contact filters: missing raw points
    # cannot be hidden by comparing only bodies that appeared in raw_contacts.
    for body in row['contact_pairs_N']:
        points = raw_by_body.get(body, [])
        reconstructed = [sum(point['force_N'] * point['normal_world'][axis] for point in points) for axis in range(3)]
        scalar_error = abs(norm(reconstructed) - row['contact_pair_net_norm_N'][body])
        if scalar_error > case['max_norm_error']:
            case['max_norm_error'] = scalar_error
            case['max_norm_error_event'] = dict(step=step, phase=phase, body=body)
        if vectors is not None:
            error = norm([a - b for a, b in zip(reconstructed, vectors[body])])
            case['vector_comparisons'] += 1
            case['vector_error_square_sum'] += error * error
            if error > case['max_vector_error']:
                case['max_vector_error'] = error
                case['max_vector_error_event'] = dict(step=step, phase=phase, body=body,
                    reconstructed_world_N=reconstructed, reported_world_N=vectors[body])
        signs = case['signed_force_counts'].setdefault(body, dict(positive=0, negative=0))
        for point in points:
            if abs(point['force_N']) <= active_force_min:
                continue
            signs['positive' if point['force_N'] > 0 else 'negative'] += 1

    native_points = [(pair['body'], point) for pair in row['raw_contacts'] if pair['body'] in FINGERS
                     for point in pair['contacts'] if abs(point['force_N']) > active_force_min]
    for body, point in native_points:
        stats = case['native_point_stats'].setdefault(body, dict(active_count=0,
            first_active=point_description(row, body, point), last_active=None,
            min_separation_m=None, min_separation_event=None, max_distance_m=0.0,
            max_distance_event=None, min_normal_alignment=1.0, max_normal_alignment=0.0))
        stats['active_count'] += 1
        stats['last_active'] = point_description(row, body, point)
        if stats['min_separation_m'] is None or point['separation_m'] < stats['min_separation_m']:
            stats['min_separation_m'] = point['separation_m']
            stats['min_separation_event'] = point_description(row, body, point)
        distance = point['source_inner_face_distance_m']
        alignment = point['inner_face_normal_abs_alignment']
        if distance > stats['max_distance_m']:
            stats['max_distance_m'] = distance
            stats['max_distance_event'] = point_description(row, body, point)
        stats['min_normal_alignment'] = min(stats['min_normal_alignment'], alignment)
        stats['max_normal_alignment'] = max(stats['max_normal_alignment'], alignment)
    if native_points:
        summary = dict(event, active_native_points=len(native_points),
            min_separation_m=min(point['separation_m'] for _, point in native_points),
            max_source_inner_distance_m=max(point['source_inner_face_distance_m'] for _, point in native_points),
            min_normal_alignment=min(point['inner_face_normal_abs_alignment'] for _, point in native_points))
        case['contact_tail'].append(summary)


def finish_case(width, case, report_trial, dt):
    tail = list(case['final_tail'])
    contact_tail = list(case['contact_tail'])
    drop = case['events'].get('drop_ge_5mm')
    withdraw = case['events'].get('withdrawal_started')
    result = dict(width_m=width,record_count=sum(case['phase_counts'].values()),
        phase_counts=dict(case['phase_counts']), contiguous_steps=case['contiguous'],
        reference_settle_open_end=describe(case['reference'], case['reference']),
        first_bilateral_native_face=case['first_face'], last_bilateral_native_face=case['last_face'],
        bilateral_native_face_samples=case['face_count'],
        longest_continuous_native_face=dict(samples=case['longest_run'], duration_s=case['longest_run'] * dt, span=case['longest_run_span']),
        events=case['events'], phase_summary=case['phases'],
        first_drop_precedes_withdrawal=(drop['step'] < withdraw['step']) if drop and withdraw else None,
        max_mimic_error_rad=case['max_mimic'], max_mimic_event=case['max_mimic_event'],
        max_arm_error_rad=case['max_arm'], max_arm_event=case['max_arm_event'],
        max_joint_limit_violation_rad=case['max_joint_violation'], all_finite=case['finite'],
        any_contact_buffer_saturation=case['saturated'], contact_body_peaks=case['body_peaks'],
        active_native_contact_stats=case['native_point_stats'], signed_active_force_counts=case['signed_force_counts'],
        signed_reconstruction=dict(max_pair_norm_error_N=case['max_norm_error'], max_pair_norm_error_event=case['max_norm_error_event'],
            pair_vector_rows=case['vector_rows'], pair_vector_comparisons=case['vector_comparisons'],
            max_vector_error_N=case['max_vector_error'] if case['vector_comparisons'] else None,
            rms_vector_error_N=math.sqrt(case['vector_error_square_sum'] / case['vector_comparisons']) if case['vector_comparisons'] else None,
            max_vector_error_event=case['max_vector_error_event'],
            interpretation='Signed scalar times raw normal; missing vectors are unavailable, not zero or verified.'),
        explicit_pose_rows=case['pose_rows'], object_linear_velocity_rows=case['linear_velocity_rows'],
        last_active_contact_samples=contact_tail,
        final_one_second=dict(samples=len(tail),
            object_z_range_m=[min(row['object_pos_m'][2] for row in tail), max(row['object_pos_m'][2] for row in tail)],
            max_speed_m_s=max(row['object_speed_m_s'] for row in tail),
            max_orientation_change_from_tail_start_deg=max(rotation_deg(row['object_quat_wxyz'], tail[0]['object_quat_wxyz']) for row in tail)),
        final_state=case['latest'], frozen_verdict=report_trial)
    return result


def analyze_run(directory):
    directory = Path(directory).resolve()
    report = json.loads((directory / 'report.json').read_text())
    manifest = json.loads((directory / 'manifest.json').read_text())
    protocol = manifest['protocol']
    dt = float(protocol['physics_dt_s'])
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError('invalid recorded dt')
    expected = {phase: count for phase, _, count in protocol['phases']}
    telemetry = directory / 'telemetry.jsonl'
    before = telemetry.stat()
    digest = hashlib.sha256()
    cases = {}
    with telemetry.open('rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):
                raise ValueError('incomplete telemetry line; wait for a finished run')
            digest.update(line)
            row = json.loads(line)
            case = cases.setdefault(row['width_m'], new_case(row, dt))
            process_row(case, row, dt, protocol['contact_point_force_min_N'])
    after = telemetry.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('telemetry changed during read-only analysis')
    if not cases:
        raise ValueError('no complete telemetry records')
    trials = {trial['width_m']: trial['verdict'] for trial in report['trials']}
    return dict(run=str(directory), protocol=protocol, protocol_sha256=manifest['protocol_sha256'],
        recorded_code_sha256=manifest['code_sha256'], report_status=report['status'], stop_reason=report['stop_reason'],
        source_files={name: dict(path=str(directory / name), bytes=(directory / name).stat().st_size,
            sha256=digest.hexdigest() if name == 'telemetry.jsonl' else sha256(directory / name))
            for name in ('telemetry.jsonl', 'report.json', 'manifest.json')},
        report_physics_steps=report['physics_steps'], gravity_probe_pass=report['gravity_probe_pass'],
        runtime_preflight_pass=report['runtime_preflight_pass'],
        phase_counts_match_protocol=all(dict(case['phase_counts']) == expected for case in cases.values()),
        trials=[finish_case(width, case, trials[width], dt) for width, case in sorted(cases.items())])


def differences(before, after, path=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            result.extend(differences(before.get(key), after.get(key), path + '/' + key))
        return result
    return [] if before == after else [dict(path=path, before=before, after=after)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('fresh output required; existing reports are preserved')
    runs = [analyze_run(path) for path in args.runs]
    result = dict(schema='rm65_native_contact_readonly_comparison_v1',
        created_at_utc=datetime.now(timezone.utc).isoformat(), simulation_only=True,
        physics_steps_executed_by_analysis=0, pi05_used=False, training_ready=False,
        deployment_accepted=False, audit_script_sha256=sha256(__file__), runs=runs,
        protocol_differences_from_first=[dict(run=run['run'], differences=differences(runs[0]['protocol'], run['protocol'])) for run in runs[1:]],
        event_definitions=dict(reference='End of settle_open, not hold_supported end.',
            rotation='First orientation change >=1 degree; quaternion sign ignored, object symmetries not quotiented.',
            slip='First XY translation >=5 mm.', drop='First world-Z decrease >=5 mm.',
            catch='First Catch force magnitude >=0.01 N.',
            markers_are_descriptive_not_acceptance_thresholds=True,
            contact_tail='Last up-to-0.25/dt records containing active native contacts; skipped no-contact records are visible from step gaps.'),
        limitations=['Frozen verdicts are copied unchanged; this report does not introduce a new acceptance criterion.',
            'Raw separation is a contact-report quantity, not an exact final-pose geometric penetration depth.',
            'Implicit actuator torque estimates are not measured applied motor efforts and are not used here.',
            'One trial per width and one wrist pose cannot establish generalization or hardware calibration.'])
    encoded = (json.dumps(result, indent=2, allow_nan=False) + '\n').encode()
    with args.output.open('xb') as stream:
        stream.write(encoded)
    print(json.dumps(dict(output=str(args.output), bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest(),
        summary=[dict(run=run['run'], trials=[dict(width_m=t['width_m'], verdict=t['frozen_verdict']['status'],
            longest_native_face_s=t['longest_continuous_native_face']['duration_s'], first_drop=t['events'].get('drop_ge_5mm', {}).get('step'),
            first_catch=t['events'].get('catch_contact_ge_0p01N', {}).get('step'), max_vector_error_N=t['signed_reconstruction']['max_vector_error_N']) for t in run['trials']]) for run in runs]), allow_nan=False))


if __name__ == '__main__':
    main()
