from isaacsim import SimulationApp

import os

HEADLESS = os.environ.get("ISAAC_HEADLESS", "0") == "1"
MAX_STEPS = int(os.environ.get("ISAAC_MAX_STEPS", "0"))

simulation_app = SimulationApp({"renderer": "RaytracedLighting", "headless": HEADLESS})

import math

import numpy as np
from isaacsim.core.api import SimulationContext
from isaacsim.core.utils import prims, rotations, viewports
from pxr import Gf, UsdGeom


RM65_STAGE_PATH = "/RM65"
RM65_LINK6_PATH = "/RM65/root_joint/link_6"
RM65_USD_PATH = "/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd"

GRIPPER_ROOT_PATH = f"{RM65_LINK6_PATH}/simple_two_finger_gripper"


def set_transform(prim_path, translate=(0.0, 0.0, 0.0), rotate_xyz=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    prim = simulation_context.stage.GetPrimAtPath(prim_path)
    xformable = UsdGeom.Xformable(prim)

    xformable.ClearXformOpOrder()
    xformable.AddTranslateOp().Set(Gf.Vec3d(*translate))
    xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rotate_xyz))
    xformable.AddScaleOp().Set(Gf.Vec3f(*scale))


def create_box(stage, prim_path, translate, scale, color, rotate_xyz=(0.0, 0.0, 0.0)):
    cube = UsdGeom.Cube.Define(stage, prim_path)
    cube.CreateSizeAttr(1.0)
    cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    set_transform(prim_path, translate=translate, rotate_xyz=rotate_xyz, scale=scale)
    return cube


def update_translate(prim_path, translate):
    prim = simulation_context.stage.GetPrimAtPath(prim_path)
    xformable = UsdGeom.Xformable(prim)
    for op in xformable.GetOrderedXformOps():
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            op.Set(Gf.Vec3d(*translate))
            return

    xformable.AddTranslateOp().Set(Gf.Vec3d(*translate))


def build_simple_gripper():
    stage = simulation_context.stage

    if stage.GetPrimAtPath(GRIPPER_ROOT_PATH):
        stage.RemovePrim(GRIPPER_ROOT_PATH)

    UsdGeom.Xform.Define(stage, GRIPPER_ROOT_PATH)
    set_transform(GRIPPER_ROOT_PATH, translate=(0.0, 0.0, 0.03))

    black = (0.02, 0.02, 0.02)
    dark_gray = (0.12, 0.12, 0.12)
    metal = (0.65, 0.65, 0.62)
    rubber = (0.01, 0.01, 0.01)

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/mount_plate",
        translate=(0.0, 0.0, 0.025),
        scale=(0.075, 0.075, 0.018),
        color=metal,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/black_palm",
        translate=(0.0, 0.0, 0.085),
        scale=(0.095, 0.035, 0.095),
        color=black,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/left_inner_link",
        translate=(0.0, 0.045, 0.155),
        rotate_xyz=(-18.0, 0.0, 0.0),
        scale=(0.018, 0.016, 0.105),
        color=dark_gray,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/right_inner_link",
        translate=(0.0, -0.045, 0.155),
        rotate_xyz=(18.0, 0.0, 0.0),
        scale=(0.018, 0.016, 0.105),
        color=dark_gray,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/left_finger",
        translate=(0.0, 0.075, 0.245),
        scale=(0.022, 0.018, 0.105),
        color=black,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/right_finger",
        translate=(0.0, -0.075, 0.245),
        scale=(0.022, 0.018, 0.105),
        color=black,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/left_rubber_pad",
        translate=(0.0, 0.052, 0.300),
        scale=(0.030, 0.012, 0.055),
        color=rubber,
    )

    create_box(
        stage,
        f"{GRIPPER_ROOT_PATH}/right_rubber_pad",
        translate=(0.0, -0.052, 0.300),
        scale=(0.030, 0.012, 0.055),
        color=rubber,
    )


def animate_gripper(sim_time):
    # Finger pad center distance from the gripper center line.
    # Range:
    #   closed: about 8 mm from center line, leaving only a small visual gap
    #   open:   about 58 mm from center line, making the opening easy to see
    opening = 0.008 + 0.050 * (0.5 + 0.5 * math.sin(sim_time * 1.5))

    update_translate(f"{GRIPPER_ROOT_PATH}/left_finger", (0.0, opening + 0.018, 0.245))
    update_translate(f"{GRIPPER_ROOT_PATH}/right_finger", (0.0, -opening - 0.018, 0.245))
    update_translate(f"{GRIPPER_ROOT_PATH}/left_rubber_pad", (0.0, opening, 0.300))
    update_translate(f"{GRIPPER_ROOT_PATH}/right_rubber_pad", (0.0, -opening, 0.300))


simulation_context = SimulationContext(stage_units_in_meters=1.0)

viewports.set_camera_view(
    eye=np.array([0.75, 0.75, 0.65]),
    target=np.array([0.0, 0.0, 0.35]),
)

prims.create_prim(
    RM65_STAGE_PATH,
    "Xform",
    position=np.array([0.0, 0.0, 0.0]),
    orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 0)),
    usd_path=RM65_USD_PATH,
)

simulation_app.update()
build_simple_gripper()

simulation_context.initialize_physics()
simulation_context.play()

print("RM65 simple gripper visual test started.")
print(f"Gripper root: {GRIPPER_ROOT_PATH}")
print("This V0 gripper is visual/kinematic for layout validation before building physical grasp control.")

sim_time = 0.0
step_count = 0
while simulation_app.is_running():
    simulation_context.step(render=True)
    sim_time += 1.0 / 60.0
    step_count += 1
    animate_gripper(sim_time)

    if MAX_STEPS > 0 and step_count >= MAX_STEPS:
        break

simulation_context.stop()
simulation_app.close()
