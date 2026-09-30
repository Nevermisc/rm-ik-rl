"""Development-only pad geometry from the exact simulated gripper URDF.

This estimates an initial box grasp, not collision-free planning or perception.
No meshes, hardware, network, or simulation are loaded by this module.
"""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np


def require_legacy_pad_diagnostic_opt_in(uses_legacy_pad_calibration, explicitly_allowed):
    if uses_legacy_pad_calibration and not explicitly_allowed:
        raise ValueError('Legacy block-derived pads are detached from visible fingers; '
                         'household collection is blocked. Use --allow-legacy-detached-pad-diagnostic '
                         'only for explicit simulation diagnosis, never as native-gripper validation.')


def rotation(axis, angle):
    axis = np.asarray(axis, dtype=float)
    norm = np.linalg.norm(axis)
    if norm < 1e-9:
        raise ValueError("zero joint axis")
    x, y, z = axis / norm
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + np.sin(angle) * skew + (1 - np.cos(angle)) * skew @ skew


def origin_transform(element):
    result = np.eye(4)
    if element is None:
        return result
    result[:3, 3] = np.fromstring(element.get("xyz", "0 0 0"), sep=" ")
    r, p, y = np.fromstring(element.get("rpy", "0 0 0"), sep=" ")
    result[:3, :3] = rotation([0, 0, 1], y) @ rotation([0, 1, 0], p) @ rotation([1, 0, 0], r)
    return result


class PadGeometry:
    def __init__(self, urdf):
        self.path = Path(urdf)
        root = ET.parse(self.path).getroot()
        self.links = {link.get("name"): link for link in root.findall("link")}
        self.joints = {j.find("child").get("link"): j for j in root.findall("joint")}

    def transform(self, child, q, visited=None):
        if child == "link_6":
            return np.eye(4)
        visited = set() if visited is None else visited
        if child in visited or child not in self.joints:
            raise ValueError("pad chain must terminate at link_6")
        visited.add(child)
        joint = self.joints[child]
        transform = origin_transform(joint.find("origin"))
        kind = joint.get("type")
        if kind == "revolute":
            limit = joint.find("limit")
            if not float(limit.get("lower")) <= q <= float(limit.get("upper")):
                raise ValueError("calibration q outside URDF joint limits")
            motion = np.eye(4)
            motion[:3, :3] = rotation(np.fromstring(joint.find("axis").get("xyz"), sep=" "), q)
            transform = transform @ motion
        elif kind != "fixed":
            raise ValueError("unsupported pad-chain joint type")
        return self.transform(joint.find("parent").get("link"), q, visited) @ transform

    def pads(self, q):
        centers, rotations, sizes = [], [], []
        for name in ("tool_r_2", "tool_l_2"):
            collision = self.links[name].find("collision[@name='contact_pad_box']")
            if collision is None:
                raise ValueError("missing contact_pad_box")
            frame = self.transform(name, q) @ origin_transform(collision.find("origin"))
            centers.append(frame[:3, 3])
            rotations.append(frame[:3, :3])
            sizes.append(np.fromstring(collision.find("geometry/box").get("size"), sep=" "))
        closing = centers[1] - centers[0]
        separation = np.linalg.norm(closing)
        if separation < 1e-9:
            raise ValueError("coincident pads")
        closing /= separation
        half_thickness = [np.abs(closing @ r) @ s / 2 for r, s in zip(rotations, sizes)]
        gap = float(separation - sum(half_thickness))
        return (centers[0] + centers[1]) / 2, closing, gap

    def fit_box(self, width_m, max_q=.8):
        if not np.isfinite(width_m) or width_m <= 0 or not 0 < max_q <= 1:
            raise ValueError("invalid width or q")
        candidates = [(q, *self.pads(q)) for q in np.linspace(0, max_q, 401)]
        gaps = [item[3] for item in candidates]
        if not min(gaps) <= width_m <= max(gaps):
            raise ValueError("object width outside modeled pad aperture")
        q, center, closing, gap = min(candidates, key=lambda item: abs(item[3] - width_m))
        return center, closing, {
            "mode": "urdf_contact_pad_box_development_only",
            "urdf_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "predicted_contact_q_rad": float(q), "modeled_gap_m": gap,
            "requested_width_m": float(width_m), "pad_midpoint_link6_m": center.tolist(),
            "closing_axis_link6": closing.tolist(),
            "perception_used": False, "collision_free_path_validated": False,
        }

    def preshape_evidence(self, q, close_q, width_m, margin_m=.004):
        if not np.isfinite(q) or not 0 < q < close_q <= 1:
            raise ValueError('preshape must be positive and below the close target')
        gap = self.pads(q)[2]
        if not np.isfinite(width_m) or width_m <= 0 or gap < width_m + margin_m:
            raise ValueError('preshape leaves insufficient object clearance')
        return dict(target_rad=q, modeled_aperture_m=gap, object_width_m=width_m,
                    minimum_extra_aperture_m=margin_m, whole_hand_collision_checked=False)
