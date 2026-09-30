"""Read authored drive modes before deciding how to interpret PD gains."""
import argparse
import json
from pathlib import Path
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--usd', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.output.exists():
    parser.error('new output required')
launcher = AppLauncher(args)
from pxr import Usd, UsdPhysics
try:
    stage = Usd.Stage.Open(str(args.usd.resolve()))
    joints = []
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.Joint) and prim.GetName().startswith('tool_'):
            drive = UsdPhysics.DriveAPI.Get(prim, 'angular')
            joints.append(dict(path=str(prim.GetPath()), valid_drive=bool(drive),
                drive_type=str(drive.GetTypeAttr().Get()) if drive else None,
                stiffness=drive.GetStiffnessAttr().Get() if drive else None,
                damping=drive.GetDampingAttr().Get() if drive else None,
                max_force=drive.GetMaxForceAttr().Get() if drive else None))
    with args.output.open('x') as stream:
        json.dump(dict(simulation_only=True, usd=str(args.usd), joints=joints), stream, indent=2)
    print(json.dumps(joints, indent=2))
finally:
    launcher.app.close(skip_cleanup=True)
