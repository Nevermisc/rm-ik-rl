"""Read-only source/derived URDF structure and STL inertial-consistency audit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import unquote,urlparse
import numpy as np
from audit_gripper_visual_collision import stl_vertices,transformed
from household_grasp_calibration import origin_transform


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flatten(element,path='',prefix=''):
    if element is None:
        return {path:None}
    result={path+'/tag':element.tag}
    for key,value in element.attrib.items():
        if key=='filename':
            value=Path(unquote(urlparse(value).path)).name
        elif prefix and key in ('name','link','joint') and value.startswith(prefix):
            value=value[len(prefix):]
        else:
            try:
                values=[float(x) for x in value.split()]
                value=values[0] if len(values)==1 else values
            except ValueError:
                pass
        result[path+'/@'+key]=value
    seen={}
    for child in element:
        index=seen.get(child.tag,0)
        seen[child.tag]=index+1
        result.update(flatten(child,f'{path}/{child.tag}[{index}]',prefix))
    return result


def differences(a,b,prefix=''):
    left,right=flatten(a),flatten(b,prefix=prefix)
    result=[]
    for key in sorted(set(left)|set(right)):
        x,y=left.get(key),right.get(key)
        if isinstance(x,(float,list)) and isinstance(y,type(x)):
            equal=np.shape(x)==np.shape(y) and np.allclose(x,y,atol=1e-14,rtol=1e-10)
        else:
            equal=x==y
        if not equal:
            result.append(dict(field=key,source=x,derived=y))
    return result


def triangle_stats(points):
    tri=np.asarray(points).reshape(-1,3,3)
    cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    area=np.linalg.norm(cross,axis=1)/2
    _,indices=np.unique(np.round(tri.reshape(-1,3),8),axis=0,return_inverse=True)
    ids=indices.reshape(-1,3)
    edges=np.concatenate((ids[:,[0,1]],ids[:,[1,2]],ids[:,[2,0]]))
    signs=np.sign(edges[:,1]-edges[:,0])
    _,inverse,counts=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True)
    winding=np.bincount(inverse,weights=signs)
    six_volume=np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2]))
    volume=float(six_volume.sum()/6)
    centroid=np.sum(six_volume[:,None]*tri.sum(axis=1),axis=0)/(4*six_volume.sum()) if abs(volume)>1e-15 else None
    return dict(triangles=len(tri),bounds_m=[points.min(axis=0).tolist(),points.max(axis=0).tolist()],
        surface_area_m2=float(area.sum()),degenerate_triangles=int(np.sum(area<1e-14)),
        non_two_manifold_edge_count=int(np.sum(counts!=2)),inconsistent_edge_winding_count=int(np.sum(winding!=0)),
        signed_volume_m3=volume,uniform_density_surface_centroid_m=None if centroid is None else centroid.tolist(),
        centroid_is_uniform_density_diagnostic_not_true_mass_measurement=True)


def source_report(urdf,meshdir):
    root=ET.parse(urdf).getroot()
    links=[]
    for link in root.findall('link'):
        visual=link.find('visual')
        mesh=visual.find('geometry/mesh')
        path=Path(meshdir)/Path(mesh.get('filename')).name
        scale=np.fromstring(mesh.get('scale','1 1 1'),sep=' ')
        points=transformed(stl_vertices(path)*scale,origin_transform(visual.find('origin')))
        stats=triangle_stats(points)
        inertial=link.find('inertial')
        com=origin_transform(inertial.find('origin'))[:3,3]
        bounds=np.array(stats['bounds_m'])
        outside=np.maximum(np.maximum(bounds[0]-com,com-bounds[1]),0)
        i=inertial.find('inertia')
        xx,yy,zz,xy,xz,yz=[float(i.get(k)) for k in ('ixx','iyy','izz','ixy','ixz','iyz')]
        eig=np.linalg.eigvalsh([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
        links.append(dict(name=link.get('name'),mesh=str(path.resolve()),mesh_sha256=sha(path),
            scale=scale.tolist(),mass_kg=float(inertial.find('mass').get('value')),
            center_of_mass_m=com.tolist(),com_outside_visual_aabb_m=outside.tolist(),
            principal_inertia_kg_m2=eig.tolist(),inertia_positive_definite=bool(eig.min()>0),
            inertia_triangle_inequality=bool(eig[-1]<=eig[:2].sum()+1e-10),mesh_stats=stats,
            visual_collision_differences=differences(visual.find('geometry'),link.find('collision/geometry'))))
    joints=[]
    for j in root.findall('joint'):
        joints.append(dict(name=j.get('name'),type=j.get('type'),parent=j.find('parent').get('link'),
            child=j.find('child').get('link'),origin=flatten(j.find('origin')),
            axis=flatten(j.find('axis')),limit=flatten(j.find('limit')),mimic=flatten(j.find('mimic'))))
    names=[l['name'] for l in links]
    children=[j['child'] for j in joints]
    roots=set(names)-set(children)
    return dict(path=str(Path(urdf).resolve()),sha256=sha(urdf),links=links,joints=joints,
                root_links=sorted(roots),duplicate_link_names=len(names)!=len(set(names)),
                multiply_parented_links=len(children)!=len(set(children))),root


def compare(urdf,arm,gripper,expected_mesh_hashes=None):
    root=ET.parse(urdf).getroot()
    changes=[]
    source_expected=set()
    for source,prefix in ((arm,''),(gripper,'tool_')):
        for tag in ('link','joint'):
            for element in source.findall(tag):
                name=prefix+element.get('name')
                source_expected.add((tag,name))
                actual=root.find(f"{tag}[@name='{name}']")
                delta=differences(element,actual,prefix)
                if delta:
                    changes.append(dict(type=tag,name=name,changes=delta))
    extra=[dict(type=e.tag,name=e.get('name'),data=flatten(e)) for e in root if e.tag in ('link','joint') and (e.tag,e.get('name')) not in source_expected]
    meshes=[]
    for link in root.findall('link'):
        source_key=('gripper:' + link.get('name')[5:]) if link.get('name').startswith('tool_') else 'arm:'+link.get('name')
        for mesh in link.findall('.//mesh'):
            path=Path(unquote(urlparse(mesh.get('filename')).path))
            actual=sha(path) if path.is_file() else None
            meshes.append(dict(link=link.get('name'),path=str(path),sha256=actual,
                               matches_source_content=expected_mesh_hashes is not None and actual==expected_mesh_hashes.get(source_key)))
    return dict(path=str(Path(urdf).resolve()),sha256=sha(urdf),source_changes=changes,extra_elements=extra,meshes=meshes,
        link_count=len(root.findall('link')),joint_count=len(root.findall('joint')),
        mimic_count=len(root.findall('joint/mimic')),collision_count=len(root.findall('link/collision')))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('arm-urdf','arm-mesh-dir','gripper-urdf','gripper-mesh-dir','generated-dir','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('fresh audit output required')
    a,arm=source_report(args.arm_urdf,args.arm_mesh_dir)
    g,gripper=source_report(args.gripper_urdf,args.gripper_mesh_dir)
    urdfs=sorted(args.generated_dir.glob('*.urdf'))+sorted(args.generated_dir.glob('native*/native.urdf'))
    hashes={part+':'+l['name']:l['mesh_sha256'] for part,s in (('arm',a),('gripper',g)) for l in s['links']}
    result=dict(schema='rm65_source_model_lineage_audit_v1',read_only=True,physics_steps=0,
        sources={'arm':a,'gripper':g},derived=[compare(p,arm,gripper,hashes) for p in urdfs],
        limitations=['Current supplied source files are not independently verified hardware CAD.',
                     'Canonical comparison ignores XML formatting, namespace prefix and mesh URI spelling, not geometry transforms.',
                     'Mesh centroid assumes uniform density; AABB exclusion flags need original CAD/inertia review.',
                     'URDF audit cannot establish authored USD or runtime overrides; these are separately audited.'])
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2)
    print(json.dumps(dict(source_link_counts={k:len(v['links']) for k,v in result['sources'].items()},
        source_com_outside=[{'part':k,'link':l['name'],'outside_m':l['com_outside_visual_aabb_m']} for k,s in result['sources'].items() for l in s['links'] if max(l['com_outside_visual_aabb_m'])>1e-6],
        derived=[dict(path=r['path'],changed=[x['name'] for x in r['source_changes']],mimics=r['mimic_count'],collisions=r['collision_count']) for r in result['derived']]),indent=2))


if __name__=='__main__':
    main()
