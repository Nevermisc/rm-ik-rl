"""Read-only bounds audit of legacy added pads against original gripper visuals.

Positive AABB separation proves a gap; overlapping bounds do NOT prove contact.
This inspects source URDF/STL geometry, not imported PhysX hulls or actual hardware.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
from urllib.parse import unquote, urlparse
import numpy as np
from household_grasp_calibration import PadGeometry, origin_transform


def stl_vertices(path):
    raw = Path(path).read_bytes()
    if len(raw) >= 84:
        count = struct.unpack_from('<I', raw, 80)[0]
        if count > 0 and len(raw) == 84 + 50 * count:
            dtype = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3,3)), ('attr', '<u2')])
            vertices = np.frombuffer(raw, dtype=dtype, count=count, offset=84)['vertices'].reshape(-1,3).astype(float)
        else:
            vertices = None
    else:
        vertices = None
    if vertices is None:
        try:
            vertices = np.array([list(map(float, line.split()[1:])) for line in raw.decode('ascii').splitlines()
                                 if line.strip().startswith('vertex ')])
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError('unsupported or corrupt STL') from error
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not len(vertices) or not np.isfinite(vertices).all():
        raise ValueError('invalid STL vertices')
    return vertices


def transformed(points, frame):
    return np.asarray(points) @ frame[:3,:3].T + frame[:3,3]


def bounds(points):
    return np.array([points.min(axis=0), points.max(axis=0)])


def aabb_separation(a, b):
    delta = np.maximum(np.maximum(a[0]-b[1], b[0]-a[1]), 0)
    return float(np.linalg.norm(delta))


def audit(urdf):
    geometry = PadGeometry(urdf)
    visuals, mesh_hashes = {}, {}
    for name, link in geometry.links.items():
        if not name.startswith('tool_'):
            continue
        parts = []
        for visual in link.findall('visual'):
            mesh = visual.find('geometry/mesh')
            if mesh is None:
                raise ValueError('review required for a non-mesh original gripper visual')
            filename = mesh.get('filename')
            path = Path(unquote(urlparse(filename).path)) if filename.startswith('file:') else Path(filename)
            if not path.is_absolute():
                path = Path(urdf).parent / path
            scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
            if scale.shape != (3,) or not np.isfinite(scale).all() or np.any(scale <= 0):
                raise ValueError('invalid visual mesh scale')
            parts.append(transformed(stl_vertices(path) * scale, origin_transform(visual.find('origin'))))
            mesh_hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        if parts:
            visuals[name] = np.concatenate(parts)
    records = []
    for q in (0., .65, .7, .8):
        all_visual_bounds = {name:bounds(transformed(points, geometry.transform(name, q))) for name,points in visuals.items()}
        for name in ('tool_l_2', 'tool_r_2'):
            link = geometry.links[name]
            pad = link.find("collision[@name='contact_pad_box']")
            if pad is None:
                raise ValueError('expected legacy contact pad')
            size = np.fromstring(pad.find('geometry/box').get('size'), sep=' ')
            corners = np.array(list(itertools.product((-1.,1.), repeat=3))) * size / 2
            local_bounds = bounds(transformed(corners, origin_transform(pad.find('origin'))))
            world_bounds = bounds(transformed(corners, geometry.transform(name,q) @ origin_transform(pad.find('origin'))))
            distances = {other:aabb_separation(world_bounds,b) for other,b in all_visual_bounds.items()}
            nearest = min(distances, key=distances.get)
            records.append(dict(q_rad=q, pad_link=name, pad_size_m=size.tolist(),
                pad_local_aabb_m=local_bounds.tolist(), parent_visual_local_aabb_m=bounds(visuals[name]).tolist(),
                gap_to_parent_visual_aabb_lower_bound_m=aabb_separation(local_bounds, bounds(visuals[name])),
                nearest_original_visual_link=nearest, gap_to_all_original_visual_aabbs_lower_bound_m=distances[nearest],
                named_pad_has_visual=link.find("visual[@name='contact_pad_box']") is not None))
    return dict(schema='rm65_legacy_pad_visual_audit_v1', simulation_only=True,
        urdf=str(urdf), urdf_sha256=hashlib.sha256(Path(urdf).read_bytes()).hexdigest(),
        mesh_sha256=mesh_hashes, cases=records,
        detached_from_all_visual_bounds_in_tested_poses=all(r['gap_to_all_original_visual_aabbs_lower_bound_m'] > .001 for r in records),
        minimum_gap_to_all_visual_bounds_m=min(r['gap_to_all_original_visual_aabbs_lower_bound_m'] for r in records),
        training_ready=False, hardware_geometry_validated=False,
        limitations=['AABB distance is a lower bound, not exact mesh-to-mesh distance.',
            'Source URDF/STL check; imported USD/PhysX geometry requires independent verification.',
            'No material, collision, asset or trajectory has been modified.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--urdf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('new output required')
    result = audit(args.urdf)
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
