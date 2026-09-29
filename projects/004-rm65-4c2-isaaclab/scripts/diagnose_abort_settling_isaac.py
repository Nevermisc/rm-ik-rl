"""Controlled Isaac physics diagnostic; not policy/task acceptance."""
import argparse
import ast
import json
from pathlib import Path
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObject, RigidObjectCfg
from isaaclab.sim import SimulationContext

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.closed_loop_report import evaluate_cube_workspace_safety

try:
    tree = ast.parse(Path(__file__).with_name('run_pick_place_baseline.py').read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'run_pi05_closed_loop')
    def assignment(node, name):
        return isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets)
    start = next(i for i,n in enumerate(function.body) if assignment(n, 'settle_a_skipped_for_safety'))
    end = next(i for i,n in enumerate(function.body) if assignment(n, 'final_target_xy_error'))
    block = compile(ast.Module(body=function.body[start:end], type_ignores=[]), '<production-settling>', 'exec')
    sim = SimulationContext(sim_utils.SimulationCfg(dt=1/240, device=args.device))
    cube = RigidObject(RigidObjectCfg(prim_path='/World/DiagnosticCube',
        spawn=sim_utils.CuboidCfg(size=(.025,.025,.025),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=True),
            mass_props=sim_utils.MassPropertiesCfg(mass=.03),
            collision_props=sim_utils.CollisionPropertiesCfg()),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0,0,1))))
    sim.reset()
    cube.update(sim.get_physics_dt())
    results=[]
    for name, prior, source, expected in [
        ('existing_abort', 'cube_outside_workspace_envelope', [0,0,3], 0),
        ('settle_a_detection', None, [0,0,3], 120),
        ('normal', None, [0,0,1], 240)]:
        steps=[]
        def measured_hold(*unused):
            for _ in range(120):
                sim.step(render=False)
                cube.update(sim.get_physics_dt())
                steps.append(1)
        env=dict(sim=sim, robot=None, cube=cube, state=None, episode_capture=None,
                 settled_source_position=torch.tensor(source, device=sim.device),
                 CUBE_WORKSPACE_ESCAPE_RADIUS_M=1.0,
                 simulation_safety_abort_reason=prior,
                 simulation_safety_first_violation_stage='injected_prior_abort' if prior else None,
                 hold=measured_hold, evaluate_cube_workspace_safety=evaluate_cube_workspace_safety)
        exec(block, env)
        results.append(dict(case=name, actual_physics_steps=len(steps), expected_steps=expected,
                            passed=len(steps)==expected, reason=env['simulation_safety_abort_reason']))
    report=dict(status='pass' if all(r['passed'] for r in results) else 'fail',
                diagnostic_only=True, policy_used=False, real_robot_command_sent=False,
                limitation='Actual settling block with real Isaac stepping; no robot/controller or natural escape reproduction.', cases=results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
finally:
    launcher.app.close()
