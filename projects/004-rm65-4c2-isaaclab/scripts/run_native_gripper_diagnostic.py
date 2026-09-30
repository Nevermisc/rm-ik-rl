"""Visible, bounded native-gripper validation, never a policy or training episode."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback
from build_native_gripper_candidate import sha256
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--hold-seconds', type=float, default=180.)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.headless or not os.environ.get('DISPLAY'):
    parser.error('new native diagnostic requires a visible desktop window')
if args.output_dir.exists() or not 0 <= args.hold_seconds <= 600:
    parser.error('fresh output directory and bounded hold required')
candidate = args.candidate.resolve()
source = json.loads((candidate/'source_audit.json').read_text())
imported = json.loads((candidate/'import_audit.json').read_text())
if imported['status'] != 'pass':
    parser.error('import audit must pass')
for filename, expected in imported['composed_layer_sha256'].items():
    if sha256(filename) != expected:
        parser.error('USD layer changed since import audit')
args.output_dir.mkdir(parents=True, exist_ok=False)
launcher = AppLauncher(args)

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaacsim.core.utils.stage import get_current_stage
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema
import omni.ui as ui


def write_live(record):
    tmp = args.output_dir/'live.tmp'
    tmp.write_text(json.dumps(dict(record, wall_time_unix=time.time()), indent=2))
    tmp.replace(args.output_dir/'live.json')


def main():
    dt = 1/120
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=dt, gravity=(0.,0.,-9.81), device=args.device))
    sim_utils.GroundPlaneCfg().func('/World/Ground', sim_utils.GroundPlaneCfg())
    light = sim_utils.DomeLightCfg(intensity=1000.)
    light.func('/World/Light',light)
    robot = Articulation(ArticulationCfg(prim_path='/World/Robot',
        spawn=sim_utils.UsdFileCfg(usd_path=str(candidate/'native.usd'), activate_contact_sensors=True,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False, max_depenetration_velocity=.2),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(enabled_self_collisions=True,
                solver_position_iteration_count=32, solver_velocity_iteration_count=8)),
        init_state=ArticulationCfg.InitialStateCfg(pos=(0.,0.,.1),joint_pos={'joint_.*':0.,'tool_.*':0.}),
        actuators={
            'arm':ImplicitActuatorCfg(joint_names_expr=['joint_[1-6]'], effort_limit_sim=300.,
                                     velocity_limit_sim=.5, stiffness=1000.,damping=100.),
            'gripper_master':ImplicitActuatorCfg(joint_names_expr=['tool_gripper_joint'],effort_limit_sim=1.,
                                                velocity_limit_sim=2.,stiffness=2.,damping=.1)}))
    ball = RigidObject(RigidObjectCfg(prim_path='/World/GravityProbe',
        spawn=sim_utils.SphereCfg(radius=.015, rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
            mass_props=sim_utils.MassPropertiesCfg(mass=.02), collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.8,.2,.1))),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(.5,0.,1.1))))
    moving = ['tool_r_1','tool_l_1','tool_r_2','tool_l_2','tool_r_3','tool_l_3']
    filters = [item['link'] for item in source['gripper']['links']]
    sensors = {name:ContactSensor(ContactSensorCfg(prim_path='/World/Robot/'+name,
        filter_prim_paths_expr=['/World/Robot/'+n for n in filters], update_period=0., history_length=0)) for name in moving}
    stage = get_current_stage()
    sim.reset()
    robot.reset()
    ball.reset()
    names = list(robot.data.joint_names)
    bodies = list(robot.data.body_names)
    gripids = [names.index(n) for n in [source['gripper']['master']]+source['gripper']['followers']]
    master = gripids[0]
    armids = [names.index('joint_'+str(i)) for i in range(1,7)]
    runtime = dict(body_mass_kg=dict(zip(bodies,robot.root_physx_view.get_masses()[0].cpu().tolist())),
                   gravity_disabled=[], kinematic_bodies=[], collision_meshes=[], self_collision=[], pair_filters=[],
                   actuators={key:list(val.joint_names) for key,val in robot.actuators.items()},
                   follower_stiffness=robot.data.joint_stiffness[0,gripids[1:]].cpu().tolist())
    for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
        if not str(prim.GetPath()).startswith('/World/Robot'):
            continue
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):
            if PhysxSchema.PhysxRigidBodyAPI(prim).GetDisableGravityAttr().Get():
                runtime['gravity_disabled'].append(str(prim.GetPath()))
            if UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get():
                runtime['kinematic_bodies'].append(str(prim.GetPath()))
        if prim.IsA(UsdGeom.Mesh) and prim.HasAPI(UsdPhysics.CollisionAPI):
            runtime['collision_meshes'].append(dict(path=str(prim.GetPath()),enabled=UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()))
        if prim.HasAPI(PhysxSchema.PhysxArticulationAPI):
            runtime['self_collision'].append(PhysxSchema.PhysxArticulationAPI(prim).GetEnabledSelfCollisionsAttr().Get())
        if prim.HasAPI(UsdPhysics.FilteredPairsAPI):
            for path in UsdPhysics.FilteredPairsAPI(prim).GetFilteredPairsRel().GetTargets():
                runtime['pair_filters'].append([prim.GetName(),str(path).rsplit('/',1)[-1]])
    runtime['gripper_mass_max_error_kg'] = max(abs(runtime['body_mass_kg'][i['link']]-i['mass_kg']) for i in source['gripper']['links'])
    target = robot.data.default_joint_pos.clone()
    center = robot.data.body_pos_w[0,bodies.index('tool_base_link')].cpu().tolist()
    sim.set_camera_view(eye=(center[0]+.32,center[1]-.40,center[2]+.25),
                        target=(center[0],center[1],center[2]+.085))
    window = ui.Window('RM65 native gripper | SIMULATION ONLY',width=540,height=145)
    with window.frame:
        with ui.VStack():
            ui.Label(f'Native STL | gravity ON | self collision ON ({len(runtime["pair_filters"])} internal pair filters)')
            ui.Label('ONE driven master + FIVE passive mimic followers; NOT pi0.5')
            label = ui.Label('PREVIEW: physics has not started')
    write_live(dict(state='preview_no_physics',step=0))
    start = time.monotonic()
    while time.monotonic()-start < 15 and launcher.app.is_running():
        sim.render()
        time.sleep(.03)
    phases = [('settle_open',0.,240),('close_030',.30,360),('hold_030',.30,180),
              ('close_065',.65,360),('hold_065',.65,180),('close_082',.82,240),
              ('hold_082',.82,180),('reopen',0.,480),('hold_open',0.,240)]
    samples, hold_errors, peak_contacts = [], [], {n:0. for n in moving}
    pair_peaks = {n:[0.]*len(filters) for n in moving}
    step, previous, stopped = 0, 0., None
    v0 = float(ball.data.root_lin_vel_w[0,2])
    acceleration = None
    with (args.output_dir/'telemetry.jsonl').open('x') as stream:
        for phase, end, count in phases:
            for j in range(count):
                started = time.monotonic()
                if not launcher.app.is_running():
                    stopped = 'window_closed'
                    break
                frac = (j+1)/count
                qtarget = previous+(end-previous)*(3*frac**2-2*frac**3)
                target[:,master] = qtarget
                robot.set_joint_position_target(target)
                robot.write_data_to_sim()
                sim.step(render=True)
                robot.update(dt)
                ball.update(dt)
                step += 1
                contact = {}
                for name, sensor in sensors.items():
                    sensor.update(dt, force_recompute=True)
                    force = float(torch.linalg.vector_norm(sensor.data.net_forces_w).item())
                    contact[name] = force
                    peak_contacts[name] = max(peak_contacts[name],force)
                    pairs = torch.linalg.vector_norm(sensor.data.force_matrix_w[0,0],dim=-1).cpu().tolist()
                    pair_peaks[name] = [max(a,b) for a,b in zip(pair_peaks[name],pairs)]
                finite = bool(torch.isfinite(robot.data.joint_pos).all() and torch.isfinite(robot.data.joint_vel).all())
                if step == 6:
                    acceleration = (float(ball.data.root_lin_vel_w[0,2])-v0)/(6*dt)
                q = robot.data.joint_pos[0,gripids].cpu().tolist()
                coupling = max(abs(value-q[0]) for value in q[1:])
                error = max(abs(value-qtarget) for value in q)
                if phase.startswith('hold_') and j > count-61:
                    hold_errors.append(error)
                record = dict(step=step,phase=phase,q_target_rad=qtarget,gripper_q_rad=q,
                    mimic_error_rad=coupling,tracking_error_rad=error,finite=finite,
                    max_joint_velocity_rad_s=float(robot.data.joint_vel.abs().max()),
                    max_arm_error_rad=float(robot.data.joint_pos[0,armids].abs().max()),
                    contacts_N=contact,body_positions_m={n:robot.data.body_pos_w[0,bodies.index(n)].cpu().tolist() for n in moving})
                if step%12 == 0 or not finite:
                    stream.write(json.dumps(record)+'\n')
                    stream.flush()
                    samples.append(record)
                    write_live(dict(record,state='running'))
                    label.text=f'RUNNING | {phase} | step {step} | target {qtarget:.3f} | master {q[0]:.3f}'
                if not finite or any(value < -.10 or value > 1.10 for value in q):
                    stopped = 'nonfinite_or_joint_out_of_bounds'
                    break
                time.sleep(max(0.,1/60-(time.monotonic()-started)))
            previous = end
            if stopped:
                break
    checks = dict(completed=stopped is None, finite=all(s['finite'] for s in samples),
        gravity_all_on=not runtime['gravity_disabled'], dynamics_all_on=not runtime['kinematic_bodies'],
        self_collision_on=bool(runtime['self_collision']) and all(runtime['self_collision']),
        all_native_colliders_enabled=len(runtime['collision_meshes'])==16 and all(m['enabled'] for m in runtime['collision_meshes']),
        original_gripper_masses=runtime['gripper_mass_max_error_kg'] < 1e-6,
        followers_not_driven=all(v==0 for v in runtime['follower_stiffness']),
        internal_pair_filter_contract=sorted(runtime['pair_filters']) == sorted(imported.get('derivation',{}).get('self_collision_filters_added',[])),
        freefall_acceleration_valid=acceleration is not None and abs(acceleration+9.81)<.05,
        master_reaches_close=bool(samples) and max(s['gripper_q_rad'][0] for s in samples)>.78,
        mimic_tracks_master=bool(samples) and max(s['mimic_error_rad'] for s in samples)<.03,
        hold_tracking=bool(hold_errors) and max(hold_errors)<.04,
        arm_stays_still=bool(samples) and max(s['max_arm_error_rad'] for s in samples)<.05)
    report = dict(schema='rm65_native_visible_dynamic_diagnostic_v1',
        status='pass' if all(checks.values()) else 'fail', checks=checks, stop_reason=stopped,
        simulation_only=True, pi05_used=False, training_ready=False, candidate=str(candidate),
        source_urdf_sha256=source['urdf_sha256'],import_audit_sha256=sha256(candidate/'import_audit.json'),
        asset_derivation=imported.get('derivation',{}),
        physics_steps=step,physics_dt_s=dt,gravity_m_s2=[0,0,-9.81],measured_freefall_m_s2=acceleration,
        runtime=runtime, joint_names=names,gripper_joint_order=[names[i] for i in gripids],
        max_hold_error_rad=max(hold_errors) if hold_errors else None,
        max_mimic_error_rad=max(s['mimic_error_rad'] for s in samples) if samples else None,
        self_contact_peak_N=peak_contacts, self_contact_filter_order=filters,self_contact_pair_peaks_N=pair_peaks,
        sensor_runtime_max_shape_capacity={n:int(s.body_physx_view.max_shapes) for n,s in sensors.items()},
        final_sample=samples[-1] if samples else None,
        limitations=['Empty-hand closure only; no grasp or household/policy success.',
                     'Convex decomposition is an approximation; no hardware calibration.'])
    with (args.output_dir/'report.json').open('x') as stream:
        json.dump(report,stream,indent=2)
    print(json.dumps(report,indent=2),flush=True)
    label.text=f'COMPLETED / PHYSICS PAUSED | {report["status"].upper()} | {step} steps'
    write_live(dict(state='completed_physics_paused',step=step,status=report['status']))
    start = time.monotonic()
    while time.monotonic()-start < args.hold_seconds and launcher.app.is_running():
        sim.render()
        time.sleep(.05)


try:
    main()
except BaseException:
    traceback.print_exc()
    write_live(dict(state='error',error=traceback.format_exc()))
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
else:
    launcher.app.close(skip_cleanup=True)
