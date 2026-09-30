"""Audit explicit visible runs, including missing reports; never infer policy success."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from check_household_visible_result import verified


def summarize(project, runs):
    project = Path(project)
    cases = []
    for run in runs:
        run_id, mode = run.split(':')
        if not re.fullmatch('[a-zA-Z0-9_]+', run_id) or mode not in ('free', 'ik', 'grasp'):
            raise ValueError('invalid run identifier or mode')
        path = project / 'datasets' / f'rm65_household_visible_{run_id}' / 'task_report.json'
        case = dict(run_id=run_id, mode=mode, report=str(path.relative_to(project)),
                    report_exists=path.is_file(), verified=False)
        if path.is_file():
            report = json.loads(path.read_text())
            case.update(status=report.get('status'), verified=verified(report, mode),
                        report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        pi05_used=report.get('pi05_used', False))
            for key in ('block_lift_height_m', 'final_target_xy_error_m', 'post_release_drift_m',
                        'unassisted_full_task_complete', 'max_joint_error_rad', 'source_offset_xy_m',
                        'development_presentation', 'target_collision_enable_stage'):
                if key in report:
                    case[key] = report[key]
        else:
            case['status'] = 'no_report_not_success'
        cases.append(case)
    return dict(schema='rm65_visible_household_development_summary_v1', cases=cases,
                grasp_reports=sum(c['mode']=='grasp' and c['report_exists'] for c in cases),
                grasp_passes=sum(c['mode']=='grasp' and c['verified'] for c in cases),
                missing_reports=sum(not c['report_exists'] for c in cases),
                simulation_only=True, checkpoint_updated=False, deployment_accepted=False,
                training_ready=False, independent_generalization_test=False,
                limitations=['Explicit development runs, including repeated conditions; not a benchmark success rate.',
                             'Scripted known-object geometry, not pi0.5 inference or visual localization.',
                             'Collision staging is recorded per run; initial-stage runs remove delayed support activation only.',
                             'Self-collision disabled; added simulated pads and gripper linkage remain uncalibrated to hardware.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('.'))
    parser.add_argument('--run', action='append', required=True, help='run_id:free|ik|grasp')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.project, args.run)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
