"""Read-only multi-asset USD audit, including zero-pose geometry vs source URDF/STL."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback
import xml.etree.ElementTree as ET
from urllib.parse import urlparse,unquote
import numpy as np
from audit_robot_model_lineage import sha
from audit_gripper_visual_collision import stl_vertices,transformed,bounds
from household_grasp_calibration import origin_transform
from isaaclab.app import AppLauncher

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--generated-dir',type=Path,required=True)
parser.add_argument('--source-combined-urdf',type=Path,required=True)
parser.add_argument('--arm-usd',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
AppLauncher.add_app_launcher_args(parser)
args=parser.parse_args()
if args.output.exists():
    parser.error('fresh report required')
launcher=AppLauncher(args)
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema


def main():
    root=ET.parse(args.source_combined_urdf).getroot()
    joints={j.find('child').get('link'):j for j in root.findall('joint')}
    def frame(link):
        if link=='base_link':
            return np.eye(4)
        joint=joints[link]
        return frame(joint.find('parent').get('link'))@origin_transform(joint.find('origin'))
    expected={}
    for link in root.findall('link'):
        visual=link.find('visual')
        mesh=visual.find('geometry/mesh')
        path=Path(unquote(urlparse(mesh.get('filename')).path))
        points=transformed(stl_vertices(path),frame(link.get('name'))@origin_transform(visual.find('origin')))
        expected[link.get('name')]=bounds(points)
    paths=[args.arm_usd]+sorted(args.generated_dir.glob('*.usd'))+sorted(args.generated_dir.glob('native*/native.usd'))
    reports=[]
    for path in paths:
        stage=Usd.Stage.Open(str(path.resolve()))
        if stage is None:
            raise RuntimeError('cannot open '+str(path))
        units=float(UsdGeom.GetStageMetersPerUnit(stage))
        cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render','proxy','guide'],False,True)
        colliders,bodies,visuals,js,roots=[],[],[],[],[]
        for prim in Usd.PrimRange.Stage(stage,Usd.TraverseInstanceProxies()):
            name=str(prim.GetPath())
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                descendants=[str(p.GetPath()) for p in Usd.PrimRange(prim,Usd.TraverseInstanceProxies()) if p.IsA(UsdGeom.Mesh)]
                box=cache.ComputeWorldBound(prim).ComputeAlignedRange()
                colliders.append(dict(path=name,type=prim.GetTypeName(),is_gprim=prim.IsA(UsdGeom.Gprim),
                    enabled=UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get(),schemas=list(prim.GetAppliedSchemas()),
                    approximation=UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() if prim.HasAPI(UsdPhysics.MeshCollisionAPI) else None,
                    child_meshes=descendants,bounds_m=(np.array([list(box.GetMin()),list(box.GetMax())])*units).tolist()))
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                api=UsdPhysics.MassAPI(prim)
                bodies.append(dict(path=name,mass_kg=api.GetMassAttr().Get(),center_of_mass=str(api.GetCenterOfMassAttr().Get()),
                    diagonal_inertia=str(api.GetDiagonalInertiaAttr().Get()),principal_axes=str(api.GetPrincipalAxesAttr().Get()),
                    gravity_disabled=PhysxSchema.PhysxRigidBodyAPI(prim).GetDisableGravityAttr().Get(),
                    kinematic=UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get()))
            if prim.IsA(UsdGeom.Mesh) and '/visuals/' in name:
                part=next((p for p in name.split('/') if p in expected),None)
                box=cache.ComputeWorldBound(prim).ComputeAlignedRange()
                actual=np.array([list(box.GetMin()),list(box.GetMax())])*units
                visuals.append(dict(path=name,source_link=part,bounds_m=actual.tolist(),
                    source_zero_pose_aabb_error_m=float(np.max(np.abs(actual-expected[part]))) if part else None))
            if prim.IsA(UsdPhysics.Joint):
                drive=UsdPhysics.DriveAPI.Get(prim,'angular')
                js.append(dict(path=name,type=prim.GetTypeName(),schemas=list(prim.GetAppliedSchemas()),
                    attributes={a.GetName():str(a.Get()) for a in prim.GetAttributes() if a.GetName().startswith(('physics:','drive:','physxMimicJoint:'))},
                    relationships={r.GetName():[str(p) for p in r.GetTargets()] for r in prim.GetRelationships()},
                    angular_drive_type=drive.GetTypeAttr().Get() if drive else None))
            if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                roots.append(dict(path=name,self_collisions=PhysxSchema.PhysxArticulationAPI(prim).GetEnabledSelfCollisionsAttr().Get()))
        reports.append(dict(path=str(path.resolve()),sha256=sha(path),meters_per_unit=units,up_axis=str(UsdGeom.GetStageUpAxis(stage)),
            layers={l.realPath:sha(l.realPath) for l in stage.GetUsedLayers() if l.realPath},
            bodies=bodies,colliders=colliders,visuals=visuals,joints=js,articulation_roots=roots,
            non_gprim_collision_api_count=sum(not c['is_gprim'] for c in colliders),
            actual_gprim_collision_api_count=sum(c['is_gprim'] for c in colliders),
            max_source_visual_aabb_error_m=max([v['source_zero_pose_aabb_error_m'] for v in visuals if v['source_zero_pose_aabb_error_m'] is not None],default=None)))
    result=dict(schema='rm65_usd_model_lineage_audit_v1',read_only=True,physics_steps=0,
        source_combined_urdf_sha256=sha(args.source_combined_urdf),assets=reports,
        limitations=['Authored USD structure only; schema presence on Xform is not proof of cooked collision shape.',
                     'Zero-pose visual bounds compare frame/scale/geometry, not all motion or hardware accuracy.',
                     'Runtime drives, gravity and scene overrides are assessed separately from asset defaults.'])
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps([dict(path=r['path'],bodies=len(r['bodies']),gprim_colliders=r['actual_gprim_collision_api_count'],
        xform_colliders=r['non_gprim_collision_api_count'],visual_error_m=r['max_source_visual_aabb_error_m'],
        roots=r['articulation_roots']) for r in reports],indent=2),flush=True)


try:
    main()
except BaseException:
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
else:
    launcher.app.close(skip_cleanup=True)
