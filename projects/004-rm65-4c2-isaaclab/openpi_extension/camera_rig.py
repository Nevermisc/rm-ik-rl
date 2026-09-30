"""Fixed simulation camera geometry; no object pose or task target input."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np


def vector3(value, name):
    vector = np.asarray(value, dtype=np.float64)
    if vector.shape != (3,) or not np.isfinite(vector).all():
        raise ValueError(f'{name} must have three finite coordinates')
    return vector


def camera_rotation(forward, up):
    """OpenGL camera-to-parent rotation: columns right, up, backward."""
    forward = vector3(forward, 'forward')
    up = vector3(up, 'up')
    if np.linalg.norm(forward) < 1e-8 or np.linalg.norm(up) < 1e-8:
        raise ValueError('camera directions must be nonzero')
    forward = forward / np.linalg.norm(forward)
    up = up / np.linalg.norm(up)
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        raise ValueError('camera up and forward must not be parallel')
    right /= np.linalg.norm(right)
    return np.column_stack((right, np.cross(right, forward), -forward))


def load_camera_rig(path: Path):
    raw = path.read_bytes()
    rig = json.loads(raw)
    if rig.get('schema') != 'rm65_fixed_camera_rig_v1' or not rig.get('rig_id'):
        raise ValueError('unsupported or unnamed fixed camera rig')
    if rig.get('simulation_only') is not True or rig.get('hardware_calibrated') is not False:
        raise ValueError('this rig is simulation-only, not hardware calibrated')
    external, wrist, optics = rig['external'], rig['wrist'], rig['optics']
    eye = vector3(external['eye_world_m'], 'external eye')
    target = vector3(external['target_world_m'], 'external target')
    camera_rotation(target - eye, [0., 0., 1.])
    if wrist['parent_link'] not in ('link_6', 'tool_base_link'):
        raise ValueError('unreviewed wrist camera parent')
    offset = vector3(wrist['offset_local_m'], 'wrist offset')
    if np.linalg.norm(offset) > .3:
        raise ValueError('wrist offset exceeds 0.3 m development limit')
    camera_rotation(wrist['forward_local'], wrist['up_local'])
    for key in ('width', 'height'):
        if type(optics[key]) is not int or not 64 <= optics[key] <= 2048:
            raise ValueError('invalid image dimensions')
    for key in ('external_focal_length_mm', 'wrist_focal_length_mm', 'horizontal_aperture_mm'):
        if not np.isfinite(optics[key]) or optics[key] <= 0:
            raise ValueError('invalid camera optics')
    clip = np.asarray(optics['clipping_range_m'], dtype=float)
    if clip.shape != (2,) or not np.isfinite(clip).all() or not 0 < clip[0] < clip[1]:
        raise ValueError('invalid clipping range')
    return {'mode': 'fixed_mount', 'uses_object_pose_for_camera_initialization': False,
            'uses_task_target_for_camera_initialization': False,
            'config_sha256': hashlib.sha256(raw).hexdigest(), 'config': rig}
