"""CPU horizontal sections and signed gravity-projection margins."""
import numpy as np
from scipy.spatial import ConvexHull


def horizontal_section(triangles, z, tolerance=1e-12):
    """Return XY intersections of finite triangles with a horizontal plane."""
    tri = np.asarray(triangles, dtype=float)
    if tri.ndim != 3 or tri.shape[1:] != (3, 3) or not np.isfinite(tri).all() or not np.isfinite(z):
        raise ValueError('finite triangles and height required')
    points = []
    for a, b in [(tri[:,0],tri[:,1]), (tri[:,1],tri[:,2]), (tri[:,2],tri[:,0])]:
        da, db = a[:,2]-z, b[:,2]-z
        points.extend(a[np.abs(da)<=tolerance,:2])
        points.extend(b[np.abs(db)<=tolerance,:2])
        crossing = (da*db < 0) & (np.abs(da)>tolerance) & (np.abs(db)>tolerance)
        if crossing.any():
            t = da[crossing]/(da[crossing]-db[crossing])
            points.extend((a[crossing]+t[:,None]*(b[crossing]-a[crossing]))[:,:2])
    return np.unique(np.asarray(points).reshape(-1,2).round(12),axis=0)


def gravity_projection_margin(point_xy, support_points_xy):
    """Signed Euclidean distance to the convex reaction footprint; positive inside."""
    point = np.asarray(point_xy, float)
    points = np.unique(np.asarray(support_points_xy, float).reshape(-1,2),axis=0)
    if point.shape!=(2,) or not np.isfinite(point).all() or not np.isfinite(points).all():
        raise ValueError('finite 2D points required')
    if not len(points):
        return dict(rank=-1,point_count=0,area_m2=0.,signed_margin_m=None,inside=False,footprint_vertices_xy_m=[])
    if len(points)==1:
        return dict(rank=0,point_count=1,area_m2=0.,signed_margin_m=-float(np.linalg.norm(point-points[0])),inside=False,footprint_vertices_xy_m=points.tolist())
    singular=np.linalg.svd(points-points.mean(0),compute_uv=False)
    if singular[-1] <= 1e-10:
        _,_,axes=np.linalg.svd(points-points.mean(0),full_matrices=False)
        order=points@axes[0];vertices=points[[np.argmin(order),np.argmax(order)]]
        a,b=vertices;v=b-a;t=np.clip(np.dot(point-a,v)/np.dot(v,v),0,1)
        return dict(rank=1,point_count=len(points),area_m2=0.,signed_margin_m=-float(np.linalg.norm(point-a-t*v)),inside=False,footprint_vertices_xy_m=vertices.tolist())
    hull=ConvexHull(points);vertices=points[hull.vertices];a=vertices;b=np.roll(vertices,-1,axis=0);v=b-a
    t=np.clip(np.einsum('ij,ij->i',point-a,v)/np.einsum('ij,ij->i',v,v),0,1)
    distance=float(np.linalg.norm(point-a-t[:,None]*v,axis=1).min())
    inside=bool(np.max(hull.equations[:,:2]@point+hull.equations[:,2])<=1e-12)
    return dict(rank=2,point_count=len(points),area_m2=float(hull.volume),signed_margin_m=distance if inside else -distance,
                inside=inside,footprint_vertices_xy_m=vertices.tolist())
