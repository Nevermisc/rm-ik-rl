"""Visible single exposed-marker native diagnostic; no policy or training data."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from build_native_gripper_candidate import sha256
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--protocol', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--hold-seconds', type=float, default=45.)
parser.add_argument('--asset-manifest', type=Path, required=True)
parser.add_argument('--object-id', default='ycb_large_marker', choices=['ycb_large_marker'])
parser.add_argument('--camera-rig', type=Path, required=True)
parser.add_argument('--object-collision-precision', action='store_true',
                    help='Require protocol-bound, temporary Object-only native cooking precision override')
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if not args.enable_cameras:
    parser.error('--enable_cameras required for real native RGB evidence')
if args.headless or not os.environ.get('DISPLAY'):
    parser.error('visible laboratory desktop required')
if args.output_dir.exists() or not 0 <= args.hold_seconds <= 180:
    parser.error('fresh output and bounded hold required')
candidate = args.candidate.resolve()
protocol = json.loads(args.protocol.read_text())
from native_object_collision_precision import validate_request, apply_scene_object_precision, PREFIX
try:
    validate_request(args.object_collision_precision, protocol)
except ValueError as exc:
    parser.error(str(exc))
previous_runtime_path=None
if args.object_collision_precision:
    previous_runtime_name=protocol.get('previous_runtime_preflight_path')
    if not isinstance(previous_runtime_name,str) or not previous_runtime_name:
        parser.error('precision comparison requires previous runtime preflight path')
    previous_runtime_path=Path(previous_runtime_name)
    if not previous_runtime_path.is_absolute():
        previous_runtime_path=Path(__file__).resolve().parents[1]/previous_runtime_path
    if sha256(previous_runtime_path)!=protocol.get('previous_runtime_preflight_sha256'):
        parser.error('previous runtime preflight identity mismatch')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import load_household
from openpi_extension.native_control_contract import load_control_contract
household=load_household(args.asset_manifest,args.object_id)
if protocol.get('object_id')!=args.object_id or protocol.get('object_package_sha256')!=household.asset_evidence['package_sha256']:
    parser.error('explicit household object/protocol identity mismatch')
if protocol.get('robot_y_offsets_m')!=[0.0] or not protocol.get('active_motion'):
    parser.error('single centre-case active diagnostic required')
if 'arm_effort_limits_Nm' not in protocol:
    parser.error('explicit source six-arm effort contract required; no 300 Nm fallback')
control_path=Path(__file__).resolve().parents[1]/'config/native_control_contract_v1.json'
if sha256(args.camera_rig)!=protocol.get('camera_rig_sha256') or sha256(control_path)!=protocol.get('control_contract_sha256'):
    parser.error('actual camera/control contract identity mismatch')
control_contract=load_control_contract(control_path,source_urdf=candidate/'native.urdf')
if (control_contract['arm_effort_caps_Nm']!=protocol['arm_effort_limits_Nm']
        or control_contract['physics_dt_s']!=protocol['physics_dt_s']
        or protocol.get('arm_drive_type_override')!='force'
        or protocol.get('solve_articulation_contact_last') is not True):
    parser.error('protocol differs from native simulation control contract')
fixed_geometry_contract=dict(support_size_world_m=[.03,.03,.04],catch_size_world_m=[.24,.30,.02],
    support_withdraw_distance_m=.10,support_lateral_clearance_m=.15,
    catch_top_below_initial_object_center_m=.16,object_center_flange_m=[0.,0.,.14],
    robot_base_z_m=.1,additional_object_scale=[1.,1.,1.],object_mass_kg=.02,
    object_material_static_friction=.7,object_material_dynamic_friction=.5,
    robot_material_static_friction=.5,robot_material_dynamic_friction=.5,
    master_close_target_rad=.82,master_effort_limit_Nm=1.,master_stiffness=2.,master_damping=.1,
    contact_point_force_min_N=.001,bilateral_pair_force_min_N=.02,
    source_inner_triangle_distance_tolerance_m=.0021,contact_normal_min_abs_alignment_with_inner_face=.95,
    contact_data_capacity_per_object=8192)
for key,value in fixed_geometry_contract.items():
    if protocol.get(key)!=value:
        parser.error('protocol differs from implemented native household geometry/contact contract: '+key)
source = json.loads((candidate/'source_audit.json').read_text())
imported = json.loads((candidate/'import_audit.json').read_text())
if imported['status'] != 'pass' or sha256(candidate/'native.usd') != protocol['candidate_root_sha256']:
    parser.error('candidate identity mismatch')
if sha256(candidate/'native.urdf') != source['urdf_sha256'] or source['urdf_sha256'] != protocol['source_urdf_sha256']:
    parser.error('source identity mismatch')
for filename, expected in dict(imported['composed_layer_sha256'], **source['mesh_sha256']).items():
    if sha256(filename) != expected:
        parser.error('source mesh or composed layer changed: '+filename)
for filename, expected in protocol.get('prerequisite_artifact_sha256',{}).items():
    if sha256(Path(filename)) != expected:
        parser.error('prerequisite evidence identity mismatch: '+filename)
args.output_dir.mkdir(parents=True, exist_ok=False)
snapshot_dir=args.output_dir/'source_snapshot'
snapshot_dir.mkdir()
code_names=['run_native_household_diagnostic.py','native_contact_geometry.py','native_contact_verdict.py',
            'native_household_geometry.py','native_object_collision_precision.py','audit_native_external_contact_geometry.py','audit_native_cooked_shapes.py','native_camera_probe.py',
            'native_active_motion.py','derive_native_collision_precision.py']
if protocol.get('active_motion'):
    code_names.append('native_active_verdict.py')
code_sources={filename:Path(__file__).with_name(filename) for filename in code_names}
code_sources['openpi_extension/camera_rig.py']=Path(__file__).resolve().parents[1]/'openpi_extension/camera_rig.py'
code_sources['openpi_extension/household_assets.py']=Path(__file__).resolve().parents[1]/'openpi_extension/household_assets.py'
code_sources['openpi_extension/native_control_contract.py']=Path(__file__).resolve().parents[1]/'openpi_extension/native_control_contract.py'
for filename,path in code_sources.items():
    (snapshot_dir/filename).parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,snapshot_dir/filename)
shutil.copyfile(args.asset_manifest,snapshot_dir/args.asset_manifest.name)
shutil.copyfile(args.camera_rig,snapshot_dir/args.camera_rig.name)
shutil.copyfile(control_path,snapshot_dir/control_path.name)
shutil.copyfile(args.protocol,snapshot_dir/args.protocol.name)
launcher = AppLauncher(args)

import numpy as np
import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.sensors import ContactSensor, ContactSensorCfg
from isaaclab.utils.math import matrix_from_quat
from isaacsim.core.utils.stage import get_current_stage
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema, Sdf, UsdShade, UsdUtils, PhysicsSchemaTools
import omni.ui as ui
from native_contact_geometry import load_inner_triangles, points_to_triangles_distances, scene_geometry
from native_contact_verdict import evaluate_trial
from native_active_motion import arm_phase_endpoints
from derive_native_collision_precision import stage_contract
from native_household_geometry import read_rigid_mesh, marker_initial_geometry, object_vertical_bounds, support_withdraw_offset
from native_camera_probe import NativeCameraProbe
from audit_native_cooked_shapes import convex_record


def save_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def live(value):
    tmp = args.output_dir/'live.tmp'
    tmp.write_text(json.dumps(dict(value, wall_time_unix=time.time()), allow_nan=False))
    tmp.replace(args.output_dir/'live.json')


def snapshot(name):
    """Capture the actual X11 desktop once per important phase; physics is unchanged."""
    try:
        from PIL import ImageGrab
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(args.output_dir/(name+'.png'))
        return True
    except Exception as exc:
        return str(exc)


def export_object_cooked(stage, object_path, source_geometry):
    """Capture the actual scene mesh's cooked hulls without a physics step."""
    from omni.physx import get_physx_cooking_interface
    from omni.physx.bindings._physx import PhysxCollisionRepresentationResult
    root=stage.GetPrimAtPath(object_path)
    meshes=[p for p in Usd.PrimRange(root,Usd.TraverseInstanceProxies())
            if p.IsA(UsdGeom.Mesh) and p.HasAPI(UsdPhysics.CollisionAPI)]
    if len(meshes)!=1:
        raise ValueError('exactly one household source mesh collider required')
    prim=meshes[0]; mesh=UsdGeom.Mesh(prim); cache=UsdGeom.XformCache()
    transform=cache.GetLocalToWorldTransform(prim)*cache.GetLocalToWorldTransform(root).GetInverse()
    matrix=np.array(transform,dtype=float)
    points=np.asarray(mesh.GetPointsAttr().Get(),dtype=float)
    body_points=points@matrix[:3,:3]+matrix[3,:3]
    unchanged=body_points.shape==source_geometry['vertices'].shape and np.allclose(body_points,source_geometry['vertices'],rtol=0,atol=1e-8)
    if not unchanged or UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()!='convexDecomposition':
        raise ValueError('spawned source object geometry/approximation changed')
    returned={}
    def callback(result,hulls):
        returned.update(result=str(result),valid=result==PhysxCollisionRepresentationResult.RESULT_VALID,
                        hulls=[convex_record(h) for h in hulls])
    stage_id=UsdUtils.StageCache.Get().Insert(stage).ToLongInt()
    get_physx_cooking_interface().request_convex_collision_representation(
        stage_id=stage_id,collision_prim_id=PhysicsSchemaTools.sdfPathToInt(prim.GetPath()),
        run_asynchronously=False,on_result=callback)
    if not returned.get('valid') or not returned['hulls']:
        raise ValueError('actual scene household hull export failed')
    bound_material,relationship=UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial('physics')
    material_prim=bound_material.GetPrim()
    raw=dict(object_id=args.object_id,mesh_path=str(prim.GetPath()),rigid_path=object_path,
        mesh_to_body_row_matrix=matrix.tolist(),source_usd_points=points.tolist(),
        source_face_vertex_indices=list(mesh.GetFaceVertexIndicesAttr().Get()),
        source_face_vertex_counts=list(mesh.GetFaceVertexCountsAttr().Get()),**returned)
    raw_path=args.output_dir/'object_cooked_raw.json'; save_json(raw_path,raw)
    return dict(mesh_path=str(prim.GetPath()),collision_enabled=bool(UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()),
        original_source_body_vertices_equal=unchanged,approximation=str(UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()),
        hull_count=len(returned['hulls']),raw_path=str(raw_path),raw_sha256=sha256(raw_path),
        mesh_to_body_row_matrix=matrix.tolist(),
        authored_cooking_parameters={a.GetName():str(a.Get()) for a in prim.GetAttributes()
            if a.HasAuthoredValueOpinion() and a.GetName().startswith('physxConvexDecompositionCollision:')},
        cooking_api_applied=prim.HasAPI(PhysxSchema.PhysxConvexDecompositionCollisionAPI),
        unapplied_engine_defaults_verified=False,
        material_path=str(material_prim.GetPath()),physics_material_attributes={a.GetName():str(a.Get())
            for a in material_prim.GetAttributes() if 'physics:' in a.GetName().lower() or 'physx' in a.GetName().lower()},
        source_asset_saved=False,physics_steps_during_export=0)


def main():
    dt = protocol['physics_dt_s']
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=dt, gravity=(0.,0.,-9.81), device=args.device,
        render=sim_utils.RenderCfg(antialiasing_mode='FXAA',enable_dlssg=False,enable_dl_denoiser=False)))
    import carb.settings
    carb.settings.get_settings().set('/rtx/post/motionblur/enabled',False)
    renderer_contract=dict(antialiasing_mode='FXAA',enable_dlssg=False,enable_dl_denoiser=False,
        motion_blur=False,physics_changed_by_renderer_configuration=False)
    sim_utils.GroundPlaneCfg().func('/World/Ground', sim_utils.GroundPlaneCfg())
    sim_utils.DomeLightCfg(intensity=1500.).func('/World/Light', sim_utils.DomeLightCfg(intensity=1500.))
    material = sim_utils.RigidBodyMaterialCfg(static_friction=.5, dynamic_friction=.5, restitution=0.,
                                             friction_combine_mode='average', restitution_combine_mode='average')
    material.func('/World/BenchMaterial', material)
    armq = protocol['arm_joint_targets_rad']
    geom = scene_geometry(candidate/'native.urdf', arm_joints=armq, base=[0,0,.1])
    source_object=read_rigid_mesh(household.usd_path)
    marker=marker_initial_geometry(geom['palm_position'],geom['palm_rotation'],source_object['vertices'])
    if (marker['support_size_world_m']!=protocol['support_size_world_m']
            or marker['catch_size_world_m']!=protocol['catch_size_world_m']
            or not np.allclose(support_withdraw_offset(1.),[protocol['support_lateral_clearance_m'],0.,-protocol['support_withdraw_distance_m']],rtol=0,atol=1e-15)):
        raise ValueError('geometry helper constants differ from the hash-bound protocol')
    if source_object['approximation']!='convexDecomposition' or abs(source_object['source_mass_kg']-household.mass_kg)>1e-6:
        raise ValueError('household source collision or mass differs from asset manifest')
    camera=NativeCameraProbe(args.camera_rig,args.output_dir,sim)
    face_triangles = load_inner_triangles(candidate/'native.urdf')
    face_normals = {}
    for name,triangles in face_triangles.items():
        normal=np.cross(triangles[0,1]-triangles[0,0],triangles[0,2]-triangles[0,0])
        face_normals[name]=normal/np.linalg.norm(normal)
    center0 = np.asarray(marker['position_world_m'])
    quat = tuple(marker['quat_wxyz'])
    body_names = [link.get('name') for link in ET.parse(candidate/'native.urdf').getroot().findall('link')]
    source_limits = {j.get('name'):[float(j.find('limit').get(k)) for k in ('lower','upper')]
                     for j in ET.parse(candidate/'native.urdf').getroot().findall('joint') if j.get('type')=='revolute'}
    source_masses = {link.get('name'):float(link.find('inertial/mass').get('value'))
                     for link in ET.parse(candidate/'native.urdf').getroot().findall('link')}
    source_arm_efforts={j.get('name'):float(j.find('limit').get('effort')) for j in
        ET.parse(candidate/'native.urdf').getroot().findall('joint') if j.get('name') in [f'joint_{i}' for i in range(1,7)]}
    arm_effort_cfg=300.
    if 'arm_effort_limits_Nm' in protocol:
        if protocol['arm_effort_limits_Nm']!=source_arm_efforts or not all(np.isfinite(v) and v>0 for v in source_arm_efforts.values()):
            raise ValueError('explicit arm effort limits must equal all six source URDF values')
        arm_effort_cfg=source_arm_efforts
    arm_endpoints=arm_phase_endpoints(protocol,source_limits)
    active_mode=protocol.get('active_motion',False)
    if active_mode:
        from native_active_verdict import evaluate_active_trial, ACTIVE_PHASE_COUNTS
        if [(phase,count) for phase,_,count in protocol['phases']] != list(ACTIVE_PHASE_COUNTS):
            raise ValueError('active protocol must match frozen verdict phase counts')
    cases = []
    for i, (width, offset) in enumerate([(float(np.ptp(source_object['vertices'][:,0])),0.)]):
        root = f'/World/Case{i}'
        center = center0 + np.array([0,offset,0])
        robot = Articulation(ArticulationCfg(prim_path=root+'/Robot',
            spawn=sim_utils.UsdFileCfg(usd_path=str(candidate/'native.usd'), activate_contact_sensors=True,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False, max_depenetration_velocity=.2),
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(enabled_self_collisions=True,
                    solver_position_iteration_count=32, solver_velocity_iteration_count=8)),
            init_state=ArticulationCfg.InitialStateCfg(pos=(0.,offset,.1),
                joint_pos={**{f'joint_{j+1}':q for j,q in enumerate(armq)},'tool_.*':0.}),
            actuators={
                'arm':ImplicitActuatorCfg(joint_names_expr=['joint_[1-6]'], effort_limit_sim=arm_effort_cfg,
                                          velocity_limit_sim=.5, stiffness=1000., damping=100.),
                'gripper_master':ImplicitActuatorCfg(joint_names_expr=['tool_gripper_joint'],
                    effort_limit_sim=1., velocity_limit_sim=2., stiffness=2., damping=.1)}))
        # Preserve the complete textured source package, mass, material, and mesh scale.
        obj = RigidObject(RigidObjectCfg(prim_path=root+'/Object',
            spawn=sim_utils.UsdFileCfg(usd_path=household.usd_path, scale=(1.,1.,1.), activate_contact_sensors=True,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False,
                    solver_position_iteration_count=32,solver_velocity_iteration_count=8,max_depenetration_velocity=.2),
                collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=.001,rest_offset=0.)),
            init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(center),rot=quat)))
        support_center = np.asarray(marker['support_center_world_m'])
        support = RigidObject(RigidObjectCfg(prim_path=root+'/Support',
            spawn=sim_utils.CuboidCfg(size=tuple(marker['support_size_world_m']),
                rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
                collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=.001,rest_offset=0.),
                physics_material=material,visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.2,.4,.8))),
            init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(support_center))))
        catch_top = marker['catch_top_world_m']
        catch = sim_utils.CuboidCfg(size=tuple(marker['catch_size_world_m']), collision_props=sim_utils.CollisionPropertiesCfg(),
            physics_material=material, visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.3,.35,.4)))
        catch.func(root+'/Catch',catch,translation=tuple(marker['catch_center_world_m']))
        # One object sensor, individually resolved body filters, all robot bodies included.
        filters = [root+'/Robot/'+n for n in body_names] + [root+'/Support',root+'/Catch/geometry/mesh']
        sensor = ContactSensor(ContactSensorCfg(prim_path=root+'/Object', filter_prim_paths_expr=filters,
            update_period=0., history_length=0, max_contact_data_count_per_prim=8192))
        arm_sensors = {n:ContactSensor(ContactSensorCfg(prim_path=root+'/Robot/'+n,
            filter_prim_paths_expr=[root+'/Robot/'+b for b in body_names],update_period=0.,history_length=0))
            for n in [f'link_{j}' for j in range(1,7)]}
        cases.append(dict(index=i,width=width,root=root,robot=robot,obj=obj,support=support,sensor=sensor,
            initial_center=center,support_initial=support_center,catch_top=catch_top,filter_names=body_names+['Support','Catch'],filter_paths=filters,
            samples=[],support_pose=None,arm_sensors=arm_sensors))
    probe = RigidObject(RigidObjectCfg(prim_path='/World/GravityProbe',
        spawn=sim_utils.SphereCfg(radius=.01,rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
            mass_props=sim_utils.MassPropertiesCfg(mass=.02),collision_props=sim_utils.CollisionPropertiesCfg()),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(.5,0,1.2))))
    stage = get_current_stage()
    object_precision_override=None
    if args.object_collision_precision:
        object_precision_override=apply_scene_object_precision(stage)
        object_precision_override['previous_runtime_preflight_path']=str(previous_runtime_path)
        object_precision_override['previous_runtime_preflight_sha256']=sha256(previous_runtime_path)
        save_json(args.output_dir/'scene_object_collision_precision_override.json',object_precision_override)
    # Bind a single disclosed material to all native robot colliders in this ephemeral scene.
    # No source USD or contact geometry is saved or altered.
    for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
        if '/Robot/' in str(prim.GetPath()) and prim.HasAPI(UsdPhysics.CollisionAPI):
            sim_utils.bind_physics_material(str(prim.GetPath()),'/World/BenchMaterial')
    if protocol.get('arm_drive_type_override') is not None:
        if protocol['arm_drive_type_override'] != 'force':
            raise ValueError('only explicit force-drive semantic diagnostic supported')
        before=stage_contract(stage,exclude_precision=False); changes=[]
        for c in cases:
            for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
                if not str(prim.GetPath()).startswith(c['root']+'/Robot/') or prim.GetName() not in [f'joint_{j}' for j in range(1,7)]:
                    continue
                drive=UsdPhysics.DriveAPI(prim,'angular')
                if drive.GetTypeAttr().Get() != 'acceleration':
                    raise ValueError('expected inherited acceleration drive for isolated comparison')
                drive.GetTypeAttr().Set('force')
                changes.append(str(prim.GetPath()))
        after=stage_contract(stage,exclude_precision=False)
        for path in changes:
            before[path]['attributes'].pop('drive:angular:physics:type')
            after[path]['attributes'].pop('drive:angular:physics:type')
        if len(changes)!=6*len(cases) or before!=after:
            raise ValueError('arm-drive-type-only scene contract failed')
        save_json(args.output_dir/'scene_arm_drive_override.json',dict(changed_joint_paths=changes,
            change='acceleration_to_force_only',unrelated_scene_attributes_equal=True,source_usd_saved=False,
            gain_force_cap_geometry_inertia_collision_unchanged=True,hardware_calibrated=False))
    if protocol.get('solve_articulation_contact_last') is not None:
        if protocol['solve_articulation_contact_last'] is not True:
            raise ValueError('only explicit contact-last diagnostic override supported')
        before=stage_contract(stage,exclude_precision=False)
        scene=stage.GetPrimAtPath(sim.cfg.physics_prim_path)
        key='physxScene:solveArticulationContactLast'
        old=scene.GetAttribute(key).Get()
        if old not in (None,False):
            raise ValueError('expected default contact-first order for isolated comparison')
        scene.CreateAttribute(key,Sdf.ValueTypeNames.Bool).Set(True)
        after=stage_contract(stage,exclude_precision=False)
        scene_path=str(scene.GetPath())
        before[scene_path]['attributes'].pop(key,None)
        after[scene_path]['attributes'].pop(key,None)
        if before!=after:
            raise ValueError('contact-last-only scene contract failed')
        save_json(args.output_dir/'scene_solver_order_override.json',dict(
            path=scene_path,attribute=key,before=old,after=True,
            unrelated_scene_attributes_equal=True,source_usd_saved=False))
    sim.reset()
    scene=stage.GetPrimAtPath(sim.cfg.physics_prim_path)
    scene_runtime={a.GetName():str(a.Get()) for a in scene.GetAttributes()}
    save_json(args.output_dir/'physics_scene_runtime.json',scene_runtime)
    if protocol.get('solve_articulation_contact_last') is True and scene.GetAttribute(
            'physxScene:solveArticulationContactLast').Get() is not True:
        raise RuntimeError('contact-last runtime scene contract failed')
    probe.reset()
    for c in cases:
        c['robot'].write_joint_state_to_sim(c['robot'].data.default_joint_pos.clone(),c['robot'].data.default_joint_vel.clone())
    sim.forward()
    runtime = []
    for c in cases:
        r=c['robot']; r.reset(); c['obj'].reset(); c['support'].reset()
        names=list(r.data.joint_names); bodies=list(r.data.body_names)
        c['names']=names; c['bodies']=bodies
        c['gripids']=[names.index(n) for n in [source['gripper']['master']]+source['gripper']['followers']]
        c['armids']=[names.index(f'joint_{j}') for j in range(1,7)]
        c['target']=r.data.default_joint_pos.clone()
        c['support_pose']=c['support'].data.default_root_state[:,:7].clone()
        limits=r.root_physx_view.get_dof_limits()[0].cpu().numpy()
        mass=dict(zip(bodies,r.root_physx_view.get_masses()[0].cpu().tolist()))
        item=dict(case=c['index'],body_mass_kg=mass,joint_limits_rad=dict(zip(names,limits.tolist())),
            joint_names=names,default_joint_pos_rad=r.data.default_joint_pos[0].cpu().tolist(),
            initial_joint_pos_rad=r.data.joint_pos[0].cpu().tolist(),
            joint_stiffness=r.data.joint_stiffness[0].cpu().tolist(),joint_damping=r.data.joint_damping[0].cpu().tolist(),
            joint_effort_limits=r.data.joint_effort_limits[0].cpu().tolist(),
            joint_limit_max_error_rad=max(float(np.max(np.abs(limits[names.index(n)]-v))) for n,v in source_limits.items()),
            gripper_mass_max_error_kg=max(abs(mass[v['link']]-v['mass_kg']) for v in source['gripper']['links']),
            robot_gravity_disabled=[],robot_kinematic=[],colliders=[],pair_filters=[],self_collision=[],
            follower_stiffness=r.data.joint_stiffness[0,c['gripids'][1:]].cpu().tolist(),
            follower_damping=r.data.joint_damping[0,c['gripids'][1:]].cpu().tolist(),
            actuators={k:list(v.joint_names) for k,v in r.actuators.items()},
            object_mass_kg=float(c['obj'].root_physx_view.get_masses()[0,0]),
            sensor_filter_count=c['sensor'].contact_physx_view.filter_count,
            expected_filter_order=c['filter_names'])
        for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
            path=str(prim.GetPath())
            if path.startswith(c['root']+'/Robot'):
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    if PhysxSchema.PhysxRigidBodyAPI(prim).GetDisableGravityAttr().Get(): item['robot_gravity_disabled'].append(path)
                    if UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get(): item['robot_kinematic'].append(path)
                if prim.HasAPI(UsdPhysics.CollisionAPI):
                    item['colliders'].append(dict(path=path,type=prim.GetTypeName(),enabled=UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()))
                if prim.HasAPI(PhysxSchema.PhysxArticulationAPI): item['self_collision'].append(PhysxSchema.PhysxArticulationAPI(prim).GetEnabledSelfCollisionsAttr().Get())
                if prim.HasAPI(UsdPhysics.FilteredPairsAPI):
                    item['pair_filters'].extend([[prim.GetName(),str(p).rsplit('/',1)[-1]] for p in UsdPhysics.FilteredPairsAPI(prim).GetFilteredPairsRel().GetTargets()])
        object_prim=stage.GetPrimAtPath(c['root']+'/Object')
        item['object_kinematic']=bool(UsdPhysics.RigidBodyAPI(object_prim).GetKinematicEnabledAttr().Get())
        item['object_gravity_disabled']=bool(PhysxSchema.PhysxRigidBodyAPI(object_prim).GetDisableGravityAttr().Get())
        item['object_runtime_com_position_xyz_principal_axes_xyzw']=c['obj'].root_physx_view.get_coms()[0].cpu().tolist()
        item['object_runtime_inertia_column_major_kg_m2']=c['obj'].root_physx_view.get_inertias()[0].cpu().tolist()
        item['object_runtime_material_static_dynamic_restitution']=c['obj'].root_physx_view.get_material_properties()[0].cpu().tolist()
        item['object_cooked_geometry']=export_object_cooked(stage,c['root']+'/Object',source_object)
        item['object_collision_precision_override']=object_precision_override
        inertia=np.asarray(item['object_runtime_inertia_column_major_kg_m2']).reshape(3,3,order='F')
        material_values=np.asarray(item['object_runtime_material_static_dynamic_restitution'])
        item['physx_dof_stiffness']=r.root_physx_view.get_dof_stiffnesses()[0].cpu().tolist()
        item['physx_dof_damping']=r.root_physx_view.get_dof_dampings()[0].cpu().tolist()
        item['physx_dof_max_force']=r.root_physx_view.get_dof_max_forces()[0].cpu().tolist()
        item['expected_arm_effort_limits_Nm']=arm_effort_cfg if isinstance(arm_effort_cfg,dict) else {
            f'joint_{i}':arm_effort_cfg for i in range(1,7)}
        item['usd_drives']={}
        for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
            if str(prim.GetPath()).startswith(c['root']+'/Robot') and prim.IsA(UsdPhysics.Joint):
                item['usd_drives'][prim.GetName()]={a.GetName():str(a.Get()) for a in prim.GetAttributes() if 'drive:' in a.GetName()}
        item['all_robot_mass_max_error_kg']=max(abs(mass[n]-v) for n,v in source_masses.items())
        def flatten_paths(value):
            if isinstance(value,(list,tuple)):
                return [s for v in value for s in flatten_paths(v)]
            return [str(value)]
        item['actual_filter_paths']=flatten_paths(c['sensor'].contact_physx_view.filter_paths)
        item['expected_filter_paths']=c['filter_paths']
        order_valid=len(item['actual_filter_paths'])==len(c['filter_paths']) and all(
            actual==expected or actual.startswith(expected+'/')
            for actual,expected in zip(item['actual_filter_paths'],c['filter_paths']))
        item['checks']=dict(source_limits=item['joint_limit_max_error_rad']<1e-6,
            source_gripper_masses=item['gripper_mass_max_error_kg']<1e-6,
            source_all_robot_masses=item['all_robot_mass_max_error_kg']<1e-6,
            gravity=not item['robot_gravity_disabled'] and not item['object_gravity_disabled'],
            dynamics=not item['robot_kinematic'] and not item['object_kinematic'],
            object_mass=abs(item['object_mass_kg']-household.mass_kg)<1e-6,
            original_16_meshes=len(item['colliders'])==16 and all(v['enabled'] and v['type']=='Mesh' for v in item['colliders']),
            self_collision=bool(item['self_collision']) and all(item['self_collision']),
            internal_filters=sorted(item['pair_filters'])==sorted(imported['derivation']['self_collision_filters_added']),
            passive_followers=all(v==0 for v in item['follower_stiffness']+item['follower_damping']),
            single_master=item['actuators']['gripper_master']==['tool_gripper_joint'],
            sensor_filter_count=item['sensor_filter_count']==len(c['filter_names']),sensor_filter_order=order_valid)
        item['checks']['arm_drive_type_contract']=all(item['usd_drives'][f'joint_{j}']['drive:angular:physics:type']==
            protocol.get('arm_drive_type_override','acceleration') for j in range(1,7))
        item['checks']['arm_effort_limits_contract']=all(abs(item['physx_dof_max_force'][names.index(name)]-value)<1e-5
            for name,value in item['expected_arm_effort_limits_Nm'].items())
        item['checks']['source_object_mesh_and_cooking']=item['object_cooked_geometry']['original_source_body_vertices_equal'] and item['object_cooked_geometry']['collision_enabled'] and item['object_cooked_geometry']['hull_count']>0
        if object_precision_override is not None:
            expected_cook={PREFIX+k:str(v) for k,v in object_precision_override['actual_schema_typed_parameters'].items()}
            item['checks']['object_precision_after_reset']=(item['object_cooked_geometry']['cooking_api_applied'] and
                item['object_cooked_geometry']['authored_cooking_parameters']==expected_cook)
        item['checks']['source_object_material']=bool(material_values.size and np.allclose(material_values,[.7,.5,0.],rtol=0,atol=1e-6))
        item['checks']['object_runtime_inertia_valid']=bool(np.isfinite(inertia).all() and np.all(np.linalg.eigvalsh(inertia)>0))
        item['checks']['object_runtime_com_finite']=bool(np.isfinite(item['object_runtime_com_position_xyz_principal_axes_xyzw']).all())
        c['limits']=limits; runtime.append(item)
    save_json(args.output_dir/'runtime_preflight.json',runtime)
    if not all(all(r['checks'].values()) for r in runtime):
        raise RuntimeError('runtime preflight failed before physics; see runtime_preflight.json')
    code_hashes={n:sha256(path) for n,path in code_sources.items()}
    save_json(args.output_dir/'manifest.json',dict(protocol=protocol,protocol_sha256=sha256(args.protocol),
        household_object=household.metadata(),asset_manifest_sha256=sha256(args.asset_manifest),
        object_source_geometry={k:v for k,v in source_object.items() if k not in ('vertices','indices')},
        object_mesh_bounds_local_m=[source_object['vertices'].min(0).tolist(),source_object['vertices'].max(0).tolist()],
        object_spawn_scale=[1.,1.,1.],marker_initial_geometry=marker,camera=camera.manifest(),
        object_pose_origin_rule='source rigid root origin at palm[0,0,.14]; bounds centre is not recentered',
        verified_control_contract=control_contract,
        object_collision_precision_override=object_precision_override,
        renderer_contract=renderer_contract,
        object_material_policy='source package material retained (authored static .7/dynamic .5); runtime properties exported',
        code_sha256=code_hashes,source_audit_sha256=sha256(candidate/'source_audit.json'),
        import_audit_sha256=sha256(candidate/'import_audit.json'),composed_layers=imported['composed_layer_sha256'],
        arm_phase_endpoints_rad=arm_endpoints,active_motion=active_mode,arm_effort_limits=arm_effort_cfg,
        source_mesh_sha256=source['mesh_sha256'],object_control='initial state only; no later object writes/forces',
        support_control='three segments: down40mm, +X150mm while above catch, down60mm; total down100mm; object never written',
        torque_telemetry_semantics='Implicit actuator torque is a PD estimate, not measured PhysX servo force. get_dof_actuation_forces contains explicit input only.',
        pi05_used=False,training_ready=False))
    sim.set_camera_view(eye=(-1.2,-1.65,1.25),target=(-.15,0,.68))
    settings_window=ui.Workspace.get_window('Simulation Settings')
    if settings_window is not None: settings_window.visible=False
    window=ui.Window('RM65 native contact bench | SIMULATION ONLY',width=830,height=115,position_x=10,position_y=590)
    with window.frame:
        with ui.VStack():
            ui.Label('Exposed development marker | original texture/geometry/20g assumption | NO pi0.5')
            ui.Label('Source STL fingers | ACTIVE lift + transport diagnostic' if active_mode else
                     'Source STL fingers | support withdrawal is NOT active lift or transport')
            label=ui.Label('PREVIEW: runtime checks passed; physics not started')
    start=time.monotonic(); live(dict(state='preview_no_physics',step=0))
    while time.monotonic()-start<20 and launcher.app.is_running(): sim.render(); time.sleep(.03)
    camera.capture(cases[0]['robot'],'preview',0,dt)
    snapshots={'preview':snapshot('desktop_preview')}
    stop=None; step=0; previous=0.; acceleration=None
    v0=float(probe.data.root_lin_vel_w[0,2])
    with (args.output_dir/'telemetry.jsonl').open('x') as stream:
        for phase,end,count in protocol['phases']:
            arm_start,arm_end=[np.array(values) for values in arm_endpoints[phase]]
            for j in range(count):
                started=time.monotonic()
                if not launcher.app.is_running(): stop='window_closed'; break
                f=(j+1)/count; smooth=3*f*f-2*f*f*f; qt=previous+(end-previous)*smooth
                for c in cases:
                    c['target'][:,c['gripids'][0]]=qt
                    c['target'][:,c['armids']]=torch.as_tensor(arm_start+(arm_end-arm_start)*smooth,device=c['target'].device,dtype=c['target'].dtype)
                    c['robot'].set_joint_position_target(c['target']); c['robot'].write_data_to_sim()
                    if phase=='withdraw_support':
                        support_delta=support_withdraw_offset(smooth)
                        c['support_pose'][:,:3]=torch.as_tensor(c['support_initial']+support_delta,device=c['support_pose'].device,dtype=c['support_pose'].dtype)
                        c['support'].write_root_pose_to_sim(c['support_pose'])
                sim.step(render=True); step+=1; probe.update(dt)
                if step==6: acceleration=(float(probe.data.root_lin_vel_w[0,2])-v0)/(6*dt)
                records=[]
                for c in cases:
                    r=c['robot']; o=c['obj']; sensor=c['sensor']
                    r.update(dt); o.update(dt); c['support'].update(dt); sensor.update(dt,force_recompute=True)
                    force_matrix=sensor.data.force_matrix_w[0,0].cpu().numpy()
                    pair_norm=np.linalg.norm(force_matrix,axis=-1)
                    forces,points,normals,seps,counts,starts=sensor.contact_physx_view.get_contact_data(dt=dt)
                    forces=forces.cpu().numpy().reshape(-1); points=points.cpu().numpy(); normals=normals.cpu().numpy(); seps=seps.cpu().numpy().reshape(-1)
                    counts=counts.cpu().numpy().reshape(-1); starts=starts.cpu().numpy().reshape(-1)
                    raw=[]; faces={}; pair_abs=np.zeros(len(counts)); saturated=bool(counts.sum()>=8192)
                    face_pose={}
                    for name in face_triangles:
                        bi=c['bodies'].index(name)
                        face_pose[name]=(r.data.body_pos_w[0,bi].cpu().numpy(),
                            matrix_from_quat(r.data.body_quat_w[0,bi]).cpu().numpy())
                    for fi,name in enumerate(c['filter_names']):
                        details=[]
                        face_data={}
                        if name in face_triangles:
                            indices=np.array([ci for ci in range(int(starts[fi]),int(starts[fi]+counts[fi]))
                                              if 0<=ci<len(forces)],dtype=int)
                            position,rot=face_pose[name]
                            local_points=(points[indices]-position)@rot
                            distances=points_to_triangles_distances(local_points,face_triangles[name])
                            alignments=np.abs(normals[indices]@(rot@face_normals[name]))
                            face_data={ci:(local,dist,alignment) for ci,local,dist,alignment in
                                       zip(indices,local_points,distances,alignments)}
                        for ci in range(int(starts[fi]),int(starts[fi]+counts[fi])):
                            if ci<0 or ci>=len(forces): saturated=True; continue
                            row=dict(force_N=float(forces[ci]),point_world_m=points[ci].tolist(),normal_world=normals[ci].tolist(),separation_m=float(seps[ci]))
                            pair_abs[fi]+=abs(float(forces[ci]))
                            if name in face_triangles:
                                local,distance,alignment=face_data[ci]
                                row['point_link_m']=local.tolist()
                                row['source_inner_face_distance_m']=float(distance)
                                row['inner_face_normal_abs_alignment']=float(alignment)
                            details.append(row)
                        if details: raw.append(dict(body=name,contacts=details))
                        if name in face_triangles:
                            active=[v for v in details if abs(v['force_N'])>.001]
                            faces[name]=bool(pair_abs[fi]>.02 and active and all(
                                v['source_inner_face_distance_m']<=.0021 and v['inner_face_normal_abs_alignment']>=.95 for v in active))
                    pos=o.data.root_pos_w[0].cpu().numpy()
                    orot=matrix_from_quat(o.data.root_quat_w[0]).cpu().numpy()
                    source_bottom,source_top=object_vertical_bounds(pos,o.data.root_quat_w[0].cpu().numpy(),source_object['vertices'])
                    qall=r.data.joint_pos[0].cpu().numpy(); q=qall[c['gripids']]
                    violation=float(np.maximum(c['limits'][:,0]-qall,qall-c['limits'][:,1]).max(initial=0))
                    finite=bool(np.isfinite(qall).all() and torch.isfinite(r.data.joint_vel).all() and torch.isfinite(o.data.root_state_w).all() and np.isfinite(force_matrix).all())
                    other=[pair_abs[k] for k,n in enumerate(body_names) if n not in face_triangles]
                    arm_self={}
                    for n,s in c['arm_sensors'].items():
                        s.update(dt,force_recompute=True)
                        arm_self[n]=dict(zip(body_names,torch.linalg.vector_norm(s.data.force_matrix_w[0,0],dim=-1).cpu().tolist()))
                    record=dict(case_index=c['index'],object_id=args.object_id,width_m=c['width'],step=step,phase=phase,physics_time_s=step*dt,
                        object_source_bottom_world_m=source_bottom,object_source_top_world_m=source_top,
                        finite=finite,bilateral_native_face_contact=all(faces.get(n,False) for n in face_triangles),
                        other_robot_contact_N=float(sum(other)),support_contact_N=float(pair_abs[-2]),
                        object_pos_m=pos.tolist(),object_speed_m_s=float(torch.linalg.vector_norm(o.data.root_lin_vel_w[0])),
                        object_quat_wxyz=o.data.root_quat_w[0].cpu().tolist(),object_angular_velocity_rad_s=o.data.root_ang_vel_w[0].cpu().tolist(),
                        object_linear_velocity_world_m_s=o.data.root_lin_vel_w[0].cpu().tolist(),
                        fingertip_pose_world={name:dict(position_m=r.data.body_pos_w[0,c['bodies'].index(name)].cpu().tolist(),
                            quat_wxyz=r.data.body_quat_w[0,c['bodies'].index(name)].cpu().tolist()) for name in face_triangles},
                        palm_pose_world=dict(position_m=r.data.body_pos_w[0,c['bodies'].index('tool_base_link')].cpu().tolist(),
                            quat_wxyz=r.data.body_quat_w[0,c['bodies'].index('tool_base_link')].cpu().tolist()),
                        gripper_q_rad=q.tolist(),q_target_rad=qt,mimic_error_rad=float(np.max(np.abs(q[1:]-q[0]))),
                        joint_limit_violation_rad=violation,
                        support_clearance_m=float(source_bottom-(float(c['support'].data.root_pos_w[0,2])+marker['support_size_world_m'][2]/2)),
                        all_robot_contact_N=float(pair_abs[:len(body_names)].sum()),contact_buffer_saturated=saturated,
                        contact_pairs_N=dict(zip(c['filter_names'],pair_abs.tolist())),contact_pair_net_norm_N=dict(zip(c['filter_names'],pair_norm.tolist())),raw_contacts=raw,
                        contact_pair_net_force_world_N=dict(zip(c['filter_names'],force_matrix.tolist())),
                        arm_max_error_rad=float(np.abs(qall[c['armids']]-c['target'][0,c['armids']].cpu().numpy()).max()),
                        all_joint_pos_rad=qall.tolist(),all_joint_target_rad=c['target'][0].cpu().tolist(),
                        physx_joint_position_targets_rad=r.root_physx_view.get_dof_position_targets()[0].cpu().tolist(),
                        physx_joint_velocity_targets_rad_s=r.root_physx_view.get_dof_velocity_targets()[0].cpu().tolist(),
                        physx_joint_actuation_forces_Nm=r.root_physx_view.get_dof_actuation_forces()[0].cpu().tolist(),
                        all_joint_velocity_rad_s=r.data.joint_vel[0].cpu().tolist(),
                        implicit_estimated_joint_torque_Nm=r.data.applied_torque[0].cpu().tolist(),arm_self_contact_N=arm_self,
                        master_implicit_estimated_torque_Nm=float(r.data.applied_torque[0,c['gripids'][0]]))
                    c['samples'].append(record); records.append(record)
                    stream.write(json.dumps(record,allow_nan=False)+'\n')
                    if not finite or violation>.03 or record['mimic_error_rad']>.08 or record['arm_max_error_rad']>.1 or saturated:
                        stop='numerical_joint_or_instrumentation_abort'
                if step%12==0 or stop:
                    stream.flush()
                    live(dict(state='running' if not stop else 'aborted',step=step,phase=phase,
                        cases=[{k:r[k] for k in ('width_m','bilateral_native_face_contact','object_pos_m','support_contact_N','other_robot_contact_N','gripper_q_rad')} for r in records]))
                    label.text=f'RUNNING | {phase} | step {step} | native bilateral: '+str([r['bilateral_native_face_contact'] for r in records])
                if stop: break
                time.sleep(max(0.,1/60-(time.monotonic()-started)))
            camera.capture(cases[0]['robot'],phase,step,dt)
            snapshots[phase]=snapshot('desktop_'+phase)
            previous=end
            if stop: break
    evaluator=evaluate_active_trial if active_mode else evaluate_trial
    verdicts=[dict(width_m=c['width'],verdict=evaluator(c['samples'],dt=dt)) for c in cases]
    gravity_ok=acceleration is not None and abs(acceleration+9.81)<.05
    for c,trial in zip(cases,verdicts):
        samples=c['samples']
        complete_counts=all(sum(s['phase']==phase for s in samples)==count for phase,_,count in protocol['phases'])
        trial['verdict']['gates']['runtime_freefall_gravity']=gravity_ok
        trial['verdict']['gates']['runner_completed']=stop is None
        trial['verdict']['gates']['protocol_phase_counts_complete']=complete_counts
        if not gravity_ok or stop is not None or not complete_counts:
            trial['verdict'].update(status='fail',diagnostic_success=False,gate_passed=False,
                                   active_lift_validated=False,transport_validated=False)
            trial['verdict']['failure_reasons'].append('runner_or_runtime_gravity_gate_failed')
    camera_report=camera.finish()
    source_object_unchanged=sha256(household.usd_path)==household.asset_evidence['package_sha256']
    source_textures_unchanged=all(sha256(Path(household.usd_path).parent/texture['relative_path'])==texture['sha256']
        for texture in household.asset_evidence['copied_textures'])
    source_robot_unchanged=all(sha256(path)==digest for path,digest in
        dict(imported['composed_layer_sha256'],**source['mesh_sha256']).items())
    source_robot_unchanged=source_robot_unchanged and sha256(candidate/'native.usd')==protocol['candidate_root_sha256'] and sha256(candidate/'native.urdf')==protocol['source_urdf_sha256']
    if not source_object_unchanged or not source_robot_unchanged or not source_textures_unchanged:
        raise RuntimeError('source asset identity changed during household diagnostic')
    report=dict(schema='rm65_native_household_diagnostic_v1',object_id=args.object_id,
        development_object_previously_exposed=True,camera_report=camera_report,simulation_only=True,pi05_used=False,training_ready=False,
        source_object_unchanged=source_object_unchanged,source_robot_unchanged=source_robot_unchanged,
        source_textures_unchanged=source_textures_unchanged,
        object_collision_precision_override=object_precision_override,
        deployment_accepted=False,active_lift_or_transport_tested=active_mode and any(
            s['phase']=='active_lift' for s in cases[0]['samples']),stop_reason=stop,physics_steps=step,
        measured_freefall_m_s2=acceleration,gravity_probe_pass=gravity_ok,
        runtime_preflight_pass=True,trials=verdicts,desktop_snapshots=snapshots,
        status='completed_diagnostics' if stop is None else 'aborted_diagnostics',
        limitations=['One previously exposed textured marker, one declared pose/path; no unseen-object or success-rate claim.',
                    'Source mesh/material retained; 20g is a project simulation assumption, not measured object mass.',
                    'Source object COM/inertia were not authored; actual runtime values and cooked hulls are exported.',
                    'When explicitly requested, six Object-only cooking attributes and their API are authored in the temporary scene; automatic runtime COM/inertia may change as dependent results.',
                    'Camera RGB evidence requires independent visual review; no semantic occlusion area or training admission.',
                    '1 Nm and rigid mimic remain diagnostic settings, not hardware calibration.',
                    'Active motion is scripted; a development object diagnostic is not policy or household generalization validation.' if active_mode else
                    'No active lift, transport, household appearance, PI training or policy evaluation.',
                    'Original COM and installation provenance questions remain open.'])
    save_json(args.output_dir/'report.json',report)
    live(dict(state='completed_physics_paused',step=step,status=report['status']))
    label.text='COMPLETED / PHYSICS PAUSED | see single-marker contact verdict | NOT pi0.5'
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    start=time.monotonic()
    while time.monotonic()-start<args.hold_seconds and launcher.app.is_running(): sim.render(); time.sleep(.05)


try:
    main()
except BaseException:
    traceback.print_exc()
    live(dict(state='error',error=traceback.format_exc()))
    if not (args.output_dir/'report.json').exists():
        save_json(args.output_dir/'report.json',dict(schema='rm65_native_contact_bench_error_v1',status='error',
            simulation_only=True,pi05_used=False,training_ready=False,deployment_accepted=False,error=traceback.format_exc()))
    sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
else:
    launcher.app.close(skip_cleanup=True)
