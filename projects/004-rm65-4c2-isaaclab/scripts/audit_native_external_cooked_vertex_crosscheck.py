"""Independent convex-vertex reconstruction crosscheck; CPU only, fresh outputs."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from audit_native_collision_fidelity import convex_sat
from audit_native_external_contact_geometry import sha256
from audit_native_external_cooked_geometry import (box_hull, common_interior_witness,
    coverage_summary, normal_ray_envelope, normalized_planes, sample_triangles)
from native_contact_geometry import load_inner_triangles


def canonical_vertex_hull(hull):
    vertices=np.asarray(hull['vertices'],float)
    convex=ConvexHull(vertices)
    return dict(vertices=vertices.tolist(), indices=convex.simplices.reshape(-1).tolist(),
        polygons=[dict(plane=plane.tolist(),num_vertices=3,index_base=3*i)
                  for i,plane in enumerate(convex.equations)])


def crosscheck(base_report, cooking_report, geometry_report, urdf, output_dir, summary):
    if output_dir.exists() or summary.exists(): raise ValueError('fresh paths required')
    base=json.loads(base_report.read_text()); cooking=json.loads(cooking_report.read_text()); geo=json.loads(geometry_report.read_text())
    if sha256(cooking_report)!=base['cooking_report_sha256'] or sha256(geometry_report)!=base['actual_pose_geometry_report_sha256'] or sha256(urdf)!=base['source_urdf_sha256']:
        raise ValueError('crosscheck evidence identity mismatch')
    raw={}; canonical={}; plane_checks={}; samples={}
    faces=load_inner_triangles(urdf)
    for row in cooking['colliders']:
        name=row['link']
        if name not in faces:continue
        if sha256(row['raw_path'])!=row['raw_sha256']:raise ValueError('raw hull identity mismatch')
        raw[name]=json.loads(Path(row['raw_path']).read_text())
        canonical[name]=[canonical_vertex_hull(h) for h in raw[name]['hulls']]
        violations=[]; canonical_violations=[]
        for old,new in zip(raw[name]['hulls'],canonical[name]):
            v=np.asarray(old['vertices']); p=normalized_planes(old); pc=normalized_planes(new)
            violations.append(float((v@p[:,:3].T+p[:,3]).max()))
            canonical_violations.append(float((v@pc[:,:3].T+pc[:,3]).max()))
        plane_checks[name]=dict(max_original_vertex_outside_polygon_plane_m=max(violations),
            original_hulls_exceeding_10um=sum(v>1e-5 for v in violations),
            max_reconstructed_vertex_outside_support_plane_m=max(canonical_violations))
        points,weights=sample_triangles(faces[name]); mesh_to_body=np.asarray(raw[name]['mesh_to_body_row_matrix']).T
        inverse=np.linalg.inv(mesh_to_body); meshpoints=points@inverse[:3,:3].T+inverse[:3,3]
        outward=np.array([0.,-1. if name=='tool_l_3' else 1.,0.])
        envelope=normal_ray_envelope(meshpoints,inverse[:3,:3]@outward,canonical[name])
        samples[name]=(points,weights,envelope)
        plane_checks[name]['vertex_hull_source_face_coverage']=coverage_summary(envelope,weights)
    output_dir.mkdir(parents=True)
    cases=[]
    for case in geo['cases']:
        objr=np.asarray(case['object_rotation_local_to_world']); objp=np.asarray(case['object_position_world_m']); half=np.asarray(case['object_half_extents_m'])
        record=dict(width_m=case['width_m'],step=case['step'],bodies={})
        for name,evidence in case['bodies'].items():
            fit=evidence['pose_reconstruction']; transform=np.eye(4)
            transform[:3,:3]=objr.T@np.asarray(fit['rotation_local_to_world'])
            transform[:3,3]=objr.T@(np.asarray(fit['position_world_m'])-objp)
            mesh_transform=transform@np.asarray(raw[name]['mesh_to_body_row_matrix']).T
            rows=[]
            for index,hull in enumerate(canonical[name]):
                gap=convex_sat(hull,box_hull(half),mesh_transform,np.eye(4))
                item=dict(hull_index=index,signed_sat_gap_m=gap)
                if gap < -1e-5:item['interior']=common_interior_witness(hull,mesh_transform,half)
                rows.append(item)
            witnesses=[r['interior'] for r in rows if r.get('interior',{}).get('strict_common_interior')]
            points,weights,envelope=samples[name]; objpoints=points@transform[:3,:3].T+transform[:3,3]
            inside=np.all(np.abs(objpoints)<half-.0001,axis=1)
            record['bodies'][name]=dict(strict_sat_overlap_hull_count=sum(r['signed_sat_gap_m'] < -1e-5 for r in rows),
                strict_interior_witness_count=len(witnesses),
                largest_common_interior_ball_radius_m=max((w['radius_m'] for w in witnesses),default=0.),
                inside_source_face_vertex_hull_coverage=coverage_summary(envelope[inside],weights[inside]),hull_details=rows)
        target=output_dir/f"width_{round(case['width_m']*1000):03d}_vertex_crosscheck.json"
        target.write_text(json.dumps(record,indent=2,allow_nan=False))
        for body in record['bodies'].values():body.pop('hull_details')
        record.update(raw_path=str(target),raw_sha256=sha256(target));cases.append(record)
    report=dict(schema='rm65_native_cooked_vertex_crosscheck_v1',physics_steps=0,simulation_only=True,pi05_used=False,training_ready=False,
        analysis_script_sha256=sha256(__file__),base_cooked_report_sha256=sha256(base_report),
        cooking_report_sha256=sha256(cooking_report),actual_pose_report_sha256=sha256(geometry_report),
        source_urdf_sha256=sha256(urdf),plane_consistency=plane_checks,cases=cases,
        conclusion='vertex_reconstructed_cooked_solids_still_intersect_objects' if all(all(b['strict_interior_witness_count']>0 for b in c['bodies'].values()) for c in cases) else 'overlap_not_universally_confirmed',
        limitations=['This independent representation is the convex hull of saved cooked vertices, not a newly cooked or simulated asset.',
            'Original polygon planes and vertices are not perfectly consistent; both representations are reported and neither is asserted to reproduce all runtime tolerances.',
            '003 cooked bytes were not re-exported in 004. Exact runtime cook equivalence and intra-step contact/pose timing remain limitations.',
            'Overlap remains an observation, not a solver/mimic/drive root-cause diagnosis.'])
    summary.write_text(json.dumps(report,indent=2,allow_nan=False));return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('base-report','cooking-report','geometry-report','urdf','output-dir','summary'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=crosscheck(a.base_report,a.cooking_report,a.geometry_report,a.urdf,a.output_dir,a.summary)
    print(json.dumps(dict(conclusion=r['conclusion'],plane_consistency=r['plane_consistency'],cases=r['cases']),indent=2))
