import unittest
from check_household_visible_result import verified


class VisibleResultTests(unittest.TestCase):
    def setUp(self):
        self.report = dict(status='diagnostic', simulation_only=True,
                           formal_acceptance_passed=False,
                           evaluation_scope='multi_object_development_only',
                           grasp_tested=False, pi05_used=False, max_joint_error_rad=.001)

    def test_good_free(self):
        self.assertTrue(verified(self.report, 'free'))

    def test_empty_report(self):
        self.assertFalse(verified({}, 'free'))

    def test_bad_error(self):
        for value in (-.1, .03, .8, float('inf'), float('nan')):
            with self.subTest(value=value):
                self.report['max_joint_error_rad'] = value
                self.assertFalse(verified(self.report, 'free'))

    def test_model_result_is_not_free_diagnostic(self):
        self.report['pi05_used'] = True
        self.assertFalse(verified(self.report, 'free'))

    def test_formal_flag_is_rejected(self):
        self.report['formal_acceptance_passed'] = True
        self.assertFalse(verified(self.report, 'free'))

    def test_wrong_scope(self):
        self.report['evaluation_scope'] = 'formal'
        self.assertFalse(verified(self.report, 'free'))

    def test_ik_needs_path(self):
        self.assertFalse(verified(self.report, 'ik'))
        self.report['retreat_waypoint_count'] = 9
        self.assertTrue(verified(self.report, 'ik'))

    def test_grasp_needs_own_success(self):
        self.assertFalse(verified(self.report, 'grasp'))
        self.report.update(status='pass', real_robot_command_sent=False)
        self.assertTrue(verified(self.report, 'grasp'))

    def test_unknown_mode(self):
        self.assertFalse(verified(self.report, 'unknown'))


if __name__ == '__main__':
    unittest.main()
