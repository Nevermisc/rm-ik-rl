"""Compare recorded USD joint constraints with URDF at multiple joint angles.

Consumes a hash-bound read-only USD audit, not an active simulation. It does
not assert collision-free motion, dynamics, closed-loop closure, or calibration.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from household_grasp_calibration import origin_transform, rotation


def pose(position, quaternion, units=1.):
    xyz = np.asarray(ast.literal_eval(position), dtype=float)
    q = np.asarray(ast.literal_eval(quaternion), dtype=float)
    if xyz.shape != (3,) or q.shape != (4,) or not np.isfinite(np.r_[xyz, q]).all() or np.linalg.norm(q) < 1e-9:
        raise ValueError('invalid USD joint pose')
    w, x, y, z = q / np.linalg.norm(q)
    result = np.eye(4)
    result[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    result[:3, 3] = xyz * units
    return result


def compare_joint(source, usd, units):
    attrs, rels = usd['attributes'], usd['relationships']
    checks = {}
    for index, tag in enumerate(('parent', 'child')):
        targets = rels.get(f'physics:body{index}', [])
        checks[tag + '_link'] = len(targets) == 1 and targets[0].rsplit('/', 1)[-1] == source.find(tag).get('link')
    fixed = source.get('type') == 'fixed'
    checks['type'] = usd['type'] == ('PhysicsFixedJoint' if fixed else 'PhysicsRevoluteJoint')
    if not fixed and source.get('type') != 'revolute':
        raise ValueError('unsupported source joint type')
    qs = [0.]
    limits = None
    if not fixed:
        lower, upper = [float(source.find('limit').get(k)) for k in ('lower', 'upper')]
        qs += list(np.linspace(lower, upper, 5))
        imported_limits = np.deg2rad([float(attrs['physics:lowerLimit']), float(attrs['physics:upperLimit'])])
        checks['limits'] = bool(np.allclose([lower, upper], imported_limits, atol=1e-6, rtol=0))
        limits = dict(source_rad=[lower, upper], imported_rad=imported_limits.tolist(),
                      strict_equality=checks['limits'])
    t0 = pose(attrs['physics:localPos0'], attrs['physics:localRot0'], units)
    t1 = pose(attrs['physics:localPos1'], attrs['physics:localRot1'], units)
    source_frame = origin_transform(source.find('origin'))
    position_errors, rotation_errors = [], []
    for q in qs:
        motion, usd_motion = np.eye(4), np.eye(4)
        if not fixed:
            motion[:3, :3] = rotation(np.fromstring(source.find('axis').get('xyz'), sep=' '), q)
            usd_motion[:3, :3] = rotation(np.eye(3)['XYZ'.index(attrs['physics:axis'])], q)
        expected, actual = source_frame @ motion, t0 @ usd_motion @ np.linalg.inv(t1)
        position_errors.append(float(np.linalg.norm(expected[:3, 3] - actual[:3, 3])))
        rotation_errors.append(float(np.max(np.abs(expected[:3, :3] - actual[:3, :3]))))
    checks['position_frames'] = max(position_errors) < 2e-6
    checks['rotation_axis_and_direction'] = max(rotation_errors) < 1e-5
    return dict(name=source.get('name'), status='pass' if all(checks.values()) else 'fail',
                checks=checks, limits=limits, sample_q_rad=qs, max_position_error_m=max(position_errors),
                max_rotation_matrix_abs_error=max(rotation_errors))


def expected_joints(source, arm_only):
    # A flange mount need not contain 'mount' in its name (rm65_to_4c2 does not).
    # Select by actual parent/child identity instead of a naming heuristic.
    return {n: j for n, j in source.items() if not arm_only or all(
        not j.find(tag).get('link').startswith('tool_') for tag in ('parent', 'child'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--urdf', type=Path, required=True)
    parser.add_argument('--usd-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('fresh report required')
    data = json.loads(args.usd_audit.read_text())
    source_hash = hashlib.sha256(args.urdf.read_bytes()).hexdigest()
    if data['source_combined_urdf_sha256'] != source_hash:
        raise ValueError('URDF does not match the USD source audit')
    source = {j.get('name'): j for j in ET.parse(args.urdf).getroot().findall('joint')}
    records = []
    for asset in data['assets']:
        joints = {j['path'].rsplit('/', 1)[-1]: j for j in asset['joints']}
        # Standalone arm has no gripper; distinguish intentionally absent parts.
        arm_only = not any(name.startswith('tool_') for name in joints)
        expected = expected_joints(source, arm_only)
        checked = [compare_joint(j, joints[n], asset['meters_per_unit']) for n, j in expected.items() if n in joints]
        missing = sorted(set(expected) - set(joints))
        records.append(dict(path=asset['path'], usd_sha256=asset['sha256'], arm_only=arm_only,
                            missing_joints=missing, joints=checked,
                            status='pass' if not missing and checked and all(c['status']=='pass' for c in checked) else 'fail'))
    result = dict(schema='rm65_imported_joint_frame_audit_v1', read_only=True, physics_steps=0,
                  urdf_sha256=source_hash, usd_audit_sha256=hashlib.sha256(args.usd_audit.read_bytes()).hexdigest(),
                  assets=records, limitations=['Independent relative joint transforms at sampled angles, not runtime motion.',
                  'Mimic dynamics, self-collision, cooked shapes and real hardware remain separate gates.'])
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps([dict(path=r['path'], status=r['status'], missing=r['missing_joints'],
                          failed=[dict(name=j['name'], checks=j['checks'], limits=j['limits'])
                                  for j in r['joints'] if j['status']!='pass']) for r in records], indent=2))


if __name__ == '__main__':
    main()
