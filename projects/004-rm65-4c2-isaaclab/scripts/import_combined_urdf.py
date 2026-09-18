#!/usr/bin/env python3
"""Import the generated RM65 + 4C2 URDF into a standalone USD file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--urdf", type=Path, required=True)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--report", type=Path)
parser.add_argument(
    "--parse-mimic",
    action="store_true",
    help="Preserve URDF mimic constraints. The default imports independent follower DOFs for stable software coupling.",
)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import omni.kit.commands  # noqa: E402
import omni.kit.app  # noqa: E402
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402
from pxr import Usd, UsdPhysics  # noqa: E402


def main() -> None:
    urdf = args.urdf.expanduser().resolve()
    usd = args.usd.expanduser().resolve()
    if not urdf.is_file():
        raise FileNotFoundError(urdf)
    usd.parent.mkdir(parents=True, exist_ok=True)

    enable_extension("isaacsim.asset.importer.urdf")
    simulation_app.update()

    status, config = omni.kit.commands.execute("URDFCreateImportConfig")
    if not status:
        raise RuntimeError("URDFCreateImportConfig failed")
    config.fix_base = True
    config.merge_fixed_joints = True
    config.make_default_prim = True
    config.create_physics_scene = False
    config.import_inertia_tensor = True
    config.self_collision = False
    config.parse_mimic = args.parse_mimic

    status, imported_path = omni.kit.commands.execute(
        "URDFParseAndImportFile",
        urdf_path=str(urdf),
        import_config=config,
        dest_path=str(usd),
    )
    if not status:
        raise RuntimeError("URDFParseAndImportFile failed")
    simulation_app.update()

    stage = Usd.Stage.Open(str(usd))
    if stage is None:
        raise RuntimeError(f"could not open generated USD: {usd}")
    joints = [prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Joint)]
    articulation_roots = [prim for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
    report = {
        "status": "pass",
        "urdf": str(urdf),
        "usd": str(usd),
        "imported_path": str(imported_path),
        "usd_joint_count": len(joints),
        "parse_mimic": args.parse_mimic,
        "gripper_coupling": "physx_mimic" if args.parse_mimic else "software_coupled_joint_targets",
        "articulation_roots": [str(prim.GetPath()) for prim in articulation_roots],
    }
    if args.report:
        report_path = args.report.expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


try:
    main()
finally:
    simulation_app.close(skip_cleanup=True)
