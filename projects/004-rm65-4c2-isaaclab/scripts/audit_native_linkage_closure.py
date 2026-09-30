"""Read-only pivot-coincidence test for the source gripper's contacting links.

This tests whether a fixed material point in each link can coincide throughout
the prescribed motion. A fit is a kinematic hypothesis, never authority to
disable collisions: CAD hinge geometry and cooked shapes still need inspection.
"""
import argparse
import itertools
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET
import numpy as np
from audit_native_aperture import NativeFK
from audit_gripper_visual_collision import stl_vertices, transformed
from build_native_gripper_candidate import sha256
from household_grasp_calibration import origin_transform


def pivot_fit(frames_a, frames_b, bounds_a, bounds_b):
    a, b = np.asarray(frames_a), np.asarray(frames_b)
    if a.shape != b.shape or a.ndim != 3 or a.shape[1:] != (4, 4) or len(a) < 3:
        raise ValueError('at least three paired rigid transforms required')
    ba, bb = np.asarray(bounds_a), np.asarray(bounds_b)
    if ba.shape != (2, 3) or bb.shape != (2, 3) or not np.isfinite(np.r_[a.ravel(), b.ravel(), ba.ravel(), bb.ravel()]).all():
        raise ValueError('finite transforms and bounds required')
    matrix = np.concatenate([a[:, :3, :3], -b[:, :3, :3]], axis=2).reshape(-1, 6)
    rhs = (b[:, :3, 3] - a[:, :3, 3]).reshape(-1)
    center = np.r_[ba.mean(axis=0), bb.mean(axis=0)]
    correction, _, rank, _ = np.linalg.lstsq(matrix, rhs - matrix @ center, rcond=1e-9)
    solution = center + correction
    residual = (matrix @ solution - rhs).reshape(-1, 3)
    error = float(np.linalg.norm(residual, axis=1).max())
    # A true relative hinge gives a one-dimensional family along its axis.
    feasible = False
    nullity = 6 - int(rank)
    interval = None
    axis_a, axis_b = None, None
    if nullity == 1:
        _, _, vh = np.linalg.svd(matrix, full_matrices=False)
        direction = vh[-1]
        axis_a = (direction[:3] / np.linalg.norm(direction[:3])).tolist()
        axis_b = (direction[3:] / np.linalg.norm(direction[3:])).tolist()
        lower, upper = np.r_[ba[0], bb[0]], np.r_[ba[1], bb[1]]
        tmin, tmax = -np.inf, np.inf
        for p, d, lo, hi in zip(solution, direction, lower, upper):
            if abs(d) < 1e-9:
                if not lo - 1e-6 <= p <= hi + 1e-6:
                    tmin, tmax = 1., 0.
                    break
            else:
                ends = sorted(((lo - p) / d, (hi - p) / d))
                tmin, tmax = max(tmin, ends[0]), min(tmax, ends[1])
        feasible = bool(tmin <= tmax)
        if feasible:
            interval = [float(tmin), float(tmax)]
            solution += direction * np.clip(0, tmin, tmax)
    return dict(matrix_rank=int(rank), nullity=nullity, max_pivot_coincidence_error_m=error,
                fixed_point_in_link_a_m=solution[:3].tolist(), fixed_point_in_link_b_m=solution[3:].tolist(),
                pivot_axis_link_a=axis_a, pivot_axis_link_b=axis_b,
                pivot_axis_has_points_inside_both_aabbs=feasible, null_parameter_interval=interval,
                plausible_kinematic_hinge=bool(error < 1e-6 and nullity == 1 and feasible),
                collision_filter_authorized=False)


def cylinder_profiles(vertices, pivot, axis):
    """Find actual triangulated cylindrical side surfaces around a candidate axis.

    Reports inside/outside normal orientation and angular coverage. No convex
    hull is manufactured, and absence of a profile is not absence of a hinge.
    """
    triangles = np.asarray(vertices).reshape(-1, 3, 3)
    origin, direction = np.asarray(pivot), np.asarray(axis)
    direction = direction / np.linalg.norm(direction)
    offset = triangles - origin
    along = offset @ direction
    radial = offset - along[:, :, None] * direction
    radius = np.linalg.norm(radial, axis=2)
    cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2
    valid = (np.ptp(radius, axis=1) < 2e-6) & (radius.mean(axis=1) > 1e-5) & (area > 1e-12)
    valid &= np.abs(cross @ direction) < .01 * np.linalg.norm(cross, axis=1)
    groups = {}
    for i in np.flatnonzero(valid):
        key = int(round(radius[i].mean() / 1e-5))
        groups.setdefault(key, []).append(i)
    reference = np.eye(3)[np.argmin(np.abs(direction))]
    u = np.cross(direction, reference)
    u /= np.linalg.norm(u)
    v = np.cross(direction, u)
    reports = []
    for indices in groups.values():
        if len(indices) < 8:
            continue
        flat = radial[indices].reshape(-1, 3)
        angles = np.unique(np.mod(np.arctan2(flat @ v, flat @ u), 2*np.pi))
        coverage = 2*np.pi - np.diff(np.r_[angles, angles[0] + 2*np.pi]).max()
        dots = np.einsum('ij,ij->i', cross[indices], radial[indices].mean(axis=1))
        inward = float(area[indices][dots < 0].sum() / area[indices].sum())
        reports.append(dict(radius_m=float(np.mean(radius[indices])), triangle_count=len(indices),
            angular_coverage_deg=float(np.rad2deg(coverage)), axial_interval_m=[float(along[indices].min()),float(along[indices].max())],
            area_m2=float(area[indices].sum()), inward_normal_area_fraction=inward,
            interpretation='hole_candidate' if inward > .9 else 'pin_candidate' if inward < .1 else 'mixed_normals'))
    return sorted(reports, key=lambda r:r['radius_m'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--urdf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('fresh report required')
    root = ET.parse(args.urdf).getroot()
    fk = NativeFK(root)
    links = [l for l in root.findall('link') if l.get('name').startswith('tool_')]
    qs = np.linspace(0., .865, 19)
    frames, boxes, hashes, surfaces = {}, {}, {}, {}
    for link in links:
        name = link.get('name')
        mesh = link.find('visual/geometry/mesh')
        path = Path(unquote(urlparse(mesh.get('filename')).path))
        vertices = transformed(stl_vertices(path), origin_transform(link.find('visual/origin')))
        boxes[name] = np.array([vertices.min(axis=0), vertices.max(axis=0)])
        surfaces[name] = vertices
        frames[name] = [fk.frame(name, float(q)) for q in qs]
        hashes[name] = sha256(path)
    adjacent = {frozenset([j.find('parent').get('link'), j.find('child').get('link')]) for j in root.findall('joint')}
    pairs = []
    for a, b in itertools.combinations(sorted(frames), 2):
        fit = pivot_fit(frames[a], frames[b], boxes[a], boxes[b])
        if fit['plausible_kinematic_hinge']:
            fit['source_cylinder_profiles'] = {
                name: cylinder_profiles(surfaces[name], fit[f'fixed_point_in_link_{side}_m'], fit[f'pivot_axis_link_{side}'])
                for name, side in ((a, 'a'), (b, 'b'))}
        pairs.append(dict(links=[a,b], directly_jointed=frozenset([a,b]) in adjacent, **fit))
    result = dict(schema='rm65_native_linkage_pivot_audit_v1', urdf_sha256=sha256(args.urdf),
        mesh_sha256=hashes, q_samples_rad=qs.tolist(), pairs=pairs, read_only=True, physics_steps=0,
        limitations=['AABB inclusion is not proof of an actual pin, material overlap, or a collision-filter rule.',
                     'Rigid/fixed-connected pairs have higher nullity and are not flagged as independent hinges.',
                     'No source or USD geometry, inertia, constraint, or collision mask changed.'])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps([r for r in pairs if r['plausible_kinematic_hinge'] and not r['directly_jointed']], indent=2))


if __name__ == '__main__':
    main()
