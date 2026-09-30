"""Export PhysX's actual convex representations without stepping or saving a stage.

Raw hull vertices belong in outputs, not Git. The compact report records counts,
parameters and hashes, not a dynamics or hardware success claim.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import traceback
import numpy as np
from build_native_gripper_candidate import sha256


def convex_record(convex):
    vertices = np.array([list(v) for v in convex.vertices], dtype=float)
    indices = [int(i) for i in convex.indices]
    polygons = [dict(plane=list(p.plane), num_vertices=int(p.num_vertices),
                     index_base=int(p.index_base)) for p in convex.polygons]
    if vertices.ndim != 2 or vertices.shape[1] != 3 or len(vertices) < 4 or not np.isfinite(vertices).all():
        raise ValueError('invalid convex vertices')
    if not indices or min(indices) < 0 or max(indices) >= len(vertices) or len(polygons) < 4:
        raise ValueError('invalid convex topology')
    for p in polygons:
        if p['num_vertices'] < 3 or p['index_base'] < 0 or p['index_base'] + p['num_vertices'] > len(indices):
            raise ValueError('invalid convex polygon slice')
        if len(p['plane']) != 4 or not np.isfinite(p['plane']).all():
            raise ValueError('invalid convex plane')
    return dict(vertices=vertices.tolist(), indices=indices, polygons=polygons,
                bounds_m=[vertices.min(0).tolist(), vertices.max(0).tolist()])


def main():
    from isaaclab.app import AppLauncher
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    if args.output_dir.exists() or args.report.exists():
        parser.error('fresh outputs required')
    audit = json.loads((args.candidate/'import_audit.json').read_text())
    if audit['status'] != 'pass':
        parser.error('static import prerequisite failed')
    for name, expected in audit['composed_layer_sha256'].items():
        if sha256(name) != expected:
            parser.error('source USD changed')
    launcher = AppLauncher(args)
    try:
        from pxr import Usd, UsdGeom, UsdPhysics, UsdUtils, PhysicsSchemaTools, PhysxSchema
        from omni.physx import get_physx_cooking_interface
        from omni.physx.bindings._physx import PhysxCollisionRepresentationResult
        stage = Usd.Stage.Open(str(args.candidate/'native.usd'))
        stage_id = UsdUtils.StageCache.Get().Insert(stage).ToLongInt()
        args.output_dir.mkdir(parents=True, exist_ok=False)
        summary = []
        for prim in stage.Traverse():
            if not prim.IsA(UsdGeom.Mesh) or not prim.HasAPI(UsdPhysics.CollisionAPI):
                continue
            ancestor = prim
            while ancestor and not ancestor.HasAPI(UsdPhysics.RigidBodyAPI):
                ancestor = ancestor.GetParent()
            if not ancestor or not ancestor.GetName().startswith('tool_'):
                continue
            returned = {}
            def callback(result, hulls):
                returned['result'] = str(result)
                returned['valid'] = result == PhysxCollisionRepresentationResult.RESULT_VALID
                returned['hulls'] = [convex_record(h) for h in hulls]
            get_physx_cooking_interface().request_convex_collision_representation(
                stage_id=stage_id, collision_prim_id=PhysicsSchemaTools.sdfPathToInt(prim.GetPath()),
                run_asynchronously=False, on_result=callback)
            if not returned.get('valid') or not returned['hulls']:
                raise ValueError('no valid representation: ' + str(prim.GetPath()) + repr(returned))
            # Mesh-to-body transform is required; do not assume mesh-local == link-local.
            cache = UsdGeom.XformCache()
            to_body = cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(ancestor).GetInverse()
            reference_stage = Usd.Stage.CreateInMemory()
            reference_prim = reference_stage.DefinePrim('/Reference', 'Mesh')
            mesh_api = PhysxSchema.PhysxConvexDecompositionCollisionAPI.Apply(reference_prim)
            params = {a.GetName():a.Get() for a in prim.GetAttributes()
                      if a.GetName().startswith('physxConvexDecompositionCollision:')}
            defaults = {n: getattr(mesh_api, method)().Get() for n,method in [
                ('minThickness','GetMinThicknessAttr'),('maxConvexHulls','GetMaxConvexHullsAttr'),
                ('hullVertexLimit','GetHullVertexLimitAttr'),('voxelResolution','GetVoxelResolutionAttr'),
                ('errorPercentage','GetErrorPercentageAttr'),('shrinkWrap','GetShrinkWrapAttr')]}
            payload = dict(link=ancestor.GetName(), mesh_path=str(prim.GetPath()),
                mesh_to_body_row_matrix=[list(r) for r in to_body], source_usd_points=[list(v) for v in UsdGeom.Mesh(prim).GetPointsAttr().Get()],
                **returned)
            path = args.output_dir/(ancestor.GetName()+'.json')
            with path.open('x') as stream:
                json.dump(payload,stream)
            summary.append(dict(link=ancestor.GetName(),mesh_path=str(prim.GetPath()),
                approximation=UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get(),
                hull_count=len(returned['hulls']),vertex_counts=[len(h['vertices']) for h in returned['hulls']],
                authored_parameters=params,parameter_api_applied=prim.HasAPI(PhysxSchema.PhysxConvexDecompositionCollisionAPI),
                schema_defaults_when_api_applied=defaults,unapplied_engine_defaults_verified=False,
                raw_path=str(path.resolve()),raw_sha256=sha256(path)))
        if len(summary) != 9:
            raise ValueError('expected all nine source gripper colliders')
        unchanged = all(sha256(n)==s for n,s in audit['composed_layer_sha256'].items())
        report = dict(schema='native_cooked_shape_audit_v1',status='pass' if unchanged else 'fail',
            import_audit_sha256=sha256(args.candidate/'import_audit.json'), candidate=str(args.candidate.resolve()),
            physics_steps=0,source_files_unchanged=unchanged,colliders=summary,training_ready=False,
            limitations=['Cooking export validates representation access, not collision fidelity or dynamics.',
                         'Raw hulls may be reordered between cooks; compare geometry, not index identity.'])
        with args.report.open('x') as stream:
            json.dump(report,stream,indent=2)
        print(json.dumps(report,indent=2),flush=True)
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(1)
    else:
        launcher.app.close(skip_cleanup=True)


if __name__ == '__main__':
    main()
