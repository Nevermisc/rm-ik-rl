"""Exercise the actual post-policy settling block without launching Isaac Sim."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class Position:
    def clone(self): return self
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return [0, 0, 0]


class AbortSettlingTest(unittest.TestCase):
    def run_case(self, prior, reasons, expected_holds, expected_reason, expected_stage):
        source = Path(__file__).with_name('run_pick_place_baseline.py').read_text()
        tree = ast.parse(source)
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == 'run_pi05_closed_loop')
        def assignment(node, name):
            return isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in node.targets)
        start = next(i for i,n in enumerate(function.body)
                     if assignment(n, 'settle_a_skipped_for_safety'))
        end = next(i for i,n in enumerate(function.body)
                   if assignment(n, 'final_target_xy_error'))
        block = ast.Module(body=function.body[start:end], type_ignores=[])
        holds = []
        checks = iter(reasons)
        env = dict(sim=None, robot=None, state=None, episode_capture=None,
                   cube=SimpleNamespace(data=SimpleNamespace(root_pos_w=[Position()])),
                   settled_source_position=Position(), CUBE_WORKSPACE_ESCAPE_RADIUS_M=1,
                   simulation_safety_abort_reason=prior,
                   simulation_safety_first_violation_stage='action_chunk_063' if prior else None,
                   hold=lambda *args: holds.append((args[4], args[5])),
                   evaluate_cube_workspace_safety=lambda *args: {'reason': next(checks)})
        exec(compile(block, '<actual-settling-block>', 'exec'), env)
        self.assertEqual(holds, [(120, p) for p in expected_holds])
        self.assertEqual(env['simulation_safety_abort_reason'], expected_reason)
        self.assertEqual(env['simulation_safety_first_violation_stage'], expected_stage)
        self.assertEqual(env['settle_a_skipped_for_safety'], prior is not None)
        self.assertEqual(env['settle_b_skipped_for_safety'], len(expected_holds) < 2)

    def test_prior_abort_skips_both(self):
        self.run_case('escape', ['escape','escape'], [], 'escape', 'action_chunk_063')

    def test_settle_a_abort_skips_b(self):
        self.run_case(None, ['escape','escape'], ['PI05_SETTLE_A'], 'escape', 'verification_settle_a')

    def test_normal_path_preserved(self):
        self.run_case(None, [None,None], ['PI05_SETTLE_A','PI05_SETTLE_B'], None, None)

    def test_final_violation_recorded(self):
        self.run_case(None, [None,'escape'], ['PI05_SETTLE_A','PI05_SETTLE_B'], 'escape', 'verification_settle_b')


if __name__ == '__main__':
    unittest.main()
