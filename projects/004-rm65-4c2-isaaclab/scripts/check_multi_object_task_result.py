"""Distinguish healthy recording/process exit from a successful probe task."""
import argparse
import json
from pathlib import Path


def task_passed(report):
    return (report.get('status') == 'pass'
            and report.get('simulation_only') is True
            and report.get('real_robot_command_sent') is False
            and report.get('evaluation_scope') == 'multi_object_development_only'
            and report.get('formal_acceptance_passed') is False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    passed = task_passed(report)
    print('MULTI_OBJECT_DEVELOPMENT_TASK=' + ('PASS' if passed else 'FAIL'))
    raise SystemExit(0 if passed else 1)
