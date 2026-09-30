"""Object-neutral placement geometry; rotation changes pose, never asset scale."""
import math


def yaw_placement(size_m, yaw_rad):
    if len(size_m) != 3 or any(not math.isfinite(v) or v <= 0 for v in size_m):
        raise ValueError('three positive finite dimensions required')
    if not math.isfinite(yaw_rad) or abs(yaw_rad) > math.pi:
        raise ValueError('object yaw must be finite and within +/-pi')
    x, y, z = size_m
    c, s = abs(math.cos(yaw_rad)), abs(math.sin(yaw_rad))
    return dict(world_aabb_size_m=[c*x+s*y, s*x+c*y, z],
                orientation_wxyz=[math.cos(yaw_rad/2), 0., 0., math.sin(yaw_rad/2)],
                asset_scale=[1.,1.,1.], object_yaw_rad=yaw_rad,
                grasp_feasibility_validated=False)
