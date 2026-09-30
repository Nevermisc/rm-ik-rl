"""CPU geometry for native contact diagnostics; no simulation or asset mutation.

Mesh triangles and contact points use link-local metres. ``scene_geometry``
returns JSON-ready lists/scalars. Source face proximity is geometric evidence,
not proof of frictional support, collision fidelity, or policy control.
"""
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

import numpy as np

from audit_gripper_visual_collision import stl_vertices, transformed
from audit_native_aperture import NativeFK, inner_face_patch
from household_grasp_calibration import origin_transform, rotation


CONTACT_LINKS = ('tool_l_3', 'tool_r_3')
DEFAULT_ARM_JOINTS = (0., 0., 0., 0., np.pi / 2, 0.)


def _validated_triangles(triangles):
    triangles = np.asarray(triangles, dtype=float)
    if (triangles.ndim != 3 or triangles.shape[1:] != (3, 3)
            or not len(triangles) or not np.isfinite(triangles).all()):
        raise ValueError('finite nonempty [N,3,3] triangles required')
    ab = triangles[:, 1] - triangles[:, 0]
    ac = triangles[:, 2] - triangles[:, 0]
    twice_area = np.linalg.norm(np.cross(ab, ac), axis=1)
    scale = np.linalg.norm(ab, axis=1) * np.linalg.norm(ac, axis=1)
    if np.any(twice_area <= 1e-14 * scale) or np.any(scale == 0):
        raise ValueError('degenerate triangle is not a contact face')
    return triangles


def _local_mesh_triangles(urdf, root, name):
    link = root.find(f"link[@name='{name}']")
    if link is None or len(link.findall('visual')) != 1:
        raise ValueError(f'exactly one native mesh visual required for {name}')
    visual = link.find('visual')
    mesh = visual.find('geometry/mesh')
    if mesh is None:
        raise ValueError(f'native mesh required for {name}')
    filename = mesh.get('filename', '')
    if filename.startswith('file:'):
        path = Path(unquote(urlparse(filename).path))
    elif '://' in filename:
        raise ValueError('resolved file or local mesh path required')
    else:
        path = Path(filename)
    if not path.is_absolute():
        path = Path(urdf).parent / path
    scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
    if scale.shape != (3,) or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError('invalid native mesh scale')
    vertices = transformed(stl_vertices(path) * scale, origin_transform(visual.find('origin')))
    if len(vertices) % 3:
        raise ValueError('STL vertices do not form complete triangles')
    return vertices.reshape(-1, 3, 3)


def load_inner_triangles(urdf):
    """Return {l3/r3 link name: ndarray[N,3,3]} in each rigid link's frame.

    Select the identical q=0 extreme-plane triangle patch used by
    ``audit_native_aperture.inner_face_patch``, including its area threshold.
    The FK frame is used only for selection; returned triangles remain local.
    """
    root = ET.parse(urdf).getroot()
    fk = NativeFK(root)
    result = {}
    for name in CONTACT_LINKS:
        local = _local_mesh_triangles(urdf, root, name)
        flange = transformed(local.reshape(-1, 3), fk.frame(name, 0.)).reshape(-1, 3, 3)
        patch = inner_face_patch(flange, 1 if name == 'tool_l_3' else -1)
        area = np.linalg.norm(np.cross(flange[:, 1] - flange[:, 0],
                                      flange[:, 2] - flange[:, 0]), axis=1) / 2
        mask = np.all(np.abs(flange[:, :, 1] - patch['plane_y_m']) < 2e-6, axis=1)
        mask &= area > 1e-12
        result[name] = _validated_triangles(local[mask]).copy()
        if len(result[name]) != patch['triangle_count']:
            raise ValueError('native face selection differs from aperture audit')
    return result


def point_to_triangles_distance(point, triangles):
    """Exact minimum Euclidean distance to the union of closed triangles.

    Includes face-interior projections, edges and vertices, so a point outside
    a finite fingertip face cannot pass merely by lying in its infinite plane.
    NaN/Inf, empty arrays and any degenerate triangle are rejected.
    """
    point = np.asarray(point, dtype=float)
    if point.shape != (3,) or not np.isfinite(point).all():
        raise ValueError('finite point with shape [3] required')
    triangles = _validated_triangles(triangles)
    a, b, c = (triangles[:, index] for index in range(3))
    ab, ac, ap = b - a, c - a, point - a
    normal = np.cross(ab, ac)
    normal_sq = np.einsum('ij,ij->i', normal, normal)
    signed_numerator = np.einsum('ij,ij->i', ap, normal)
    projected = ap - (signed_numerator / normal_sq)[:, None] * normal
    # Oriented cross products avoid subtracting almost equal dot products in
    # the barycentric determinant for thin, valid triangles.
    beta = np.einsum('ij,ij->i', np.cross(projected, ac), normal) / normal_sq
    gamma = np.einsum('ij,ij->i', np.cross(ab, projected), normal) / normal_sq
    inside = (beta >= 0) & (gamma >= 0) & (beta + gamma <= 1)
    distances_sq = np.where(inside, signed_numerator ** 2 / normal_sq, np.inf)
    for start, end in ((a, b), (b, c), (c, a)):
        edge = end - start
        amount = np.einsum('ij,ij->i', point - start, edge) / np.einsum('ij,ij->i', edge, edge)
        closest = start + np.clip(amount, 0, 1)[:, None] * edge
        delta = point - closest
        distances_sq = np.minimum(distances_sq, np.einsum('ij,ij->i', delta, delta))
    return float(np.sqrt(np.min(distances_sq)))


def points_to_triangles_distances(points, triangles):
    """Batch the same closed-triangle distance; preserve every contact point.

    This only changes instrumentation cost, never the source face or tolerance.
    An empty contact list is valid; invalid and degenerate geometry still fails.
    """
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1:] != (3,) or not np.isfinite(points).all():
        raise ValueError('finite points with shape [N,3] required')
    triangles = _validated_triangles(triangles)
    if not len(points):
        return np.empty(0, dtype=float)
    a, b, c = (triangles[:, index] for index in range(3))
    ab, ac = b - a, c - a
    ap = points[:, None, :] - a[None, :, :]
    normal = np.cross(ab, ac)
    normal_sq = np.einsum('ij,ij->i', normal, normal)
    numerator = np.einsum('ptj,tj->pt', ap, normal)
    projected = ap - (numerator / normal_sq)[:, :, None] * normal[None, :, :]
    beta = np.einsum('ptj,tj->pt', np.cross(projected, ac), normal) / normal_sq
    gamma = np.einsum('ptj,tj->pt', np.cross(ab, projected), normal) / normal_sq
    inside = (beta >= 0) & (gamma >= 0) & (beta + gamma <= 1)
    distance_sq = np.where(inside, numerator ** 2 / normal_sq, np.inf)
    for start, end in ((a, b), (b, c), (c, a)):
        edge = end - start
        offset = points[:, None, :] - start[None, :, :]
        amount = np.einsum('ptj,tj->pt', offset, edge) / np.einsum('ij,ij->i', edge, edge)
        delta = offset - np.clip(amount, 0, 1)[:, :, None] * edge[None, :, :]
        distance_sq = np.minimum(distance_sq, np.einsum('ptj,ptj->pt', delta, delta))
    return np.sqrt(np.min(distance_sq, axis=1))


def _quaternion_wxyz(matrix):
    """Unit quaternion from a proper rotation, stable around 180 degrees."""
    r = np.asarray(matrix, dtype=float)
    if r.shape != (3, 3) or not np.allclose(r.T @ r, np.eye(3), atol=1e-8) or not np.isclose(np.linalg.det(r), 1.):
        raise ValueError('proper finite rotation required')
    if np.trace(r) > 0:
        s = 2 * np.sqrt(1 + np.trace(r))
        q = np.array([s / 4, (r[2, 1] - r[1, 2]) / s,
                      (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s])
    else:
        i = int(np.argmax(np.diag(r)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = 2 * np.sqrt(1 + r[i, i] - r[j, j] - r[k, k])
        q = np.zeros(4)
        q[0] = (r[k, j] - r[j, k]) / s
        q[i + 1] = s / 4
        q[j + 1] = (r[j, i] + r[i, j]) / s
        q[k + 1] = (r[k, i] + r[i, k]) / s
    q /= np.linalg.norm(q)
    return q if q[0] >= 0 else -q


def scene_geometry(urdf, arm_joints=DEFAULT_ARM_JOINTS, base=(0., 0., .1)):
    """JSON-ready source geometry for a horizontal native grasp diagnostic.

    Object dimensions in palm axes are (20 mm, width, 20 mm), with a common
    centre (0,0,140 mm). Widths/mass/material belong to the caller's protocol.
    No runtime articulation compliance or collision clearance is certified.
    """
    arm = np.asarray(arm_joints, dtype=float)
    base = np.asarray(base, dtype=float)
    if arm.shape != (6,) or base.shape != (3,) or not np.isfinite(np.r_[arm, base]).all():
        raise ValueError('six finite arm angles and three finite base coordinates required')
    root = ET.parse(urdf).getroot()
    frame = np.eye(4)
    frame[:3, 3] = base
    parent = 'base_link'
    for index, q in enumerate(arm, 1):
        joint = root.find(f"joint[@name='joint_{index}']")
        if joint is None or joint.get('type') != 'revolute' or joint.find('parent').get('link') != parent:
            raise ValueError('expected serial RM65 arm chain')
        limit = joint.find('limit')
        if not float(limit.get('lower')) <= q <= float(limit.get('upper')):
            raise ValueError('arm joint outside source limits')
        motion = np.eye(4)
        motion[:3, :3] = rotation(np.fromstring(joint.find('axis').get('xyz'), sep=' '), q)
        frame = frame @ origin_transform(joint.find('origin')) @ motion
        parent = joint.find('child').get('link')
    if parent != 'link_6':
        raise ValueError('arm chain must terminate at flange link_6')
    fk = NativeFK(root)
    palm = frame @ fk.frame('tool_base_link', 0.)
    local = load_inner_triangles(urdf)
    samples = []
    for q in (0., .3, .65, .82):
        faces = {}
        for name, triangles in local.items():
            points = transformed(triangles.reshape(-1, 3), fk.frame(name, q)).reshape(-1, 3, 3)
            faces[name] = inner_face_patch(points, 1 if name == 'tool_l_3' else -1)
        samples.append(dict(q_rad=q, faces=faces,
            gap_m=faces['tool_r_3']['plane_y_m'] - faces['tool_l_3']['plane_y_m'],
            midpoint_flange_m=np.mean([f['centroid_link6_m'] for f in faces.values()], axis=0).tolist()))
    return dict(flange_position=frame[:3, 3].tolist(), flange_rotation=frame[:3, :3].tolist(),
        palm_position=palm[:3, 3].tolist(), palm_rotation=palm[:3, :3].tolist(),
        object_center_palm=[0., 0., .14],
        object_center_world=transformed([[0., 0., .14]], palm)[0].tolist(),
        object_quat_wxyz=_quaternion_wxyz(palm[:3, :3]).tolist(),
        arm_joints_rad=arm.tolist(), base_position=base.tolist(), face_samples=samples,
        simulation_only=True, dynamic_clearance_validated=False)
