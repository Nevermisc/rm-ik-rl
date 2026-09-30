"""Ideal source-URDF inner fingertip face sweep, not a graspability certificate."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET
import numpy as np
from build_native_gripper_candidate import audit_native_source, sha256
from household_grasp_calibration import origin_transform, rotation
from audit_gripper_visual_collision import stl_vertices, transformed


def inner_face_patch(triangles, sign):
    triangles = np.asarray(triangles,dtype=float)
    if triangles.ndim!=3 or triangles.shape[1:]!=(3,3) or not len(triangles) or not np.isfinite(triangles).all() or sign not in (-1,1):
        raise ValueError('invalid triangle surface')
    plane = float(np.max(sign*triangles[:,:,1]))*sign
    selected = triangles[np.all(np.abs(triangles[:,:,1]-plane)<2e-6,axis=1)]
    cross = np.cross(selected[:,1]-selected[:,0],selected[:,2]-selected[:,0])
    areas = np.linalg.norm(cross,axis=1)*.5
    keep = areas>1e-12
    selected, areas, cross = selected[keep],areas[keep],cross[keep]
    if not len(areas) or areas.sum()<1e-6 or not np.all(np.abs(cross[:,1])/(2*areas)>.999):
        raise ValueError('no substantial planar inner face at native fingertip extreme')
    points = selected.reshape(-1,3)
    return dict(plane_y_m=plane,area_m2=float(areas.sum()),triangle_count=len(areas),
        centroid_link6_m=np.average(selected.mean(axis=1),weights=areas,axis=0).tolist(),
        bounds_link6_m=[points.min(axis=0).tolist(),points.max(axis=0).tolist()])


class NativeFK:
    def __init__(self,root):
        self.joints = {j.find('child').get('link'):j for j in root.findall('joint')}
        self.by_name = {j.get('name'):j for j in root.findall('joint')}

    def joint_value(self,joint,q):
        if not np.isfinite(q) or not 0<=q<=.865:
            raise ValueError('native q outside source master limits')
        if joint.get('name')=='tool_gripper_joint':
            return q
        mimic = joint.find('mimic')
        if mimic is None or mimic.get('joint')!='tool_gripper_joint':
            raise ValueError('unsupported native mimic chain')
        value = float(mimic.get('multiplier','1'))*q+float(mimic.get('offset','0'))
        limits = joint.find('limit')
        if not float(limits.get('lower'))<=value<=float(limits.get('upper')):
            raise ValueError('native follower outside source limits')
        return value

    def frame(self,link,q,visited=None):
        if link=='link_6':
            return np.eye(4)
        visited=set() if visited is None else set(visited)
        if link in visited or link not in self.joints:
            raise ValueError('native chain must terminate at flange')
        visited.add(link)
        joint=self.joints[link]
        transform=origin_transform(joint.find('origin'))
        if joint.get('type')=='revolute':
            motion=np.eye(4)
            motion[:3,:3]=rotation(np.fromstring(joint.find('axis').get('xyz'),sep=' '),self.joint_value(joint,q))
            transform=transform@motion
        elif joint.get('type')!='fixed':
            raise ValueError('unsupported native joint')
        return self.frame(joint.find('parent').get('link'),q,visited)@transform


def audit(urdf):
    root=ET.parse(urdf).getroot()
    native=audit_native_source(root)
    fk=NativeFK(root)
    source={}
    for name in ('tool_l_3','tool_r_3'):
        visual=root.find(f"link[@name='{name}']/visual")
        path=Path(unquote(urlparse(visual.find('geometry/mesh').get('filename')).path))
        source[name]=transformed(stl_vertices(path),origin_transform(visual.find('origin')))
    records=[]
    for q in (0.,.1,.2,.3,.4,.5,.6,.65,.7,.75,.8,.82,.865):
        faces={name:inner_face_patch(transformed(points,fk.frame(name,q)).reshape(-1,3,3),
                                     1 if name=='tool_l_3' else -1) for name,points in source.items()}
        gap=faces['tool_r_3']['plane_y_m']-faces['tool_l_3']['plane_y_m']
        records.append(dict(q_rad=q,ideal_inner_face_gap_m=gap,faces=faces))
    return dict(schema='rm65_native_inner_face_geometry_v1',simulation_only=True,urdf_sha256=sha256(urdf),
        source_mesh_sha256={i['link']:i['sha256'] for i in native['links']}, samples=records,
        contact_links=['tool_l_3','tool_r_3'],legacy_pad_geometry_used=False,
        opening_nonincreasing=bool(np.all(np.diff([r['ideal_inner_face_gap_m'] for r in records])<0)),
        dynamic_graspability_validated=False,training_ready=False,
        limitations=['Exact source triangle inner-plane patches under ideal URDF mimic kinematics only.',
                     'Not a collision-free grasp envelope; support, hand sweep, force and real hardware remain unvalidated.',
                     'No object rescaling and no inherited legacy-pad aperture limits.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--urdf',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('new output required')
    result=audit(args.urdf)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
