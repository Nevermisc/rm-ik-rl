from isaacsim import SimulationApp

import os

HEADLESS = os.environ.get("ISAAC_HEADLESS", "0") == "1"
MAX_STEPS = int(os.environ.get("ISAAC_MAX_STEPS", "900"))

simulation_app = SimulationApp({"renderer": "RaytracedLighting", "headless": HEADLESS})

import numpy as np
from isaacsim.core.api import SimulationContext
from isaacsim.core.api.materials.physics_material import PhysicsMaterial
from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
from isaacsim.core.utils import viewports
from pxr import UsdPhysics


TABLE_HEIGHT = 0.0
CUBE_SIZE = 0.045
CUBE_INITIAL_Z = TABLE_HEIGHT + CUBE_SIZE / 2.0 + 0.002

LEFT_FINGER_PATH = "/World/FunctionalGripper/left_finger"
RIGHT_FINGER_PATH = "/World/FunctionalGripper/right_finger"
CUBE_PATH = "/World/target_cube"


def make_kinematic(rigid_object):
    prim = rigid_object.prim
    rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(prim)
    rigid_body_api.CreateKinematicEnabledAttr().Set(True)


def set_object_position(obj, position):
    obj.set_world_pose(position=np.array(position, dtype=np.float64))


def get_object_position(obj):
    position, _ = obj.get_world_pose()
    return np.array(position)


def phase_targets(step):
    """Return left_y, right_y, finger_z for a simple close-and-lift grasp test."""
    open_y = 0.085
    # Close slightly into the cube's side faces so contact is guaranteed.
    closed_y = 0.022
    # Put the fingers lower so their contact area overlaps the cube body.
    base_z = TABLE_HEIGHT + 0.060
    lift_z = TABLE_HEIGHT + 0.190

    if step < 180:
        # Settle phase: keep the gripper open and let the cube rest on the table.
        alpha = 0.0
        z = base_z
    elif step < 360:
        # Close phase: move both fingers inward.
        alpha = (step - 180) / 180.0
        z = base_z
    elif step < 660:
        # Lift phase: keep fingers closed and lift them upward.
        alpha = 1.0
        lift_alpha = (step - 360) / 300.0
        z = base_z + (lift_z - base_z) * lift_alpha
    else:
        # Hold phase: keep the object lifted if the grasp worked.
        alpha = 1.0
        z = lift_z

    y = open_y + (closed_y - open_y) * alpha
    return y, -y, z


simulation_context = SimulationContext(stage_units_in_meters=1.0)

viewports.set_camera_view(
    eye=np.array([0.45, 0.55, 0.35]),
    target=np.array([0.0, 0.0, 0.08]),
)

grip_material = PhysicsMaterial(
    prim_path="/World/PhysicsMaterials/high_friction_grip",
    static_friction=4.0,
    dynamic_friction=3.0,
    restitution=0.0,
)

cube_material = PhysicsMaterial(
    prim_path="/World/PhysicsMaterials/cube_material",
    static_friction=2.0,
    dynamic_friction=2.0,
    restitution=0.0,
)

table = FixedCuboid(
    prim_path="/World/table",
    name="table",
    position=np.array([0.0, 0.0, TABLE_HEIGHT - 0.012]),
    scale=np.array([0.50, 0.50, 0.024]),
    color=np.array([0.45, 0.45, 0.45]),
    physics_material=grip_material,
)

target_cube = DynamicCuboid(
    prim_path=CUBE_PATH,
    name="target_cube",
    position=np.array([0.0, 0.0, CUBE_INITIAL_Z]),
    scale=np.array([CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]),
    color=np.array([0.9, 0.25, 0.15]),
    mass=0.035,
    physics_material=cube_material,
)

left_finger = DynamicCuboid(
    prim_path=LEFT_FINGER_PATH,
    name="left_finger",
    position=np.array([0.0, 0.085, TABLE_HEIGHT + 0.080]),
    scale=np.array([0.035, 0.018, 0.115]),
    color=np.array([0.02, 0.02, 0.02]),
    mass=1.0,
    physics_material=grip_material,
)

right_finger = DynamicCuboid(
    prim_path=RIGHT_FINGER_PATH,
    name="right_finger",
    position=np.array([0.0, -0.085, TABLE_HEIGHT + 0.080]),
    scale=np.array([0.035, 0.018, 0.115]),
    color=np.array([0.02, 0.02, 0.02]),
    mass=1.0,
    physics_material=grip_material,
)

make_kinematic(left_finger)
make_kinematic(right_finger)

simulation_context.initialize_physics()
simulation_context.play()

print("Simple gripper grasp physics test started.", flush=True)
print("Goal: close two kinematic collision fingers around a dynamic cube, then lift.", flush=True)
print("Success criterion: cube center z rises above 0.06 m.", flush=True)

max_cube_z = CUBE_INITIAL_Z
success = False

for step in range(MAX_STEPS):
    left_y, right_y, finger_z = phase_targets(step)
    set_object_position(left_finger, [0.0, left_y, finger_z])
    set_object_position(right_finger, [0.0, right_y, finger_z])

    simulation_context.step(render=not HEADLESS)

    cube_position = get_object_position(target_cube)
    max_cube_z = max(max_cube_z, float(cube_position[2]))
    success = success or cube_position[2] > 0.06

    if step % 60 == 0:
        print(
            f"step={step:04d} "
            f"cube_z={cube_position[2]:.4f} "
            f"max_cube_z={max_cube_z:.4f} "
            f"success={success}",
            flush=True,
        )

print(f"FINAL max_cube_z={max_cube_z:.4f} success={success}", flush=True)

simulation_context.stop()
simulation_app.close()
