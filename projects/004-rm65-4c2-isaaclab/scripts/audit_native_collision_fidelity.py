"""Read-only source-triangle and cooked-convex comparisons at source FK poses."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET
import numpy as np
from audit_native_aperture import NativeFK
from audit_gripper_visual_collision import stl_vertices, transformed
from household_grasp_calibration import origin_transform
from build_native_gripper_candidate import sha256


def triangle_intersections(a, b, tolerance=1e-9):
    """Triangle SAT including in-plane axes for coplanar triangles.

    Counts surface intersections, not solid containment or minimum clearance.
    AABB broad phase and per-source-triangle batching bound memory usage.
    """
    a,b=np.asarray(a,float),np.asarray(b,float)
    if a.ndim!=3 or b.ndim!=3 or a.shape[1:]!=(3,3) or b.shape[1:]!=(3,3):
        raise ValueError('triangle arrays required')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('finite triangles required')
    count, examples=0,[]
    blo,bhi=b.min(1),b.max(1)
    eb=np.roll(b,-1,axis=1)-b
    nb=np.cross(eb[:,0],eb[:,1])
    for index,t in enumerate(a):
        ea=np.roll(t,-1,axis=0)-t
        na=np.cross(ea[0],ea[1])
        if np.linalg.norm(na)<1e-14:
            continue
        ids=np.flatnonzero(np.all(bhi>=t.min(0)-tolerance,axis=1)&np.all(blo<=t.max(0)+tolerance,axis=1)&(np.linalg.norm(nb,axis=1)>1e-14))
        if not len(ids): continue
        axes=np.concatenate((np.broadcast_to(na,(len(ids),1,3)),nb[ids,None,:],
            np.cross(ea[None,:,None,:],eb[ids,None,:,:]).reshape(len(ids),9,3),
            np.broadcast_to(np.cross(na,ea),(len(ids),3,3)),np.cross(nb[ids,None,:],eb[ids])),axis=1)
        norms=np.linalg.norm(axes,axis=2)
        axes=axes/np.where(norms>1e-16,norms,1)[:,:,None]
        pa=np.einsum('v d,n a d->n a v',t,axes)
        pb=np.einsum('n v d,n a d->n a v',b[ids],axes)
        gap=np.maximum(pa.min(2)-pb.max(2),pb.min(2)-pa.max(2))
        hits=ids[np.all((gap<=tolerance)|(norms<=1e-16),axis=1)]
        count+=len(hits)
        examples.extend([[index,int(i)] for i in hits[:max(0,8-len(examples))]])
    return dict(surface_intersecting_triangle_pairs=int(count),example_triangle_indices=examples,
                contains_test_performed=False,tolerance_m=tolerance)


def convex_axes(hull):
    vertices=np.asarray(hull['vertices'],float)
    faces=[]; edges=[]
    for p in hull['polygons']:
        ids=hull['indices'][p['index_base']:p['index_base']+p['num_vertices']]
        face=vertices[ids]
        faces.append(np.asarray(p['plane'][:3],float))
        edges.extend(np.roll(face,-1,axis=0)-face)
    return np.array(faces),np.array(edges)


def convex_sat(a,b,ta=None,tb=None):
    """Largest separating-axis gap. <=0 means overlapping/touching hulls."""
    ta=np.eye(4) if ta is None else ta; tb=np.eye(4) if tb is None else tb
    va,vb=transformed(np.array(a['vertices']),ta),transformed(np.array(b['vertices']),tb)
    na,ea=convex_axes(a); nb,eb=convex_axes(b)
    na=na@ta[:3,:3].T; nb=nb@tb[:3,:3].T
    ea=ea@ta[:3,:3].T; eb=eb@tb[:3,:3].T
    axes=np.concatenate((na,nb,np.cross(ea[:,None,:],eb[None,:,:]).reshape(-1,3)))
    norms=np.linalg.norm(axes,axis=1); axes=axes[norms>1e-12]/norms[norms>1e-12,None]
    axes=np.unique(np.round(axes,10),axis=0)
    if not len(axes): raise ValueError('degenerate convex pair')
    pa,pb=va@axes.T,vb@axes.T
    gaps=np.maximum(pa.min(0)-pb.max(0),pb.min(0)-pa.max(0))
    i=int(np.argmax(gaps))
    return float(gaps[i])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--urdf',type=Path,required=True)
    parser.add_argument('--cooking-report',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('fresh report required')
    root=ET.parse(args.urdf).getroot(); fk=NativeFK(root)
    cooked=json.loads(args.cooking_report.read_text())
    if cooked['status']!='pass': parser.error('cooking export must pass')
    raw={}; meshes={}; meshhash={}
    for row in cooked['colliders']:
        if sha256(row['raw_path'])!=row['raw_sha256']: raise ValueError('raw cooking hash mismatch')
        raw[row['link']]=json.loads(Path(row['raw_path']).read_text())
    for name in ('tool_r_1','tool_r_2','tool_l_1','tool_l_2'):
        visual=root.find(f"link[@name='{name}']/visual")
        path=Path(unquote(urlparse(visual.find('geometry/mesh').get('filename')).path))
        meshes[name]=transformed(stl_vertices(path),origin_transform(visual.find('origin')))
        meshhash[name]=sha256(path)
    samples=[]
    for q in (0.,.3,.65,.70,.75,.82,.865):
        for side in ('l','r'):
            left,right=f'tool_{side}_1',f'tool_{side}_2'
            fa,fb=fk.frame(left,q),fk.frame(right,q)
            tri=triangle_intersections(transformed(meshes[left],fa).reshape(-1,3,3),transformed(meshes[right],fb).reshape(-1,3,3))
            ra,rb=raw[left],raw[right]
            ta=fa@np.array(ra['mesh_to_body_row_matrix']).T
            tb=fb@np.array(rb['mesh_to_body_row_matrix']).T
            pairs=[]
            for ia,ha in enumerate(ra['hulls']):
                for ib,hb in enumerate(rb['hulls']):
                    gap=convex_sat(ha,hb,ta,tb)
                    if gap<.002:
                        pairs.append(dict(hull_indices=[ia,ib],largest_axis_gap_m=gap,geometric_overlap=gap<0))
            samples.append(dict(q_rad=q,links=[left,right],source=tri,
                cooked_overlapping_pair_count=sum(r['geometric_overlap'] for r in pairs),
                near_pairs=sorted(pairs,key=lambda r:r['largest_axis_gap_m'])))
    result=dict(schema='native_collision_fidelity_v1',urdf_sha256=sha256(args.urdf),source_mesh_sha256=meshhash,
        cooking_report_sha256=sha256(args.cooking_report),samples=samples,physics_steps=0,
        limitations=['Source triangle intersection is not a solid-containment/minimum-distance test.',
                    'SAT uses ideal source poses, not measured dynamics; positive gap is an axis-distance lower bound.',
                    'Existing contact offsets can create contact before geometric overlap; no filters or geometry changed.'])
    with args.output.open('x') as stream: json.dump(result,stream,indent=2)
    print(json.dumps([dict(q=s['q_rad'],links=s['links'],source_crossings=s['source']['surface_intersecting_triangle_pairs'],cooked_overlap=s['cooked_overlapping_pair_count'],min_axis_gap=min([p['largest_axis_gap_m'] for p in s['near_pairs']],default=None)) for s in samples],indent=2))


if __name__=='__main__': main()
