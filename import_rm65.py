"""Import the project-local RM65-B URDF as an Isaac Sim USD asset.

Run with Isaac Sim's bundled Python:
    ~/isaac-sim/python.sh import_rm65.py
"""

from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": True})

import omni.kit.commands


project_dir = Path(__file__).resolve().parent
urdf_path = project_dir / "assets" / "RM65-B" / "urdf" / "RM65-B.urdf"
usd_path = project_dir / "assets" / "RM65-B" / "RM65-B.usd"


def main() -> int:
    print(f"[RM65] URDF source: {urdf_path}")
    print(f"[RM65] USD output:  {usd_path}")

    if not urdf_path.is_file():
        print("[RESULT] FAIL: RM65-B URDF was not found.")
        return 1

    status, import_config = omni.kit.commands.execute("URDFCreateImportConfig")
    if not status:
        print("[RESULT] FAIL: Isaac Sim could not create a URDF import configuration.")
        return 1

    # Keep the six revolute joints, use the URDF inertia data, and anchor the base.
    import_config.merge_fixed_joints = False
    import_config.convex_decomp = False
    import_config.import_inertia_tensor = True
    import_config.fix_base = True
    import_config.distance_scale = 1.0
    import_config.make_default_prim = True
    import_config.create_physics_scene = True

    status, articulation_root = omni.kit.commands.execute(
        "URDFParseAndImportFile",
        urdf_path=str(urdf_path),
        import_config=import_config,
        dest_path=str(usd_path),
        get_articulation_root=True,
    )

    if not status or not usd_path.is_file():
        print(f"[RM65] Import command status: {status}")
        print(f"[RM65] Returned articulation root: {articulation_root}")
        print("[RESULT] FAIL: RM65-B USD was not generated.")
        return 1

    print(f"[RM65] Articulation root: {articulation_root}")
    print(f"[RM65] Generated file size: {usd_path.stat().st_size} bytes")
    print("[RESULT] PASS: RM65-B URDF was imported as USD.")
    return 0


try:
    exit_code = main()
finally:
    simulation_app.close()

raise SystemExit(exit_code)
