"""Predict contact-pad/table clearance along closure; not whole-hand collision planning."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from household_grasp_calibration import PadGeometry, origin_transform
from grasp_geometry import compute_top_down_link_pose
from openpi_extension.household_assets import load_household
from openpi_extension.object_placement import yaw_placement


def scan(geometry, width, height, height_offset=0., max_q=.8):
    if not np.isfinite(height) or height <= 0 or not np.isfinite(height_offset):
        raise ValueError('invalid object height or contact offset')
    center, closing, fit = geometry.fit_box(width, max_q)
    position, rotation, _ = compute_top_down_link_pose(-center, np.eye(3), np.zeros(3), 0,
                                                     reference_closing_axis_world=closing)
    states = []
    for q in np.linspace(0, max_q, 101):
        pads = {}
        for name in ('tool_r_2', 'tool_l_2'):
            collision = geometry.links[name].find("collision[@name='contact_pad_box']")
            size = np.fromstring(collision.find('geometry/box').get('size'), sep=' ')
            frame = geometry.transform(name, float(q)) @ origin_transform(collision.find('origin'))
            corners = np.array(list(product((-1,1), repeat=3))) * size / 2
            world = corners @ (rotation @ frame[:3,:3]).T + position + rotation @ frame[:3,3]
            pads[name] = dict(min_z_above_table_m=float(world[:,2].min()+height/2+height_offset),
                              max_z_above_table_m=float(world[:,2].max()+height/2+height_offset))
        states.append(dict(q_rad=float(q), aperture_m=geometry.pads(float(q))[2], pads=pads))
    return dict(fit=fit, object_height_m=height, grasp_height_offset_m=height_offset, states=states,
                whole_hand_collision_checked=False, contact_feasibility_proven=False)


def require_pad_table_clearance(result, margin_m=.002):
    values = [p['min_z_above_table_m'] for s in result['states'] for p in s['pads'].values()]
    minimum = min(values)
    if not all(np.isfinite(v) for v in values) or minimum < margin_m:
        raise ValueError(f'predicted pad/table clearance {minimum:.6f} m is below {margin_m:.6f} m; choose a physically reachable contact height')
    return dict(minimum_modeled_pad_clearance_m=minimum, required_margin_m=margin_m,
                whole_hand_collision_checked=False, contact_feasibility_proven=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--object-id', required=True)
    parser.add_argument('--object-yaw-rad', type=float, default=0.)
    parser.add_argument('--gripper-urdf', type=Path, required=True)
    parser.add_argument('--height-offset-m', type=float, default=0.)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spec = load_household(args.manifest, args.object_id)
    placed = yaw_placement(spec.size_m, args.object_yaw_rad)
    result = scan(PadGeometry(args.gripper_urdf), placed['world_aabb_size_m'][1], spec.size_m[2], args.height_offset_m)
    result.update(object_id=args.object_id, placement=placed, simulation_only=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({**{k:v for k,v in result.items() if k != 'states'},
                      'selected_states': [r for r in result['states'] if round(r['q_rad'],2) in (0.,.6,.65,.7,.75,.78,.8)]}, indent=2))


if __name__ == '__main__':
    main()
