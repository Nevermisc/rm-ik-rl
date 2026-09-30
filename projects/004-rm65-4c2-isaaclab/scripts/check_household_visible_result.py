"""Check actual reports: Isaac's launcher exit status alone is insufficient."""
import argparse
import json
from pathlib import Path
from check_multi_object_task_result import task_passed


def verified(report, mode):
    common = (report.get('simulation_only') is True and
              report.get('formal_acceptance_passed') is False and
              report.get('evaluation_scope') == 'multi_object_development_only')
    if not common:
        return False
    if mode == 'grasp':
        return task_passed(report)
    if mode == 'ik':
        return report.get('status') == 'diagnostic' and report.get('retreat_waypoint_count', 0) > 0
    if mode != 'free':
        return False
    return (report.get('status') == 'diagnostic' and report.get('grasp_tested') is False
            and report.get('pi05_used') is False and 0 <= report.get('max_joint_error_rad', float('inf')) < .03)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--mode', choices=('free','ik','grasp'), required=True)
    args=parser.parse_args()
    if not args.report.is_file():
        parser.exit(2, 'ERROR: no report, simulator process exit is not success\n')
    passed=verified(json.loads(args.report.read_text()), args.mode)
    print(f'VISIBLE_{args.mode.upper()}_RESULT=' + ('VERIFIED' if passed else 'NOT_PASSED'))
    raise SystemExit(0 if passed else 1)
