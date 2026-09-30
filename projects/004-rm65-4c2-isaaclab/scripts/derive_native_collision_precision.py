"""Fresh uniform gripper collision-precision diagnostic, without geometry edits."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
from build_native_gripper_candidate import sha256

# Shared across all nine gripper meshes, not tuned by object/side/task success.
PARAMETERS = dict(hullVertexLimit=64,maxConvexHulls=128,minThickness=.0001,
                  voxelResolution=1000000,errorPercentage=1.,shrinkWrap=True)
PREFIX='physxConvexDecompositionCollision:'


def stage_contract(stage, exclude_precision=True):
    """All existing composed values/relationships, excluding only precision attrs."""
    result={}
    for prim in stage.Traverse():
        result[str(prim.GetPath())]=dict(type=prim.GetTypeName(),
            attributes={a.GetName():str(a.Get()) for a in prim.GetAttributes() if not exclude_precision or not a.GetName().startswith(PREFIX)},
            relationships={r.GetName():[str(p) for p in r.GetTargets()] for r in prim.GetRelationships()},
            schemas=[s for s in prim.GetAppliedSchemas() if not exclude_precision or s!='PhysxConvexDecompositionCollisionAPI'])
    return result


def main():
    from isaaclab.app import AppLauncher
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    AppLauncher.add_app_launcher_args(parser)
    args=parser.parse_args(); src=args.source.resolve(); dst=args.destination.resolve()
    if dst.exists(): parser.error('fresh destination required')
    audit=json.loads((src/'import_audit.json').read_text())
    source_audit=json.loads((src/'source_audit.json').read_text())
    if audit['status']!='pass': parser.error('source audit failed')
    for name,expected in {**audit['composed_layer_sha256'],**source_audit['mesh_sha256']}.items():
        if sha256(name)!=expected: parser.error('source file changed')
    launcher=AppLauncher(args)
    try:
        from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema
        dst.mkdir(parents=True,exist_ok=False)
        for name in ('native.usd','native.urdf'): shutil.copy2(src/name,dst/name)
        shutil.copytree(src/'configuration',dst/'configuration')
        source_audit['urdf']=str(dst/'native.urdf')
        with (dst/'source_audit.json').open('x') as stream: json.dump(source_audit,stream,indent=2)
        stage=Usd.Stage.Open(str(dst/'native.usd')); before=stage_contract(stage); modified=[]
        for prim in stage.Traverse():
            if not prim.IsA(UsdGeom.Mesh) or not prim.HasAPI(UsdPhysics.CollisionAPI): continue
            ancestor=prim
            while ancestor and not ancestor.HasAPI(UsdPhysics.RigidBodyAPI): ancestor=ancestor.GetParent()
            if not ancestor or not ancestor.GetName().startswith('tool_'): continue
            if UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()!='convexDecomposition':
                raise ValueError('expected existing convex decomposition')
            api=PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(prim)
            for key,value in PARAMETERS.items():
                getattr(api,'Create'+key[0].upper()+key[1:]+'Attr')().Set(value)
            modified.append(str(prim.GetPath()))
        if len(modified)!=9 or before!=stage_contract(stage):
            raise ValueError('uniform precision-only contract failed')
        stage.GetRootLayer().Save()
        if before!=stage_contract(Usd.Stage.Open(str(dst/'native.usd'))):
            raise ValueError('saved stage changed unrelated values')
        inherited=audit.get('derivation',{})
        audit['usd']=str(dst/'native.usd')
        audit['composed_layer_sha256']={l.realPath:sha256(l.realPath) for l in stage.GetUsedLayers() if l.realPath}
        audit['derivation']=dict(source=str(src),source_import_audit_sha256=sha256(src/'import_audit.json'),
            change='uniform_nine_gripper_mesh_collision_precision_only',precision_parameters=PARAMETERS,
            modified_meshes=modified,self_collision_filters_added=inherited.get('self_collision_filters_added',[]),
            inherited_derivation=inherited,unrelated_stage_contract_equal=True,source_urdf_unchanged=sha256(src/'native.urdf')==sha256(dst/'native.urdf'),
            physics_steps=0,hardware_transmission_validated=False,source_follower_limit_equality=False,
            rationale='Source triangles do not cross at sampled angles; previous convex hulls overlap increasingly. '
                      'Uniform sub-mm cooking precision tests approximation fidelity, not task-specific geometry changes.')
        with (dst/'import_audit.json').open('x') as stream: json.dump(audit,stream,indent=2)
        print(json.dumps(audit['derivation'],indent=2),flush=True)
    except BaseException:
        traceback.print_exc(); sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
    else: launcher.app.close(skip_cleanup=True)


if __name__=='__main__': main()
