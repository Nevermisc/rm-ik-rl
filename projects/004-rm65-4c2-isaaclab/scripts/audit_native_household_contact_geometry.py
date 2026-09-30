"""Finite saved-frame/point audit of a native textured marker; CPU only."""
import argparse
import copy
import json
from pathlib import Path
import numpy as np

from audit_native_external_contact_geometry import quaternion_matrix,sha256
from native_contact_geometry import load_inner_triangles,point_to_triangles_distance
from native_household_geometry import read_rigid_mesh
from native_curved_geometry import closest_source_surface,solid_winding_number,hull_from_vertices,closest_normal_ray_interval


def stats(values):
    a=np.asarray(values,float)
    return dict(count=len(a),min=float(a.min()),median=float(np.median(a)),p95=float(np.quantile(a,.95)),max=float(a.max())) if len(a) else dict(count=0)


def sample_faces(triangles,count=256,seed=713):
    cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);area=np.linalg.norm(cross,axis=1)/2
    rng=np.random.default_rng(seed);indices=rng.choice(len(triangles),size=count,p=area/area.sum())
    t=triangles[indices];u=np.sqrt(rng.random(count));v=rng.random(count)
    points=(1-u[:,None])*t[:,0]+(u*(1-v))[:,None]*t[:,1]+(u*v)[:,None]*t[:,2]
    return points,cross[indices]/(2*area[indices,None]),indices


def selected_frames(telemetry):
    chosen={};extreme=None;first_failure=None
    for line_number,line in enumerate(telemetry.open(),1):
        row=json.loads(line)
        if row['phase'] in ('hold_unsupported','hold_lift','hold_transport'):
            chosen[row['phase']+'_last']=(line_number,row)
        if first_failure is None and row['phase'] in ('active_lift','active_transport') and not row['bilateral_native_face_contact']:
            first_failure=(line_number,row)
        for pair in row['raw_contacts']:
            if pair['body'] not in ('tool_l_3','tool_r_3'):continue
            for c in pair['contacts']:
                if abs(c['force_N'])>.001 and (extreme is None or c['separation_m']<extreme[0]):
                    extreme=(c['separation_m'],line_number,row)
    if extreme is not None:chosen['most_negative_force_bearing_separation']=(extreme[1],extreme[2])
    if first_failure is not None:chosen['first_active_native_flag_false']=first_failure
    return chosen


def audit(run_dir,candidate,asset_usd,preflight_result,output_dir,summary):
    if output_dir.exists() or summary.exists():raise ValueError('fresh outputs required')
    telemetry=run_dir/'telemetry.jsonl';run_report=run_dir/'report.json';manifest_path=run_dir/'manifest.json';cooked_path=run_dir/'object_cooked_raw.json'
    report=json.loads(run_report.read_text());manifest=json.loads(manifest_path.read_text());runtime=json.loads((run_dir/'runtime_preflight.json').read_text())
    preflight=json.loads(preflight_result.read_text());raw_source_path=Path(preflight['raw_geometry_path'])
    inputs=[telemetry,run_report,manifest_path,cooked_path,asset_usd,candidate/'native.urdf',preflight_result,raw_source_path,run_dir/'runtime_preflight.json']
    identities={str(p):sha256(p) for p in inputs}
    if report['physics_steps']!=3360 or report['stop_reason'] is not None:raise ValueError('complete stable finite run required')
    if identities[str(asset_usd)]!=manifest['household_object']['local_asset_sha256']:raise ValueError('source package hash mismatch')
    if identities[str(raw_source_path)]!=preflight['raw_geometry_sha256']:raise ValueError('preflight source points changed')
    if identities[str(cooked_path)]!=runtime[0]['object_cooked_geometry']['raw_sha256']:raise ValueError('runtime cooked payload identity mismatch')
    if identities[str(candidate/'native.urdf')]!=manifest['protocol']['source_urdf_sha256']:raise ValueError('source robot identity mismatch')
    source=read_rigid_mesh(asset_usd);raw=json.loads(cooked_path.read_text());old_source=json.loads(raw_source_path.read_text())
    vertices=source['vertices'];indices=source['indices'];triangles=vertices[indices]
    M=np.asarray(raw['mesh_to_body_row_matrix']);scene_points=np.asarray(raw['source_usd_points'])@M[:3,:3]+M[3,:3]
    topology_equal=np.array_equal(np.asarray(raw['source_face_vertex_indices']).reshape(-1,3),indices) and all(c==3 for c in raw['source_face_vertex_counts'])
    point_error=float(np.max(np.abs(vertices-scene_points)))
    if point_error>1e-8 or not topology_equal or not np.array_equal(vertices,np.asarray(old_source['vertices_rigid_m'])) or not np.array_equal(indices,np.asarray(old_source['triangle_indices'])):
        raise ValueError('source/package/scene/CPU preflight geometry mismatch')
    unique,reverse=np.unique(vertices,axis=0,return_inverse=True);ii=reverse[indices]
    directed=np.concatenate([ii[:,[0,1]],ii[:,[1,2]],ii[:,[2,0]]]);edges=np.sort(directed,axis=1)
    _,inverse,counts=np.unique(edges,axis=0,return_counts=True,return_inverse=True)
    balances=np.bincount(inverse,weights=np.where(directed[:,0]<directed[:,1],1.,-1.))
    topology=dict(exact_position_weld_vertices=len(unique),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),inconsistent_oriented_edges=int((balances!=0).sum()))
    if topology['boundary_edges'] or topology['nonmanifold_edges'] or topology['inconsistent_oriented_edges']:raise ValueError('closed oriented source surface required for winding witnesses')
    hulls=[];canonical=[];raw_plane_violations=[]
    for i,h in enumerate(raw['hulls']):
        hv=np.asarray(h['vertices'])@M[:3,:3]+M[3,:3];hull=hull_from_vertices(hv);hulls.append(hull)
        canonical.append(dict(index=i,vertices_rigid_m=hv.tolist(),support_planes_rigid=hull['planes'].tolist(),
            max_vertex_outside_reconstructed_support_plane_m=float((hv@hull['planes'][:,:3].T+hull['planes'][:,3]).max())))
        rp=np.asarray([p['plane'] for p in h['polygons']]);normals=np.linalg.solve(M[:3,:3],rp[:,:3].T).T
        planes=np.c_[normals,rp[:,3]-normals@M[3,:3]];planes/=np.linalg.norm(planes[:,:3],axis=1)[:,None]
        raw_plane_violations.append(float((hv@planes[:,:3].T+planes[:,3]).max()))
    points,normals,triangle_ids=sample_faces(triangles)
    ray_rows=[]
    for p,n,tid in zip(points,normals,triangle_ids):
        ray=closest_normal_ray_interval(p,n,hulls)
        ray_rows.append(dict(source_point_rigid_m=p.tolist(),source_normal_rigid=n.tolist(),source_triangle_index=int(tid),**ray))
    hv=np.unique(np.concatenate([h['vertices'] for h in hulls]),axis=0)
    hv_sample=hv[np.linspace(0,len(hv)-1,min(256,len(hv)),dtype=int)]
    vertex_rows=[]
    for p in hv_sample:
        nearest=closest_source_surface(p,triangles);w=solid_winding_number(p,triangles)
        vertex_rows.append(dict(cooked_vertex_rigid_m=p.tolist(),source_distance_m=nearest['distance_m'],source_winding_number=w,
            signed_distance_positive_outside_m=(-1 if abs(w)>.5 else 1)*nearest['distance_m']))
    output_dir.mkdir(parents=True)
    surface_raw=output_dir/'canonical_hulls_and_surface_samples.json'
    surface_raw.write_text(json.dumps(dict(canonical_hulls=canonical,source_surface_normal_rays=ray_rows,cooked_vertex_samples=vertex_rows),indent=2,allow_nan=False))
    faces=load_inner_triangles(candidate/'native.urdf');frames=[]
    for reason,(line_number,row) in selected_frames(telemetry).items():
        objR=quaternion_matrix(row['object_quat_wxyz']);objp=np.asarray(row['object_pos_m'])
        entry=dict(selection=reason,step=row['step'],phase=row['phase'],telemetry_line_number=line_number,
            object_pose=dict(position_m=row['object_pos_m'],quat_wxyz=row['object_quat_wxyz']),native_bilateral_flag=row['bilateral_native_face_contact'],bodies={})
        for name,face in faces.items():
            pose=row['fingertip_pose_world'][name];R=quaternion_matrix(pose['quat_wxyz']);p=np.asarray(pose['position_m'])
            contacts=[c for pair in row['raw_contacts'] if pair['body']==name for c in pair['contacts'] if abs(c['force_N'])>.001]
            selected_indices=sorted(set(([int(np.argmin([c['separation_m'] for c in contacts])),int(np.argmax([abs(c['force_N']) for c in contacts]))]+np.linspace(0,len(contacts)-1,min(16,len(contacts)),dtype=int).tolist()) if contacts else []))
            contact_rows=[]
            for index in selected_indices:
                c=contacts[index];world=np.array(c['point_world_m']);local=(world-objp)@objR;normal=np.array(c['normal_world'])@objR
                nearest=closest_source_surface(local,triangles);n=np.array(nearest['normal'])
                finger_local=(world-p)@R
                contact_rows.append(dict(contact=c,object_local_point_m=local.tolist(),source_object_surface_distance_m=nearest['distance_m'],
                    closest_object_triangle_index=nearest['triangle_index'],source_object_normal_abs_alignment=float(abs(n@normal)/np.linalg.norm(normal)),
                    source_finger_surface_distance_recomputed_m=point_to_triangles_distance(finger_local,face),
                    source_object_winding_at_contact=solid_winding_number(local,triangles)))
            fp=np.unique(np.concatenate([face.reshape(-1,3),face.mean(1),((face+np.roll(face,-1,axis=1))/2).reshape(-1,3)]),axis=0)
            witnesses=[]
            for point in fp:
                ol=(point@R.T+p-objp)@objR;w=solid_winding_number(ol,triangles)
                if abs(w)>.5:
                    nearest=closest_source_surface(ol,triangles)
                    if nearest['distance_m']>.0001:witnesses.append(dict(finger_point_local_m=point.tolist(),object_point_local_m=ol.tolist(),source_winding=w,distance_to_object_surface_m=nearest['distance_m']))
            entry['bodies'][name]=dict(active_contact_count=len(contacts),sampled_contact_count=len(contact_rows),
                active_raw_separation_m=stats([c['separation_m'] for c in contacts]),
                sampled_source_object_surface_distance_m=stats([c['source_object_surface_distance_m'] for c in contact_rows]),
                sampled_source_object_normal_abs_alignment=stats([c['source_object_normal_abs_alignment'] for c in contact_rows]),
                sampled_source_finger_distance_m=stats([c['source_finger_surface_distance_recomputed_m'] for c in contact_rows]),
                sampled_original_finger_face_point_count=len(fp),strict_source_finger_face_inside_object_witness_count=len(witnesses),
                largest_inside_witness_distance_to_source_object_surface_m=max((w['distance_to_object_surface_m'] for w in witnesses),default=0.),
                contact_point_samples=contact_rows,source_face_inside_witnesses=witnesses)
        frame_raw=output_dir/f"step_{row['step']:04d}_{reason}.json"
        frame_raw.write_text(json.dumps(dict(geometry=entry,original_telemetry_record=row),indent=2,allow_nan=False))
        compact=copy.deepcopy(entry)
        for b in compact['bodies'].values():b.pop('contact_point_samples');b.pop('source_face_inside_witnesses')
        compact.update(raw_path=str(frame_raw),raw_sha256=sha256(frame_raw));frames.append(compact)
    if any(sha256(p)!=digest for p,digest in identities.items()):raise ValueError('input changed during CPU audit')
    ray_offsets=[r['outward_boundary_offset_m'] for r in ray_rows if r['hit']]
    result=dict(schema='rm65_native_curved_object_geometry_v1',simulation_only=True,physics_steps=0,pi05_used=False,training_ready=False,
        asset_object_id='ycb_large_marker',input_sha256=identities,source_topology=topology,
        source_scene_correspondence=dict(scene_mesh_path=raw['mesh_path'],max_rigid_vertex_coordinate_error_m=point_error,
            triangle_topology_equal=topology_equal,source_preflight_vertices_and_triangles_equal=True,mesh_to_rigid_row_matrix=M.tolist(),
            cooked_coordinates='Raw cooked vertices are mesh-local; original approximately0.01 mesh-to-rigid transform applied exactly once.'),
        cooked_vertex_reconstruction=dict(hull_count=len(hulls),raw_polygon_plane_max_vertex_outside_m=max(raw_plane_violations),
            canonical_support_plane_max_vertex_outside_m=max(h['max_vertex_outside_reconstructed_support_plane_m'] for h in canonical),
            source_surface_sample_count=len(ray_rows),source_sample_selection='Area-proportional seeded triangle/barycentric sampling, NumPy PCG64 seed713',
            no_normal_ray_hit_count=sum(not r['hit'] for r in ray_rows),source_points_inside_hull_union_count=sum(r['source_point_in_hull_union'] for r in ray_rows),
            normal_ray_outward_boundary_offset_m=stats(ray_offsets),sampled_cooked_vertex_signed_distance_to_source_m=stats([r['signed_distance_positive_outside_m'] for r in vertex_rows]),
            raw_surface_audit_path=str(surface_raw),raw_surface_audit_sha256=sha256(surface_raw)),frames=frames,
        analysis_code_sha256={Path(__file__).name:sha256(__file__),'native_curved_geometry.py':sha256(Path(__file__).with_name('native_curved_geometry.py'))},
        limitations=['Only fixed finite source samples and selected saved frames are audited; no full-time or global collision-accuracy certification.',
            'Halfspaces are reconstructed from actual saved cooked vertices, never trusted from exported polygon-plane fields alone.',
            'Normal-ray offsets are directional measurements of the nearest occupied line component, not Euclidean mesh Hausdorff distance.',
            'Sampled cooked vertex distances may miss larger face-interior bridging errors. Source normals near triangulated seams/features can change abruptly.',
            'Contact points/separations describe contact generation within a physics step; source distances use recorded post-step object/finger poses.',
            'Inside witnesses use a closed oriented curved source mesh winding number and exact finite-triangle distances, not a cuboid/AABB surrogate.',
            'No sampled inside witness is not proof of zero surface intersection elsewhere; no complete triangle/triangle intersection sweep is claimed.',
            'No physical settings, assets, thresholds, prior reports, or simulator state were changed. Diagnostic data are excluded from training.'])
    summary.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['run-dir','candidate','asset-usd','preflight-result','output-dir','summary']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=audit(a.run_dir,a.candidate,a.asset_usd,a.preflight_result,a.output_dir,a.summary)
    print(json.dumps(dict(report=str(a.summary),sha256=sha256(a.summary),cooked=r['cooked_vertex_reconstruction'],frames=r['frames']),indent=2))
