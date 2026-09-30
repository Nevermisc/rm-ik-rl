"""Summarize development evidence without turning diagnostics into task wins."""
import argparse
import json
from pathlib import Path


def summarize(root):
    cases = []
    for folder in sorted(Path(root).glob('rm65_household_dev_*')):
        report_path = folder/'task_report.json'
        if not report_path.is_file():
            continue
        report = json.loads(report_path.read_text())
        calibration = report.get('development_pad_calibration') or {}
        case = dict(case=folder.name, report=str(report_path), status=report.get('status'),
            pi05_used=report.get('pi05_used', False),
            diagnostic_only=report.get('status') == 'diagnostic',
            object_id=report.get('object_probe', {}).get('object_id'),
            formal_acceptance_passed=False, training_eligible=False)
        for field in ('failure_stage','block_lift_height_m','final_target_xy_error_m','action_chunks',
                      'executed_actions','max_joint_error_rad','soft_gains_diagnostic','force_drive_diagnostic'):
            if field in report:
                case[field] = report[field]
        if calibration:
            case['pad_calibration'] = {key:calibration[key] for key in
                ('height_offset_m','predicted_contact_q_rad','modeled_gap_m','source_support_sensor_filter')
                if key in calibration}
        forces = calibration.get('source_support_contact_by_body')
        if forces:
            case['source_support_peak_force_n'] = max(v['peak_n'] for v in forces.values())
            case['support_sensor_filter_validated'] = calibration.get('source_support_sensor_filter') == '/World/SourcePlatform/geometry/mesh'
        cases.append(case)
    return dict(schema='rm65_household_development_summary_v1', simulation_only=True,
        checkpoint_updated=False, deployment_accepted=False, independent_generalization_test=False,
        note='Repeated diagnostic/development cases, not a sampled success-rate benchmark. Scripted lift metric is end-of-lift; policy lift metric is maximum during rollout.',
        cases=cases, task_trial_count=sum(not c['diagnostic_only'] for c in cases),
        task_pass_count=sum(c['status']=='pass' and not c['diagnostic_only'] for c in cases),
        diagnostic_count=sum(c['diagnostic_only'] for c in cases))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datasets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.datasets)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))
