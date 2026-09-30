"""Inspect composed USD gripper geometry without running physics or editing assets."""
import argparse
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--usd', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output.exists():
    parser.error('new output required')
launcher = AppLauncher(args)
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema
import numpy as np
from audit_gripper_visual_collision import aabb_separation

try:
    stage = Usd.Stage.Open(str(args.usd.resolve()))
    if stage is None:
        raise ValueError('USD did not open')
    # Imported URDF collision shapes use guide purpose and are invisible by design.
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default','render','proxy','guide'], useExtentsHint=False, ignoreVisibility=True)
    records = []
    for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
        path = str(prim.GetPath())
        if not any(part.startswith('tool_') for part in path.split('/')) or not prim.IsA(UsdGeom.Boundable):
            continue
        aligned = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if aligned.IsEmpty():
            continue
        low, high = list(aligned.GetMin()), list(aligned.GetMax())
        if not np.isfinite([low,high]).all():
            raise ValueError('invalid geometry bounds: ' + path)
        collision = prim.HasAPI(UsdPhysics.CollisionAPI) or '/collisions/' in path
        mesh_collision = UsdPhysics.MeshCollisionAPI(prim)
        record = dict(path=path, type=str(prim.GetTypeName()), collision=collision,
            purpose=str(UsdGeom.Imageable(prim).ComputePurpose()),
            authored_visibility=str(UsdGeom.Imageable(prim).ComputeVisibility()),
            world_aabb_m=[low,high], approximation=str(mesh_collision.GetApproximationAttr().Get()) if mesh_collision else None)
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            record['collision_enabled'] = UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get()
        records.append(record)
    pads = [r for r in records if 'contact_pad_box' in r['path'] and r['collision']]
    visuals = [r for r in records if not r['collision'] and r['authored_visibility'] != 'invisible']
    if len(pads) != 2 or not visuals:
        print('GEOMETRY_INVENTORY=' + json.dumps(records), flush=True)
        print('PAD_PRIMS=' + json.dumps([str(p.GetPath()) for p in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()) if 'pad' in str(p.GetPath())]), flush=True)
        raise ValueError(f'expected two pads and original visual geometry; got {len(pads)} pads, {len(visuals)} visuals')
    distances = []
    for pad in pads:
        candidates = [(aabb_separation(np.array(pad['world_aabb_m']),np.array(v['world_aabb_m'])),v['path']) for v in visuals]
        gap, closest = min(candidates)
        distances.append(dict(pad=pad['path'], nearest_visual=closest, aabb_gap_lower_bound_m=gap,
                              collision_enabled=pad.get('collision_enabled')))
    layers = {}
    for layer in stage.GetUsedLayers():
        if layer.realPath:
            layers[layer.realPath] = hashlib.sha256(Path(layer.realPath).read_bytes()).hexdigest()
    report = dict(schema='rm65_imported_gripper_geometry_audit_v1', simulation_only=True,
        physics_steps_executed=0, asset_modified=False, usd=str(args.usd), layer_sha256=layers,
        stage_meters_per_unit=UsdGeom.GetStageMetersPerUnit(stage),
        geometry=records, pad_visual_separation=distances,
        detached_pad_collision_enabled=all(d['aabb_gap_lower_bound_m'] > .001 and d['collision_enabled'] is True for d in distances),
        training_ready=False, native_gripper_validated=False,
        limitations=['Composed USD at authored default transforms, not dynamic PhysX hull extraction.',
                     'Positive bounds separation proves a geometric gap; overlap would not prove contact.'])
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(dict(pad_visual_separation=distances, geometry_count=len(records),
                         detached_pad_collision_enabled=report['detached_pad_collision_enabled']), indent=2), flush=True)
except BaseException:
    # SimulationApp immediate close otherwise swallows pending exceptions with exit 0.
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
else:
    launcher.app.close(skip_cleanup=True)
