"""Render textured household assets and measure settling, not robot/task success."""
import argparse
import json
import sys
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output_dir.exists():
    parser.error('output directory exists')
if not args.enable_cameras:
    parser.error('--enable_cameras required')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import HOUSEHOLD_CATALOG, load_household, household_spawn_config
specs = [load_household(args.manifest, key) for key in HOUSEHOLD_CATALOG]
launcher = AppLauncher(args)
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObject, RigidObjectCfg
from isaaclab.sensors import Camera, CameraCfg
from PIL import Image

try:
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1/240, device=args.device))
    floor = sim_utils.CuboidCfg(size=(2,2,.04), collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.16,.18,.21)))
    floor.func('/World/Table', floor, translation=(0,0,-.02))
    light = sim_utils.DomeLightCfg(intensity=700)
    light.func('/World/Light', light)
    objects = []
    positions = [(0,0),(.30,0),(0,.30),(.30,.30)]
    for spec, (x,y) in zip(specs, positions):
        objects.append(RigidObject(RigidObjectCfg(prim_path=f'/World/{spec.object_id}',
            spawn=household_spawn_config(spec, sim_utils),
            init_state=RigidObjectCfg.InitialStateCfg(pos=(x,y,spec.size_m[2]/2+.08)))))
    camera = Camera(CameraCfg(prim_path='/World/Camera', height=720, width=960, data_types=['rgb'],
        spawn=sim_utils.PinholeCameraCfg(focal_length=24, horizontal_aperture=20.955, clipping_range=(.01,10))))
    sim.reset()
    camera.set_world_poses_from_view(torch.tensor([[.65,.80,.72]],device=sim.device),
                                     torch.tensor([[.15,.15,.04]],device=sim.device))
    trajectories = [[] for _ in objects]
    for step in range(720):
        sim.step(render=False)
        for i,obj in enumerate(objects):
            obj.update(sim.get_physics_dt())
            if step == 0 or step >= 600:
                trajectories[i].append(obj.data.root_state_w[0].detach().cpu().tolist())
    for _ in range(30):
        sim.render()
        camera.update(sim.get_physics_dt(), force_recompute=True)
    args.output_dir.mkdir(parents=True)
    rgb = camera.data.output['rgb'][0,:,:,:3].detach().cpu().numpy()
    Image.fromarray(rgb).save(args.output_dir/'overview.png')
    cases = []
    for spec, xy, states in zip(specs, positions, trajectories):
        tail = torch.tensor(states[1:])
        finite = bool(torch.isfinite(torch.tensor(states)).all())
        drift = float(torch.linalg.vector_norm(tail[:,:3]-tail[0,:3],dim=1).max())
        speed = float(torch.linalg.vector_norm(tail[:,7:10],dim=1).max())
        drop = states[0][2]-states[-1][2]
        passed = finite and drift < .01 and speed < .05 and drop > .03 and states[-1][2] > 0
        cases.append(dict(object=spec.metadata(), initial_xy=xy, physics_settling_passed=passed,
            drop_m=drop, tail_drift_m=drift, tail_speed_m_s=speed, final_state=states[-1]))
    report = dict(version='household-impl.005', status='pass' if all(c['physics_settling_passed'] for c in cases) else 'fail',
        simulation_only=True, real_robot_command_sent=False, pi05_used=False, grasp_tested=False,
        visual_review_required=True, collision_cavity_validated=False, image='overview.png', cases=cases)
    (args.output_dir/'report.json').write_text(json.dumps(report,indent=2))
    print('HOUSEHOLD_SCENE_REPORT=' + str(args.output_dir/'report.json'), flush=True)
finally:
    launcher.app.close(skip_cleanup=True)
raise SystemExit(0 if report['status'] == 'pass' else 1)
