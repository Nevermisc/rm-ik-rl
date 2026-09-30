"""Read the installed Isaac asset catalog; never treats availability as grasp success."""
import argparse
import json
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output.exists():
    parser.error('use a new output path')
launcher = AppLauncher(args)
import omni.client
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

try:
    inventory = []
    for family in ['Axis_Aligned_Physics', 'Axis_Aligned']:
        root = f'{ISAAC_NUCLEUS_DIR}/Props/YCB/{family}'
        result, entries = omni.client.list(root)
        item = dict(root=root, result=str(result), entries=[e.relative_path for e in entries])
        inventory.append(item)
        print(json.dumps(item), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(dict(simulation_only=True, inventory=inventory), stream, indent=2)
finally:
    launcher.app.close(skip_cleanup=True)
