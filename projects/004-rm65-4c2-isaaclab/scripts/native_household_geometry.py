"""Source-only marker geometry and fixture motion; no simulator or object control."""
from pathlib import Path
import numpy as np

from native_contact_geometry import _quaternion_wxyz
from audit_native_external_contact_geometry import quaternion_matrix

MARKER_TO_PALM = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
SUPPORT_SIZE = np.array([.03, .03, .04])
CATCH_SIZE = np.array([.24, .30, .02])


def read_rigid_mesh(usd_path):
    """Resolve authored mesh transforms into rigid-root metres, without cooking."""
    from pxr import Usd, UsdGeom, UsdPhysics
    stage = Usd.Stage.Open(str(Path(usd_path)))
    root = stage.GetDefaultPrim()
    if not root or not root.HasAPI(UsdPhysics.RigidBodyAPI):
        raise ValueError('default prim must be the source rigid body')
    if UsdGeom.GetStageMetersPerUnit(stage) != 1. or str(UsdGeom.GetStageUpAxis(stage)) != 'Z':
        raise ValueError('source package must use metres and Z-up')
    meshes = [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh) and p.HasAPI(UsdPhysics.CollisionAPI)]
    if len(meshes) != 1:
        raise ValueError('one original mesh collider required')
    prim = meshes[0]
    mesh = UsdGeom.Mesh(prim)
    if not np.all(np.asarray(mesh.GetFaceVertexCountsAttr().Get()) == 3):
        raise ValueError('triangular source mesh required')
    cache = UsdGeom.XformCache()
    transform = cache.GetLocalToWorldTransform(prim) * cache.GetLocalToWorldTransform(root).GetInverse()
    matrix = np.array(transform, dtype=float)
    vertices = np.asarray(mesh.GetPointsAttr().Get(), dtype=float) @ matrix[:3, :3] + matrix[3, :3]
    triangles = np.asarray(mesh.GetFaceVertexIndicesAttr().Get(), dtype=int).reshape(-1, 3)
    if not np.isfinite(vertices).all() or vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError('finite source points required')
    return dict(vertices=vertices, indices=triangles, mesh_path=str(prim.GetPath()),
                mesh_to_rigid_row_matrix=matrix.tolist(), rigid_path=str(root.GetPath()),
                source_mass_kg=float(UsdPhysics.MassAPI(root).GetMassAttr().Get()),
                approximation=str(UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get()))


def marker_initial_geometry(palm_position, palm_rotation, vertices):
    p, R, v = np.asarray(palm_position), np.asarray(palm_rotation), np.asarray(vertices)
    if p.shape != (3,) or R.shape != (3, 3) or v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(np.r_[p.ravel(), R.ravel(), v.ravel()]).all():
        raise ValueError('finite source geometry required')
    rotation = R @ MARKER_TO_PALM
    center = p + R @ np.array([0., 0., .14])
    world = v @ rotation.T + center
    support_center = center.copy()
    support_center[2] = world[:, 2].min() - SUPPORT_SIZE[2]/2
    return dict(position_world_m=center.tolist(), quat_wxyz=_quaternion_wxyz(rotation).tolist(),
                source_to_palm_rotation=MARKER_TO_PALM.tolist(), source_world_bounds_m=[world.min(0).tolist(), world.max(0).tolist()],
                support_center_world_m=support_center.tolist(), support_size_world_m=SUPPORT_SIZE.tolist(),
                catch_center_world_m=(center+np.array([0., 0., -.17])).tolist(), catch_size_world_m=CATCH_SIZE.tolist(),
                catch_top_world_m=float(center[2]-.16))


def object_vertical_bounds(position, quaternion_wxyz, vertices):
    p, v = np.asarray(position, float), np.asarray(vertices, float)
    if p.shape != (3,) or v.ndim != 2 or v.shape[1] != 3 or not len(v) or not np.isfinite(np.r_[p, v.ravel()]).all():
        raise ValueError('finite position and source vertices required')
    height = v @ quaternion_matrix(quaternion_wxyz)[2] + p[2]
    return float(height.min()), float(height.max())


def support_withdraw_offset(fraction):
    """Drop 40 mm, move +X 150 mm above catch, then drop another 60 mm."""
    if not np.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError('fraction must be in [0,1]')
    f = 3*float(fraction)
    return np.array([.15*np.clip(f-1, 0, 1), 0., -.04*np.clip(f, 0, 1)-.06*np.clip(f-2, 0, 1)])
