"""Read-only CPU reconstruction of logged native fingertip/object intersections.

Writes fresh evidence only.  Actual link frames are reconstructed from paired
world/link contact points logged in one physics frame; source FK is not used
as a substitute for actual articulation pose.  A geometric intersection is
not a diagnosis of why the contact solver permitted it.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

import numpy as np

from native_contact_geometry import load_inner_triangles


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def quaternion_matrix(wxyz):
    q = np.asarray(wxyz, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all() or np.linalg.norm(q) < 1e-12:
        raise ValueError('finite nonzero object quaternion required')
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def reconstruct_body_frame(contacts):
    local = np.asarray([c['point_link_m'] for c in contacts], dtype=float)
    world = np.asarray([c['point_world_m'] for c in contacts], dtype=float)
    if local.ndim != 2 or local.shape != world.shape or local.shape[1:] != (3,) or not np.isfinite(np.r_[local.ravel(), world.ravel()]).all():
        return dict(valid=False, reason='invalid_correspondences')
    x, y = local-local.mean(0), world-world.mean(0)
    spread = np.linalg.svd(x, compute_uv=False)
    rank = int(np.sum(spread > max(1e-8, float(spread[0])*1e-6))) if len(spread) else 0
    result = dict(point_count=len(local), centered_local_rank=rank, singular_values_m=spread.tolist())
    if len(local) < 3 or rank < 2:
        return dict(result, valid=False, reason='fewer_than_three_noncollinear_points')
    u, _, vt = np.linalg.svd(x.T @ y)
    correction = np.eye(3)
    correction[2, 2] = np.linalg.det(vt.T @ u.T)
    rot = vt.T @ correction @ u.T
    position = world.mean(0) - rot @ local.mean(0)
    errors = np.linalg.norm(local @ rot.T + position - world, axis=1)
    return dict(result, valid=bool(errors.max() < 1e-5),
        reason=None if errors.max() < 1e-5 else 'rigid_fit_residual_exceeds_10_um',
        rotation_local_to_world=rot.tolist(), position_world_m=position.tolist(),
        rms_residual_m=float(np.sqrt(np.mean(errors**2))), max_residual_m=float(errors.max()),
        determinant=float(np.linalg.det(rot)))


def clip_triangle_to_box(triangle, half_extents):
    """Sutherland-Hodgman clipping of one 3-D triangle against six box planes."""
    triangle, half = np.asarray(triangle, float), np.asarray(half_extents, float)
    if triangle.shape != (3, 3) or half.shape != (3,) or not np.isfinite(np.r_[triangle.ravel(), half]).all() or np.any(half <= 0):
        raise ValueError('finite triangle and positive box half extents required')
    polygon = [v.copy() for v in triangle]
    for axis in range(3):
        for sign in (-1., 1.):
            output = []
            for a, b in zip(polygon, polygon[1:] + polygon[:1]):
                da, db = half[axis]-sign*a[axis], half[axis]-sign*b[axis]
                ina, inb = da >= 0, db >= 0
                if ina:
                    output.append(a)
                if ina != inb:
                    output.append(a + (b-a)*(da/(da-db)))
            polygon = output
            if not polygon:
                return np.empty((0, 3))
    return np.asarray(polygon)


def triangle_box_evidence(triangles_object, half_extents, witness_threshold_m=1e-4):
    """Return finite source-face area lying in the solid box and interior witnesses.

    The margin is the distance of an interior witness to its nearest box face;
    it is a conservative positive witness, not the full mesh penetration depth.
    """
    half = np.asarray(half_extents, float)
    rows = []
    for index, triangle in enumerate(triangles_object):
        polygon = clip_triangle_to_box(triangle, half)
        if len(polygon) < 3:
            continue
        pieces = np.array([[polygon[0], polygon[j], polygon[j+1]] for j in range(1, len(polygon)-1)])
        areas = np.linalg.norm(np.cross(pieces[:, 1]-pieces[:, 0], pieces[:, 2]-pieces[:, 0]), axis=1)/2
        area = float(areas.sum())
        if area <= 1e-12:
            continue
        witness = np.average(pieces.mean(axis=1), weights=areas, axis=0)
        margin = float(np.min(half-np.abs(witness)))
        rows.append(dict(source_triangle_index=index, clipped_area_m2=area,
            interior_witness_object_m=witness.tolist(), witness_nearest_box_face_margin_m=margin,
            clipped_polygon_object_m=polygon.tolist()))
    max_margin = max((r['witness_nearest_box_face_margin_m'] for r in rows), default=0.)
    return dict(source_face_triangle_count=len(triangles_object), intersecting_triangle_count=len(rows),
        source_face_area_in_closed_box_m2=sum(r['clipped_area_m2'] for r in rows),
        max_interior_witness_margin_m=max_margin,
        strict_source_face_inside_object=bool(max_margin > witness_threshold_m),
        witness_threshold_m=witness_threshold_m, triangle_intersections=rows)


def select_frames(telemetry, force_min_N=.001):
    chosen = {}
    for line_number, line in enumerate(Path(telemetry).open(), 1):
        row = json.loads(line)
        for pair in row['raw_contacts']:
            if pair['body'] not in ('tool_l_3', 'tool_r_3'):
                continue
            for contact in pair['contacts']:
                if abs(contact['force_N']) <= force_min_N:
                    continue
                width = float(row['width_m'])
                if width not in chosen or contact['separation_m'] < chosen[width]['worst_contact']['separation_m']:
                    chosen[width] = dict(telemetry_line_number=line_number, row=row,
                        worst_body=pair['body'], worst_contact=contact)
    return chosen


def audit(telemetry, urdf, output_dir, summary_path):
    output_dir, summary_path = Path(output_dir), Path(summary_path)
    if output_dir.exists() or summary_path.exists():
        raise ValueError('fresh raw output directory and summary required')
    faces = load_inner_triangles(urdf)
    selected = select_frames(telemetry)
    if set(selected) != {.02, .035, .05}:
        raise ValueError('all three frozen widths must have force-bearing fingertip contacts')
    output_dir.mkdir(parents=True)
    cases = []
    for width, choice in sorted(selected.items()):
        row = choice['row']
        object_position = np.asarray(row['object_pos_m'], float)
        object_rotation = quaternion_matrix(row['object_quat_wxyz'])
        half = np.array([.01, width/2, .01])
        case = dict(width_m=width, step=row['step'], phase=row['phase'],
            telemetry_line_number=choice['telemetry_line_number'], worst_body=choice['worst_body'],
            worst_contact=choice['worst_contact'], object_position_world_m=object_position.tolist(),
            object_rotation_local_to_world=object_rotation.tolist(), object_half_extents_m=half.tolist(), bodies={})
        for pair in row['raw_contacts']:
            name = pair['body']
            if name not in faces:
                continue
            contacts = [c for c in pair['contacts'] if 'point_link_m' in c]
            fit = reconstruct_body_frame(contacts)
            body = dict(pose_reconstruction=fit)
            if fit['valid']:
                rot, pos = np.asarray(fit['rotation_local_to_world']), np.asarray(fit['position_world_m'])
                world = faces[name] @ rot.T + pos
                object_local = (world-object_position) @ object_rotation
                body['source_face_vs_actual_object'] = triangle_box_evidence(object_local, half)
            case['bodies'][name] = body
        raw_path = output_dir/f'width_{round(width*1000):03d}_selected_frame.json'
        raw_path.write_text(json.dumps(dict(selection=case, original_telemetry_record=row), indent=2, allow_nan=False))
        case['raw_evidence_path'] = str(raw_path)
        case['raw_evidence_sha256'] = sha256(raw_path)
        for body in case['bodies'].values():
            if 'source_face_vs_actual_object' in body:
                body['source_face_vs_actual_object'].pop('triangle_intersections')
        case['source_face_penetration_confirmed'] = any(
            b.get('source_face_vs_actual_object', {}).get('strict_source_face_inside_object', False)
            for b in case['bodies'].values())
        cases.append(case)
    root = ET.parse(urdf).getroot()
    mesh_hashes = {}
    for name in faces:
        filename = root.find(f"link[@name='{name}']/visual/geometry/mesh").get('filename')
        mesh = Path(unquote(urlparse(filename).path))
        mesh_hashes[str(mesh)] = sha256(mesh)
    manifest = Path(telemetry).parent/'manifest.json'
    report = dict(schema='rm65_native_external_contact_geometry_v1', read_only_physics=True,
        physics_steps=0, simulation_only=True, pi05_used=False, training_ready=False,
        telemetry_path=str(telemetry), telemetry_sha256=sha256(telemetry),
        source_urdf_path=str(urdf), source_urdf_sha256=sha256(urdf), source_inner_mesh_sha256=mesh_hashes,
        runner_manifest_sha256=sha256(manifest) if manifest.exists() else None,
        analysis_script_sha256=sha256(__file__), selection_force_threshold_N=.001,
        pose_evidence='Single-frame paired point_link_m / point_world_m; least-squares proper rigid transform.',
        source_fk_substituted_for_actual_body_pose=False, cases=cases,
        conclusion='source_inner_surfaces_intersect_actual_object_solids' if all(c['source_face_penetration_confirmed'] for c in cases) else 'per_case_geometry_evidence_required',
        limitations=[
            'Reconstruction depends on correctness of logged point_link_m conversion; paired points are not an independent sensor.',
            'The link transform and object pose are post-step telemetry; PhysX contact separation may refer to an earlier solver/contact-generation instant within that step. Negative separation is not equated numerically to post-step overlap.',
            'Geometric overlap is demonstrated by finite source triangles inside actual logged cuboid poses, not by PhysX separation alone.',
            'Interior witness margin is a conservative distance to the nearest object face, not exact penetration depth.',
            'This does not identify whether drive, solver, convex decomposition, collision topology, or another factor caused overlap.',
            'Only the selected extreme frames were audited; cooked convex shapes were not used in this source-surface proof.',
        ])
    summary_path.write_text(json.dumps(report, indent=2, allow_nan=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--telemetry', type=Path, required=True)
    parser.add_argument('--urdf', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.telemetry, args.urdf, args.output_dir, args.summary)
    print(json.dumps(dict(conclusion=result['conclusion'], cases=[dict(width_m=c['width_m'],step=c['step'],
        source_face_penetration_confirmed=c['source_face_penetration_confirmed'],bodies=c['bodies']) for c in result['cases']]), indent=2))
