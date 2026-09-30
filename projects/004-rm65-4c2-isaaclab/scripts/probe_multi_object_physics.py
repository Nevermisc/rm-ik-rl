"""Check free-fall/contact/settling of development geometry; NOT grasp success."""
import argparse
import json
import sys
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output.exists():
    parser.error("output exists; use a fresh path")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.multi_object import CATALOG, spawn_config
launcher = AppLauncher(args)
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObject, RigidObjectCfg

try:
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1/240, device=args.device))
    floor = sim_utils.GroundPlaneCfg()
    floor.func("/World/Ground", floor)
    specs = [s for s in CATALOG.values() if s.split == "development"]
    objects = []
    for i, spec in enumerate(specs):
        objects.append(RigidObject(RigidObjectCfg(
            prim_path=f"/World/{spec.object_id}", spawn=spawn_config(spec, sim_utils),
            init_state=RigidObjectCfg.InitialStateCfg(pos=(i*.3, 0, spec.size_m[2]/2+.10)))))
    sim.reset()
    samples = [[] for _ in objects]
    for step in range(720):
        sim.step(render=False)
        for i, obj in enumerate(objects):
            obj.update(sim.get_physics_dt())
            if step == 0 or step >= 600:
                samples[i].append(obj.data.root_state_w[0].detach().cpu().tolist())
    cases = []
    for spec, states in zip(specs, samples):
        first, final = states[0], states[-1]
        tail = torch.tensor(states[1:])
        finite = bool(torch.isfinite(torch.tensor(states)).all())
        height_error = abs(final[2] - spec.size_m[2]/2)
        drift = float(torch.linalg.vector_norm(tail[:,:3] - tail[0,:3], dim=1).max())
        speed = float(torch.linalg.vector_norm(tail[:,7:10], dim=1).max())
        drop = first[2]-final[2]
        passed = finite and drop > .07 and height_error < .005 and drift < .005 and speed < .02
        cases.append(dict(object=spec.metadata(), passed=passed, all_finite=finite,
                          drop_m=drop, upright_height_error_m=height_error,
                          last_half_second_drift_m=drift, max_linear_speed_m_s=speed,
                          final_state=final))
    report = dict(version="multi-object-impl.001", status="pass" if all(c['passed'] for c in cases) else "fail",
                  simulation_only=True, real_robot_command_sent=False, policy_used=False,
                  grasp_tested=False, steps=720, dt_s=1/240,
                  limitation="Primitive upright drop test only; no robot, images, household semantics or grasp capability validated.", cases=cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print("MULTI_OBJECT_PHYSICS_REPORT=" + str(args.output), flush=True)
finally:
    launcher.app.close(skip_cleanup=True)
