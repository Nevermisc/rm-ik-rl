import json
import tempfile
import unittest
from pathlib import Path
from summarize_household_visible_session import summarize


class SummaryTests(unittest.TestCase):
    def test_missing_is_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            result = summarize(folder, ['missing:grasp'])
            self.assertEqual(result['missing_reports'], 1)
            self.assertEqual(result['grasp_passes'], 0)

    def test_scripted_pass_not_deployment(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'datasets/rm65_household_visible_ok/task_report.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(dict(status='pass', simulation_only=True,
                formal_acceptance_passed=False, real_robot_command_sent=False,
                evaluation_scope='multi_object_development_only', pi05_used=False)))
            result = summarize(folder, ['ok:grasp'])
            self.assertEqual(result['grasp_passes'], 1)
            self.assertFalse(result['deployment_accepted'])
            self.assertFalse(result['training_ready'])

    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            summarize('.', ['../oops:grasp'])


if __name__ == '__main__':
    unittest.main()
