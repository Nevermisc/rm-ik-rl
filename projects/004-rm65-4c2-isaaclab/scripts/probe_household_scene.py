"""Render textured household assets and measure settling, not robot/task success."""
import argparse
import json
import sys
import time
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--viewer-hold-seconds', type=float, default=0)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output_dir.exists():
    parser.error('output directory exists')
if not args.enable_cameras:
    parser.error('--enable_cameras required')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import manifest_object_ids, load_household, household_spawn_config
from openpi_extension.physics_contract import GRAVITY_M_S2
specs = [load_household(args.manifest, key) for key in manifest_object_ids(args.manifest)]
if not 0 <= args.viewer_hold_seconds <= 600:
    parser.error('viewer hold must be within 0..600 seconds')
launcher = AppLauncher(args)
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import RigidObject, RigidObjectCfg
from isaaclab.sensors import Camera, CameraCfg
from PIL import Image

try:
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1/240, gravity=GRAVITY_M_S2, device=args.device))
    sim.set_camera_view(eye=(.65,.8,.72), target=(.15,.15,.04))
    floor = sim_utils.CuboidCfg(size=(2,2,.04), collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.16,.18,.21)))
    floor.func('/World/Table', floor, translation=(0,0,-.02))
    light = sim_utils.DomeLightCfg(intensity=700)
    light.func('/World/Light', light)
    objects = []
    positions = [(.30*(i%3), .30*(i//3)) for i in range(len(specs))]
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
    initial_velocity_z = [float(obj.data.root_lin_vel_w[0,2]) for obj in objects]
    measured_acceleration_z = [None for _ in objects]
    for step in range(720):
        if not launcher.app.is_running():
            raise RuntimeError('viewer closed before physics validation completed')
        sim.step(render=False)
        for i,obj in enumerate(objects):
            obj.update(sim.get_physics_dt())
            if step == 11:
                measured_acceleration_z[i] = (float(obj.data.root_lin_vel_w[0,2])-initial_velocity_z[i])/(12*sim.get_physics_dt())
            if step == 0 or step >= 600:
                trajectories[i].append(obj.data.root_state_w[0].detach().cpu().tolist())
        if not args.headless and step % 8 == 0:
            sim.render()
    for _ in range(30):
        sim.render()
        camera.update(sim.get_physics_dt(), force_recompute=True)
    args.output_dir.mkdir(parents=True)
    rgb = camera.data.output['rgb'][0,:,:,:3].detach().cpu().numpy()
    Image.fromarray(rgb).save(args.output_dir/'overview.png')
    cases = []
    for spec, xy, states, acceleration, obj in zip(specs, positions, trajectories, measured_acceleration_z, objects):
        tail = torch.tensor(states[1:])
        finite = bool(torch.isfinite(torch.tensor(states)).all())
        drift = float(torch.linalg.vector_norm(tail[:,:3]-tail[0,:3],dim=1).max())
        speed = float(torch.linalg.vector_norm(tail[:,7:10],dim=1).max())
        drop = states[0][2]-states[-1][2]
        gravity_passed = acceleration is not None and abs(acceleration + 9.81) < .2
        passed = finite and gravity_passed and drift < .01 and speed < .05 and drop > .03 and states[-1][2] > 0
        cases.append(dict(object=spec.metadata(), initial_xy=xy, physics_settling_passed=passed,
            drop_m=drop, tail_drift_m=drift, tail_speed_m_s=speed, final_state=states[-1],
            free_fall_acceleration_z_m_s2=acceleration, free_fall_gravity_passed=gravity_passed,
            runtime_mass_kg=obj.root_physx_view.get_masses().detach().cpu().reshape(-1).tolist()))
    report = dict(version='household-generalization.004', status='pass' if all(c['physics_settling_passed'] for c in cases) else 'fail',
        simulation_only=True, real_robot_command_sent=False, pi05_used=False, grasp_tested=False,
        visual_review_required=True, collision_cavity_validated=False, image='overview.png', cases=cases)
    (args.output_dir/'report.json').write_text(json.dumps(report,indent=2))
    print('HOUSEHOLD_SCENE_REPORT=' + str(args.output_dir/'report.json'), flush=True)
    deadline = time.monotonic() + args.viewer_hold_seconds
    while not args.headless and launcher.app.is_running() and time.monotonic() < deadline:
        sim.render()
        time.sleep(.02)
finally:
    launcher.app.close(skip_cleanup=True)
raise SystemExit(0 if report['status'] == 'pass' else 1)
