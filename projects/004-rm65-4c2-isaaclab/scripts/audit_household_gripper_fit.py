"""Conservative axis-aligned width screen; not a grasp feasibility proof."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.household_assets import manifest_object_ids, load_household
from household_grasp_calibration import PadGeometry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--gripper-urdf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('use a new output path')
    geometry = PadGeometry(args.gripper_urdf)
    gaps = [geometry.pads(float(q))[2] for q in np.linspace(0, .8, 401)]
    cases = []
    for object_id in manifest_object_ids(args.manifest):
        spec = load_household(args.manifest, object_id)
        cases.append(dict(object_id=object_id, size_m=spec.size_m,
            current_y_width_within_modeled_aperture=min(gaps) <= spec.size_m[1] <= max(gaps),
            axes_with_width_in_aperture=[a for a, width in zip('xyz', spec.size_m)
                                        if min(gaps) <= width <= max(gaps)],
            interpretation='Bounding-box screen only; handles, local cross-sections, pose and table clearance need separate analysis.',
            grasp_feasibility_validated=False))
    report = dict(simulation_only=True, development_only=True, min_gap_m=min(gaps), max_gap_m=max(gaps),
                  q_range_rad=[0, .8], cases=cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
