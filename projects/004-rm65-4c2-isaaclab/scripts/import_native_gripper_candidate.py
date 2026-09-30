"""Import a fresh native candidate and audit authored geometry/coupling; zero physics steps."""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback
from build_native_gripper_candidate import sha256
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
root = args.candidate.resolve()
usd = root / 'native.usd'
report_path = root / 'import_audit.json'
if usd.exists() or report_path.exists() or (root/'configuration').exists():
    parser.error('fresh USD and configuration paths required')
source = json.loads((root/'source_audit.json').read_text())
if sha256(root/'native.urdf') != source['urdf_sha256']:
    parser.error('source URDF changed since audit')
for filename, expected in source['mesh_sha256'].items():
    if sha256(filename) != expected:
        parser.error('source mesh changed since audit')
launcher = AppLauncher(args)

import numpy as np
import omni.kit.commands
from isaacsim.core.utils.extensions import enable_extension
from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema


def main():
    enable_extension('isaacsim.asset.importer.urdf')
    launcher.app.update()
    status, config = omni.kit.commands.execute('URDFCreateImportConfig')
    if not status:
        raise RuntimeError('import config failed')
    config.fix_base = True
    config.merge_fixed_joints = False
    config.make_default_prim = True
    config.create_physics_scene = False
    config.import_inertia_tensor = True
    config.self_collision = True
    config.parse_mimic = True
    config.convex_decomp = True
    status, imported = omni.kit.commands.execute('URDFParseAndImportFile',
        urdf_path=str(root/'native.urdf'), import_config=config, dest_path=str(usd))
    if not status:
        raise RuntimeError('native URDF import failed')
    launcher.app.update()
    stage = Usd.Stage.Open(str(usd))
    if stage is None:
        raise RuntimeError('missing imported stage')
    # Author overrides in this new root layer only; source/historical layers remain untouched.
    for prim in list(stage.Traverse()):
        if prim.IsInstance():
            prim.SetInstanceable(False)
    collider_repairs = []
    for prim in list(stage.Traverse()):
        if not prim.HasAPI(UsdPhysics.CollisionAPI) or prim.IsA(UsdGeom.Gprim):
            continue
        if '/collisions/' not in str(prim.GetPath()):
            raise RuntimeError('unexpected non-mesh collider outside source collision hierarchy')
        children = [p for p in Usd.PrimRange(prim) if p.IsA(UsdGeom.Mesh)]
        if len(children) != 1:
            raise RuntimeError('ambiguous imported collider subtree: '+str(prim.GetPath()))
        mesh = children[0]
        prim.RemoveAPI(UsdPhysics.CollisionAPI)
        prim.RemoveAPI(UsdPhysics.MeshCollisionAPI)
        UsdPhysics.CollisionAPI.Apply(mesh).CreateCollisionEnabledAttr(True)
        UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr('convexDecomposition')
        collider_repairs.append(dict(from_xform=str(prim.GetPath()), to_mesh=str(mesh.GetPath())))
    for prim in stage.Traverse():
        if prim.HasAPI(UsdPhysics.CollisionAPI):
            PhysxSchema.PhysxCollisionAPI.Apply(prim).CreateContactOffsetAttr(.001)
            PhysxSchema.PhysxCollisionAPI.Apply(prim).CreateRestOffsetAttr(0.)
    followers = set(source['gripper']['followers'])
    found_followers, drives = [], []
    for prim in stage.Traverse():
        if not prim.IsA(UsdPhysics.Joint):
            continue
        if prim.GetName() in followers:
            schemas = [str(s) for s in prim.GetAppliedSchemas() if 'Mimic' in str(s)]
            if len(schemas) != 1:
                raise RuntimeError('expected one PhysX mimic on '+str(prim.GetPath()))
            if prim.HasAPI(UsdPhysics.DriveAPI, 'angular'):
                prim.RemoveAPI(UsdPhysics.DriveAPI, 'angular')
            found_followers.append(dict(name=prim.GetName(), schemas=schemas,
                mimic_attributes={a.GetName():str(a.Get()) for a in prim.GetAttributes() if 'mimic' in a.GetName().lower()},
                mimic_relationships={r.GetName():[str(p) for p in r.GetTargets()] for r in prim.GetRelationships() if 'mimic' in r.GetName().lower()}))
        elif prim.GetName() == 'tool_gripper_joint':
            drive = UsdPhysics.DriveAPI.Apply(prim, 'angular')
            drive.CreateTypeAttr('force')
            drive.CreateMaxForceAttr(1.)
            # Isaac Lab sets gains with the appropriate radians/degrees conversion on load.
            drives.append(str(prim.GetPath()))
    if len(found_followers) != 5 or len(drives) != 1:
        raise RuntimeError('incomplete native coupling')
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default','render','proxy','guide'], useExtentsHint=False, ignoreVisibility=True)
    meshes = []
    for prim in Usd.PrimRange.Stage(stage, Usd.TraverseInstanceProxies()):
        path = str(prim.GetPath())
        if not prim.IsA(UsdGeom.Mesh) or '/tool_' not in path:
            continue
        box = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        coll = prim.HasAPI(UsdPhysics.CollisionAPI)
        meshes.append(dict(path=path, collision=coll,
            collision_enabled=UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get() if coll else None,
            approximation=UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() if coll else None,
            bounds_m=[list(box.GetMin()),list(box.GetMax())],
            point_count=len(UsdGeom.Mesh(prim).GetPointsAttr().Get())))
    comparisons = []
    for item in source['gripper']['links']:
        link = item['link']
        parts = [m for m in meshes if '/'+link+'/' in m['path']]
        vis = [m for m in parts if '/visuals/' in m['path']]
        cols = [m for m in parts if m['collision']]
        if len(vis) != 1 or len(cols) != 1:
            raise RuntimeError('expected matching native visual/collider for '+link+': '+str(parts))
        difference = float(np.max(np.abs(np.array(vis[0]['bounds_m'])-np.array(cols[0]['bounds_m']))))
        if difference > 1e-6 or not cols[0]['collision_enabled'] or cols[0]['approximation'] != 'convexDecomposition':
            raise RuntimeError('native imported collision mismatch: '+link)
        comparisons.append(dict(link=link, authored_mesh_bounds_max_error_m=difference,
            visual_points=vis[0]['point_count'], collision_points=cols[0]['point_count']))
    if any('contact_pad' in str(p.GetPath()) for p in stage.Traverse()):
        raise RuntimeError('unexpected legacy pad')
    stage.GetRootLayer().Save()
    report = dict(schema='rm65_native_import_audit_v1', status='pass', simulation_only=True,
        usd=str(usd), imported_path=str(imported), merge_fixed_joints=False,
        self_collision_requested=True, parse_mimic=True, source_urdf_sha256=source['urdf_sha256'],
        force_driven_master=drives, passive_mimic_followers=found_followers,
        geometry_comparisons=comparisons, meshes=meshes, physics_steps=0,
        collider_schema_relocations=collider_repairs, contact_offset_m=.001, rest_offset_m=0.,
        composed_layer_sha256={layer.realPath:sha256(layer.realPath) for layer in stage.GetUsedLayers() if layer.realPath},
        native_dynamic_validation=False, training_ready=False, pi05_used=False,
        limitations=['Authored mesh bounds checked; cooked PhysX convex hulls not extracted.',
                     'No dynamic closure, contact, or hardware validation yet.'])
    with report_path.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2), flush=True)


try:
    main()
except BaseException:
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)
else:
    launcher.app.close(skip_cleanup=True)
