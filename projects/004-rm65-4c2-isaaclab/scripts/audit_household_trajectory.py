"""Object-aware temporal checks on immutable recordings; never grants training admission."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def rotated_half_extents(size, quat):
    q = np.asarray(quat, dtype=float)
    norm = np.linalg.norm(q)
    if q.shape != (4,) or not np.isfinite(q).all() or abs(norm-1.) > .01:
        raise ValueError('invalid object quaternion')
    w,x,y,z = q/norm
    rotation = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                         [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                         [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    return np.abs(rotation) @ (np.asarray(size)/2)


def analyze(poses, actions, phases, report, object_size):
    poses, actions, phases = np.asarray(poses), np.asarray(actions), np.asarray(phases)
    if poses.shape != (len(phases),7) or actions.shape != (len(phases),7) or not len(phases):
        raise ValueError('frame/shape mismatch')
    if not np.isfinite(poses).all() or not np.isfinite(actions).all():
        raise ValueError('non-finite trajectory')
    if np.any((actions[:,6] < 0) | (actions[:,6] > 1)):
        raise ValueError('gripper commands must be normalized to [0, 1]')
    object_size = np.asarray(object_size, dtype=float)
    if object_size.shape != (3,) or not np.isfinite(object_size).all() or np.any(object_size <= 0):
        raise ValueError('invalid object size')
    joints = np.asarray(report['final_gripper_joint_position_rad'], dtype=float)
    if joints.shape != (6,) or not np.isfinite(joints).all():
        raise ValueError('six finite final gripper positions required')
    required = ('SOURCE_SETTLE', 'LIFT_HOLD', 'TRANSFER', 'OPEN', 'RELEASE_SETTLE', 'FINAL_SETTLE')
    missing = [name for name in required if not np.any(phases == name)]
    result = dict(evaluation_scope='household_temporal_development_only', training_ready=False,
                  formal_acceptance_passed=False, missing_phases=missing)
    if missing:
        return dict(result, candidate_checks_passed=False, reason='incomplete task recording')
    indices = [np.flatnonzero(phases == name) for name in required]
    phase_order_valid = all(left[-1] < right[0] for left, right in zip(indices, indices[1:]))
    source_z = float(np.median(poses[phases == 'SOURCE_SETTLE'][-5:,2]))
    carry = poses[np.isin(phases, ('LIFT_HOLD','TRANSFER')),:3]
    final = poses[phases == 'FINAL_SETTLE']
    release = poses[phases == 'RELEASE_SETTLE']
    platform_center = np.asarray(report['target_platform_position_m'])
    platform_size = np.asarray(report['target_platform_size_m'])
    if (platform_center.shape != (3,) or platform_size.shape != (3,)
            or not np.isfinite(platform_center).all() or not np.isfinite(platform_size).all()
            or np.any(platform_size <= 0)):
        raise ValueError('invalid support geometry')
    if report.get('target_support_mode') != 'wide_platform':
        raise ValueError('only axis-aligned wide-platform geometry is reviewed')
    extents = np.array([rotated_half_extents(object_size, p[3:]) for p in final])
    support_top = float(platform_center[2]+platform_size[2]/2)
    min_xy_margin = float(np.min(platform_size[:2]/2 - np.abs(final[:,:2]-platform_center[:2]) - extents[:,:2]))
    bottom_error = final[:,2]-extents[:,2]-support_top
    carry_min_height = float(carry[:,2].min()-source_z)
    carry_vertical_range = float(np.ptp(carry[:,2]))
    release_drift = float(np.linalg.norm(final[-1,:3]-release[-1,:3]))
    end_open_command = float(actions[phases == 'OPEN'][-1,6])
    checks = dict(
        required_phases_in_order=phase_order_valid,
        recorded_task_passed=report.get('status') == 'pass',
        strict_initial_gravity=report.get('physics_contract',{}).get('initial',{}).get('validation',{}).get('status') == 'pass',
        strict_final_gravity=report.get('physics_contract',{}).get('final',{}).get('validation',{}).get('status') == 'pass',
        continuously_elevated_during_carry=carry_min_height > .02,
        no_large_vertical_drop_during_carry=carry_vertical_range < .015,
        release_command_fully_open=end_open_command < .02,
        final_joint_feedback_open=bool(np.all(np.abs(joints) < .12)),
        final_footprint_within_support=min_xy_margin >= .005,
        final_bottom_near_support=bool(np.all((bottom_error >= -.003) & (bottom_error <= .008))),
        stable_after_release=release_drift < .01,
    )
    return dict(result, candidate_checks_passed=all(checks.values()), checks=checks,
                carry_min_height_above_source_m=carry_min_height, carry_vertical_range_m=carry_vertical_range,
                final_footprint_min_margin_m=min_xy_margin, final_bottom_error_range_m=[float(bottom_error.min()),float(bottom_error.max())],
                release_drift_m=release_drift, last_open_command_normalized=end_open_command,
                limitations=['Object AABB/support screen is conservative, not contact-mesh proof.',
                             'Does not validate whole-hand collisions, force calibration or unseen-object generalization.',
                             'Even a passing development candidate cannot automatically enter training.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('episode', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.episode/'metadata.json').read_text())
    report = json.loads((args.episode/'task_report.json').read_text())
    with np.load(args.episode/'episode.npz') as data:
        phases = [manifest['phase_names'][int(i)] for i in data['phase_id']]
        result = analyze(data['cube_pose_wxyz'], data['action'], phases, report,
                         manifest['metadata']['object_probe']['size_m'])
    result.update(episode=str(args.episode), simulation_only=True,
                  sources_sha256={name:hashlib.sha256((args.episode/name).read_bytes()).hexdigest()
                                  for name in ('metadata.json','task_report.json','episode.npz')})
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
