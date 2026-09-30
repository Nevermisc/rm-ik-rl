"""Fresh, source-faithful 4C2 mesh candidate; never modifies historical assets."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

import numpy as np
from build_combined_urdf import prefix_gripper_names, rewrite_meshes
from household_grasp_calibration import origin_transform


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mesh_signature(element):
    mesh = element.find('geometry/mesh')
    if mesh is None or len(element.find('geometry')) != 1:
        raise ValueError('native gripper requires exactly one mesh per geometry')
    filename = mesh.get('filename', '')
    if not filename.startswith('file:'):
        raise ValueError('mesh path must be resolved before audit')
    path = Path(unquote(urlparse(filename).path)).resolve()
    if not path.is_file():
        raise ValueError('missing native mesh')
    scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
    frame = origin_transform(element.find('origin'))
    if scale.shape != (3,) or not np.isfinite(scale).all() or not np.allclose(scale, 1, atol=0, rtol=0):
        raise ValueError('native source must remain at unit scale')
    if not np.isfinite(frame).all():
        raise ValueError('non-finite native mesh transform')
    return str(path), scale, frame


def audit_native_source(robot):
    links = [link for link in robot.findall('link') if link.get('name', '').startswith('tool_')]
    if len(links) != 9:
        raise ValueError('expected nine source 4C2 links')
    records = []
    for link in links:
        visuals, collisions = link.findall('visual'), link.findall('collision')
        if len(visuals) != 1 or len(collisions) != 1:
            raise ValueError('one source visual and one matching collision required; extra pads forbidden')
        a, b = mesh_signature(visuals[0]), mesh_signature(collisions[0])
        if a[0] != b[0] or not np.array_equal(a[1], b[1]) or not np.allclose(a[2], b[2], atol=1e-12, rtol=0):
            raise ValueError('collision must coincide with original visible mesh')
        inertia = link.find('inertial/inertia')
        mass = float(link.find('inertial/mass').get('value'))
        xx, yy, zz, xy, xz, yz = [float(inertia.get(k)) for k in ('ixx','iyy','izz','ixy','ixz','iyz')]
        eig = np.linalg.eigvalsh([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])
        if not np.isfinite(mass) or mass <= 0 or not np.isfinite(eig).all() or eig.min() <= 0 or eig[-1] > eig[:2].sum() + 1e-10:
            raise ValueError('invalid mass/inertia; do not silently regularize')
        records.append(dict(link=link.get('name'), mesh=a[0], sha256=sha256(a[0]),
                            mass_kg=mass, principal_inertia_kg_m2=eig.tolist(),
                            visual_collision_transform_equal=True))
    joints = [j for j in robot.findall('joint') if j.get('name', '').startswith('tool_') and j.get('type') != 'fixed']
    master = next((j for j in joints if j.get('name') == 'tool_gripper_joint'), None)
    if len(joints) != 6 or master is None or master.find('mimic') is not None:
        raise ValueError('expected one master and five followers')
    limit = master.find('limit')
    if float(limit.get('lower')) != 0 or float(limit.get('upper')) != .865:
        raise ValueError('unexpected native master limits')
    followers = []
    for joint in joints:
        if joint is master:
            continue
        mimic = joint.find('mimic')
        if mimic is None or mimic.get('joint') != master.get('name') or float(mimic.get('multiplier','1')) != 1 or float(mimic.get('offset','0')) != 0:
            raise ValueError('source 4C2 requires five unchanged 1:1 mimic relationships')
        followers.append(joint.get('name'))
    return dict(links=records, master=master.get('name'), followers=sorted(followers),
                master_limit_rad=[0., .865], source_total_gripper_mass_kg=sum(r['mass_kg'] for r in records))


def build(arm_path, arm_meshes, gripper_path, gripper_meshes, destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('fresh candidate directory required; historical assets are immutable')
    arm = ET.parse(arm_path).getroot()
    gripper = ET.parse(gripper_path).getroot()
    rewrite_meshes(arm, Path(arm_meshes))
    rewrite_meshes(gripper, Path(gripper_meshes))
    prefix_gripper_names(gripper, 'tool_')
    audit = audit_native_source(gripper)
    if 'link_6' not in {x.get('name') for x in arm.findall('link')}:
        raise ValueError('missing RM65 flange')
    for element in gripper:
        arm.append(copy.deepcopy(element))
    mount = ET.SubElement(arm, 'joint', name='rm65_to_4c2', type='fixed')
    ET.SubElement(mount, 'origin', xyz='0 0 0', rpy='0 0 0')
    ET.SubElement(mount, 'parent', link='link_6')
    ET.SubElement(mount, 'child', link='tool_base_link')
    arm.set('name', 'rm65_4c2_native')
    mesh_hashes = {}
    for mesh in arm.findall('.//mesh'):
        path = Path(unquote(urlparse(mesh.get('filename')).path))
        mesh_hashes[str(path)] = sha256(path)
    report = dict(schema='rm65_native_mesh_candidate_v1', simulation_only=True,
                  sources={str(Path(p).resolve()):sha256(p) for p in (arm_path,gripper_path)},
                  mesh_sha256=mesh_hashes, gripper=audit, added_collision_pads=0,
                  source_dimensions_preserved=True, source_inertias_preserved=True,
                  mount_xyz_m=[0,0,0], mount_rpy_rad=[0,0,0],
                  imported_physics_validated=False, training_ready=False,
                  hardware_validated=False, pi05_used=False)
    destination.mkdir(parents=True, exist_ok=False)
    urdf = destination / 'native.urdf'
    ET.indent(arm, space='  ')
    with urdf.open('xb') as stream:
        ET.ElementTree(arm).write(stream, encoding='utf-8', xml_declaration=True)
    report.update(urdf=str(urdf), urdf_sha256=sha256(urdf))
    with (destination / 'source_audit.json').open('x') as stream:
        json.dump(report, stream, indent=2)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('arm-urdf','arm-mesh-dir','gripper-urdf','gripper-mesh-dir','destination'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.arm_urdf, args.arm_mesh_dir, args.gripper_urdf, args.gripper_mesh_dir, args.destination), indent=2))
