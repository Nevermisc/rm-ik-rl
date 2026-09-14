from pathlib import Path
import json
import os

from isaaclab.app import AppLauncher


app_launcher = AppLauncher(headless=True)
simulation_app = app_launcher.app

from pxr import Usd, UsdPhysics


sim_evals_dir = Path(
    os.environ.get("SIM_EVALS_DIR", Path.home() / "robot-learning" / "sim-evals")
)
root = sim_evals_dir / "assets"
result = {}
for scene_id in (1, 2, 3):
    print(f"SCENE {scene_id}", flush=True)
    stage = Usd.Stage.Open(str(root / f"scene{scene_id}.usd"))
    result[str(scene_id)] = []
    for prim in stage.GetPrimAtPath("/World").GetChildren():
        position = prim.GetAttribute("xformOp:translate").Get()
        print(
            prim.GetName(),
            prim.GetTypeName(),
            bool(UsdPhysics.RigidBodyAPI(prim)),
            prim.GetAttribute("xformOp:translate").Get(),
            flush=True,
        )
        result[str(scene_id)].append(
            {
                "name": prim.GetName(),
                "type": prim.GetTypeName(),
                "rigid": bool(UsdPhysics.RigidBodyAPI(prim)),
                "position": list(position) if position is not None else None,
            }
        )

Path("/tmp/droid_scene_prims.json").write_text(json.dumps(result, indent=2))

simulation_app.close()
