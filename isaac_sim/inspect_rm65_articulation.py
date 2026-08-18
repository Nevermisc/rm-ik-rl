from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import omni.usd
from isaacsim.core.utils import prims
from pxr import UsdPhysics, PhysxSchema

RM65_STAGE_PATH = "/RM65"
RM65_USD_PATH = "/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd"

prims.create_prim(
    RM65_STAGE_PATH,
    "Xform",
    usd_path=RM65_USD_PATH,
)

simulation_app.update()

stage = omni.usd.get_context().get_stage()

print("=== All prims with articulation / rigid body / joint related schemas ===")

for prim in stage.Traverse():
    path = str(prim.GetPath())
    type_name = prim.GetTypeName()
    applied_schemas = list(prim.GetAppliedSchemas())

    has_articulation = prim.HasAPI(UsdPhysics.ArticulationRootAPI)
    has_rigid_body = prim.HasAPI(UsdPhysics.RigidBodyAPI)
    has_collision = prim.HasAPI(UsdPhysics.CollisionAPI)

    schema_text = " ".join(applied_schemas)
    looks_relevant = (
        has_articulation
        or has_rigid_body
        or has_collision
        or "Articulation" in schema_text
        or "RigidBody" in schema_text
        or "Joint" in type_name
        or "joint" in path.lower()
    )

    if looks_relevant:
        print(f"path: {path}")
        print(f"  type: {type_name}")
        print(f"  applied_schemas: {applied_schemas}")
        print(f"  has ArticulationRootAPI: {has_articulation}")
        print(f"  has RigidBodyAPI: {has_rigid_body}")
        print(f"  has CollisionAPI: {has_collision}")
        print()

simulation_app.close()
