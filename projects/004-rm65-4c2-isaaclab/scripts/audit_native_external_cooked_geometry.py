"""CPU-only saved convex-hull/OBB audit; no cooking, simulation, or asset writes."""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

from audit_native_collision_fidelity import convex_sat
from audit_native_external_contact_geometry import sha256
from native_contact_geometry import load_inner_triangles


def box_hull(half):
    half = np.asarray(half, float)
    vertices = np.array(list(itertools.product((-1., 1.), repeat=3))) * half
    indices, polygons = [], []
    for axis in range(3):
        other = [j for j in range(3) if j != axis]
        for sign in (-1., 1.):
            ids = np.flatnonzero(vertices[:, axis] == sign*half[axis])
            angle = np.arctan2(vertices[ids, other[1]], vertices[ids, other[0]])
            ids = ids[np.argsort(angle)]
            normal = np.eye(3)[axis]*sign
            polygons.append(dict(plane=[*normal, -half[axis]], index_base=len(indices), num_vertices=4))
            indices.extend(ids.tolist())
    return dict(vertices=vertices.tolist(), indices=indices, polygons=polygons)


def normalized_planes(hull):
    planes = np.array([p['plane'] for p in hull['polygons']], float)
    lengths = np.linalg.norm(planes[:, :3], axis=1)
    if not np.isfinite(planes).all() or np.any(lengths < 1e-12):
        raise ValueError('finite nondegenerate hull planes required')
    return planes/lengths[:, None]


def common_interior_witness(hull, mesh_to_object, half):
    """Largest inscribed-ball LP provides an explicit common-interior witness.

    Radius is a witness of solid overlap, not minimum translation depth. The LP
    works in mm to keep feasibility tolerances well below the 10 um threshold.
    """
    planes = normalized_planes(hull)
    rotation, translation = mesh_to_object[:3, :3], mesh_to_object[:3, 3]
    normals = planes[:, :3] @ rotation.T
    offsets = planes[:, 3] - normals @ translation
    boxes = normalized_planes(box_hull(half))
    normals = np.concatenate([normals, boxes[:, :3]])
    offsets = np.r_[offsets, boxes[:, 3]]
    result = linprog([0., 0., 0., -1.], A_ub=np.column_stack([normals, np.ones(len(normals))]),
        b_ub=-offsets*1000., bounds=[(None, None)]*3+[(0., None)], method='highs')
    if not result.success:
        return dict(feasible=False, solver_status=int(result.status), solver_message=result.message)
    center, radius = result.x[:3]/1000., float(result.x[3]/1000.)
    margin = float(np.min(-offsets-normals@center))
    return dict(feasible=True, center_object_m=center.tolist(), radius_m=radius,
        minimum_verified_halfspace_margin_m=margin, strict_common_interior=margin > 1e-5)


def sample_triangles(triangles, spacing=.0005):
    points, weights = [], []
    for triangle in triangles:
        edges = np.roll(triangle, -1, axis=0)-triangle
        divisions = max(2, int(np.ceil(np.linalg.norm(edges, axis=1).max()/spacing)))
        # Interior lattice avoids edge duplication; triangle area weights keep
        # narrow, heavily subdivided source triangles from dominating coverage.
        uv = np.array([[(i+1/3)/divisions, (j+1/3)/divisions]
                       for i in range(divisions) for j in range(divisions-i)])
        keep = uv.sum(axis=1) < 1.
        uv = uv[keep]
        samples = triangle[0]+uv[:, :1]*(triangle[1]-triangle[0])+uv[:, 1:]*(triangle[2]-triangle[0])
        area = np.linalg.norm(np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0]))/2
        points.extend(samples)
        weights.extend([area/len(samples)]*len(samples))
    return np.asarray(points), np.asarray(weights)


def normal_ray_envelope(points_mesh, outward_mesh, hulls):
    """Outwardmost cooked boundary along each source face-normal ray.

    A negative value is recession below the source plane, positive is extension
    beyond it. NaN means no hull intersects that normal line; it is not a metric
    point-to-union distance or proof that neighboring unsampled points agree.
    """
    positions = np.asarray(points_mesh, float)
    upper_envelope = np.full(len(positions), np.nan)
    for hull in hulls:
        planes = normalized_planes(hull)
        denominator = planes[:, :3]@outward_mesh
        rhs = -(positions@planes[:, :3].T+planes[:, 3])
        positive, negative, parallel = denominator > 1e-10, denominator < -1e-10, np.abs(denominator) <= 1e-10
        upper = np.min(rhs[:, positive]/denominator[positive], axis=1) if positive.any() else np.full(len(positions), np.inf)
        lower = np.max(rhs[:, negative]/denominator[negative], axis=1) if negative.any() else np.full(len(positions), -np.inf)
        valid = np.all(rhs[:, parallel] >= -1e-8, axis=1) & (lower <= upper+1e-8) & np.isfinite(upper)
        upper_envelope[valid] = np.fmax(upper_envelope[valid], upper[valid])
    return upper_envelope


def coverage_summary(envelope, weights):
    weights = np.asarray(weights, float)
    finite = np.isfinite(envelope)
    total = weights.sum()
    fraction = lambda mask: float(weights[mask].sum()/total) if total else 0.
    return dict(sample_count=len(envelope), sample_area_weight_sum_m2=float(total),
        no_normal_ray_hull_fraction=fraction(~finite),
        within_0_1mm_of_source_fraction=fraction(finite & (np.abs(envelope) <= .0001)),
        recessed_over_0_1mm_fraction=fraction(finite & (envelope < -.0001)),
        recessed_over_1mm_fraction=fraction(finite & (envelope < -.001)),
        outward_over_0_1mm_fraction=fraction(finite & (envelope > .0001)),
        minimum_outward_boundary_offset_m=float(envelope[finite].min()) if finite.any() else None,
        maximum_outward_boundary_offset_m=float(envelope[finite].max()) if finite.any() else None,
        sampled_coverage_only=True)


def verify_cooking_contract(cooking, final_candidate):
    """Use standalone pxr CPU reads to bind old cooked shapes to final geometry."""
    from pxr import Usd, UsdGeom
    original = Path(cooking['candidate'])
    old_audit = json.loads((original/'import_audit.json').read_text())
    new_audit = json.loads((final_candidate/'import_audit.json').read_text())
    if sha256(original/'import_audit.json') != cooking['import_audit_sha256']:
        raise ValueError('cooked import audit identity mismatch')
    for audit in (old_audit, new_audit):
        for path, expected in audit['composed_layer_sha256'].items():
            if sha256(path) != expected:
                raise ValueError('candidate USD layer identity changed')
    sources = [json.loads((p/'source_audit.json').read_text()) for p in (original, final_candidate)]
    if sources[0]['mesh_sha256'] != sources[1]['mesh_sha256']:
        raise ValueError('source mesh identity differs between cooked and final candidate')
    for path, expected in sources[1]['mesh_sha256'].items():
        if sha256(path) != expected:
            raise ValueError('source mesh identity changed')
    stages = [Usd.Stage.Open(str(p/'native.usd')) for p in (original, final_candidate)]
    records, raw = [], {}
    for row in cooking['colliders']:
        if row['link'] not in ('tool_l_3', 'tool_r_3'):
            continue
        if sha256(row['raw_path']) != row['raw_sha256']:
            raise ValueError('cooked raw identity mismatch')
        data = json.loads(Path(row['raw_path']).read_text())
        prims = [stage.GetPrimAtPath(row['mesh_path']) for stage in stages]
        meshes = [UsdGeom.Mesh(prim) for prim in prims]
        checks = {}
        for name in ('points', 'faceVertexCounts', 'faceVertexIndices'):
            values = [np.asarray(prim.GetAttribute(name).Get()) for prim in prims]
            checks[name+'_equal'] = np.array_equal(*values)
        checks['raw_source_points_equal'] = np.array_equal(np.asarray(data['source_usd_points']), np.asarray(meshes[1].GetPointsAttr().Get()))
        parameters = {key:prims[1].GetAttribute(key).Get() for key in row['authored_parameters']}
        checks['cooking_parameters_equal'] = all(prims[0].GetAttribute(k).Get() == parameters[k] == v for k,v in row['authored_parameters'].items())
        transforms = []
        for stage, prim in zip(stages, prims):
            cache = UsdGeom.XformCache()
            body = stage.GetPrimAtPath('/rm65_4c2_native/'+row['link'])
            transforms.append(np.asarray(cache.GetLocalToWorldTransform(prim)*cache.GetLocalToWorldTransform(body).GetInverse()))
        checks['mesh_to_body_equal'] = np.allclose(transforms[0], transforms[1], atol=1e-12, rtol=0) and np.allclose(transforms[1], data['mesh_to_body_row_matrix'], atol=1e-12, rtol=0)
        checks['approximation_equal'] = all(str(prim.GetAttribute('physics:approximation').Get()) == row['approximation'] for prim in prims)
        checks['hull_export_valid'] = bool(data['valid']) and len(data['hulls']) == row['hull_count']
        if not all(checks.values()):
            raise ValueError('cooked/final mesh contract failed: '+str(checks))
        raw[row['link']] = data
        records.append(dict(link=row['link'], checks=checks, hull_count=len(data['hulls']), cooking_parameters=parameters,
            raw_path=row['raw_path'], raw_sha256=row['raw_sha256']))
    return dict(status='pass', original_candidate=str(original), final_candidate=str(final_candidate),
        original_import_audit_sha256=sha256(original/'import_audit.json'), final_import_audit_sha256=sha256(final_candidate/'import_audit.json'),
        original_usd_sha256=sha256(original/'native.usd'), final_usd_sha256=sha256(final_candidate/'native.usd'),
        source_mesh_sha256=sources[1]['mesh_sha256'], colliders=records,
        runtime_004_hulls_reexported=False), raw


def audit(cooking_path, geometry_path, candidate, output_dir, summary_path):
    if output_dir.exists() or summary_path.exists():
        raise ValueError('fresh output and summary paths required')
    cooking = json.loads(cooking_path.read_text())
    geometry = json.loads(geometry_path.read_text())
    if cooking['status'] != 'pass' or sha256(candidate/'native.urdf') != geometry['source_urdf_sha256']:
        raise ValueError('input evidence gate failed')
    contract, raw = verify_cooking_contract(cooking, candidate)
    faces = load_inner_triangles(candidate/'native.urdf')
    output_dir.mkdir(parents=True)
    body_samples, coverages = {}, {}
    for name, triangles in faces.items():
        mesh_to_body = np.asarray(raw[name]['mesh_to_body_row_matrix']).T
        body_to_mesh = np.linalg.inv(mesh_to_body)
        points, weights = sample_triangles(triangles)
        mesh_points = points@body_to_mesh[:3,:3].T+body_to_mesh[:3,3]
        outward = np.cross(triangles[0,1]-triangles[0,0], triangles[0,2]-triangles[0,0]); outward /= np.linalg.norm(outward)
        full_centroid = np.asarray(raw[name]['source_usd_points']).mean(0)@mesh_to_body[:3,:3].T+mesh_to_body[:3,3]
        if outward@(triangles.reshape(-1,3).mean(0)-full_centroid) < 0:
            outward *= -1
        envelope = normal_ray_envelope(mesh_points, body_to_mesh[:3,:3]@outward, raw[name]['hulls'])
        body_samples[name] = (points, weights, envelope)
        coverages[name] = dict(source_outward_normal_body=outward.tolist(), sampling_edge_spacing_m=.0005,
            source_inner_face=coverage_summary(envelope, weights))
    cases=[]
    for case in geometry['cases']:
        raw_path=Path(case['raw_evidence_path'])
        if sha256(raw_path) != case['raw_evidence_sha256']:
            raise ValueError('saved actual pose evidence changed')
        object_rotation = np.asarray(case['object_rotation_local_to_world'])
        object_position = np.asarray(case['object_position_world_m'])
        half = np.asarray(case['object_half_extents_m'])
        box=box_hull(half)
        record=dict(width_m=case['width_m'], step=case['step'], phase=case['phase'], bodies={})
        for name, evidence in case['bodies'].items():
            fit=evidence['pose_reconstruction']
            if not fit['valid']:
                raise ValueError('actual body pose was not proven')
            body_to_object=np.eye(4)
            body_to_object[:3,:3]=object_rotation.T@np.asarray(fit['rotation_local_to_world'])
            body_to_object[:3,3]=object_rotation.T@(np.asarray(fit['position_world_m'])-object_position)
            mesh_to_object=body_to_object@np.asarray(raw[name]['mesh_to_body_row_matrix']).T
            rows=[]
            for index,hull in enumerate(raw[name]['hulls']):
                gap=convex_sat(hull,box,mesh_to_object,np.eye(4))
                item=dict(hull_index=index,signed_sat_axis_gap_m=gap,strict_sat_overlap=gap < -1e-5)
                if gap < -1e-5:
                    item['common_interior_witness']=common_interior_witness(hull,mesh_to_object,half)
                rows.append(item)
            points,weights,envelope=body_samples[name]
            object_points=points@body_to_object[:3,:3].T+body_to_object[:3,3]
            inside=np.all(np.abs(object_points)<half-.0001,axis=1)
            witnesses=[v['common_interior_witness'] for v in rows if v.get('common_interior_witness',{}).get('strict_common_interior')]
            record['bodies'][name]=dict(hull_count=len(rows),strict_sat_overlap_hull_count=sum(v['strict_sat_overlap'] for v in rows),
                smallest_signed_sat_axis_gap_m=min(v['signed_sat_axis_gap_m'] for v in rows),
                explicit_common_interior_witness_count=len(witnesses),
                largest_common_interior_ball_radius_m=max((v['radius_m'] for v in witnesses),default=0.),
                source_face_samples_strictly_inside_object=coverage_summary(envelope[inside],weights[inside]),
                source_surface_penetration_confirmed=evidence['source_face_vs_actual_object']['strict_source_face_inside_object'],
                saved_cooked_hull_penetration_confirmed=bool(witnesses),hull_details=rows)
        raw_case_path=output_dir/f"width_{round(case['width_m']*1000):03d}_cooked_comparison.json"
        raw_case_path.write_text(json.dumps(record,indent=2,allow_nan=False))
        for body in record['bodies'].values(): body.pop('hull_details')
        record.update(raw_path=str(raw_case_path),raw_sha256=sha256(raw_case_path))
        cases.append(record)
    report=dict(schema='rm65_native_external_cooked_geometry_v1',simulation_only=True,read_only_physics=True,physics_steps=0,
        pi05_used=False,training_ready=False,analysis_script_sha256=sha256(__file__),
        cooking_report_sha256=sha256(cooking_path),actual_pose_geometry_report_sha256=sha256(geometry_path),
        telemetry_sha256=geometry['telemetry_sha256'],source_urdf_sha256=geometry['source_urdf_sha256'],
        cooked_to_final_asset_contract=contract,source_face_coverage=coverages,cases=cases,
        conclusion='saved_cooked_solids_also_intersect_objects' if all(all(b['saved_cooked_hull_penetration_confirmed'] for b in c['bodies'].values()) for c in cases) else 'per_case_evidence_required',
        limitations=[
            'The 003 hull export is bound to final mesh points, topology, mesh-to-body transform and cooking settings; 004 runtime hull bytes were not re-exported, so cook nondeterminism/cache differences are not excluded.',
            'Actual body pose reconstruction and object OBB are post-step; contact generation/separation may refer to an earlier solver instant within the step.',
            'SAT axis gaps and common-interior ball radii are overlap witnesses, not exact whole-gripper penetration depth.',
            'Source-face coverage uses deterministic area-weighted samples and normal rays; it does not prove all unsampled surfaces or 3-D Hausdorff distance.',
            'A simultaneous cooked-solid overlap disproves missing cooked coverage as a complete explanation at these frames, conditional on the saved-cook equivalence; it does not isolate solver, drive, mimic, or contact-material causes.',
            'No new dynamics, geometry, collision filters, force parameters, or object sizes were changed.',
        ])
    summary_path.write_text(json.dumps(report,indent=2,allow_nan=False))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cooking-report',type=Path,required=True)
    parser.add_argument('--geometry-report',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--summary',type=Path,required=True)
    args=parser.parse_args()
    report=audit(args.cooking_report,args.geometry_report,args.candidate,args.output_dir,args.summary)
    print(json.dumps(dict(conclusion=report['conclusion'],source_face_coverage=report['source_face_coverage'],cases=report['cases']),indent=2))
