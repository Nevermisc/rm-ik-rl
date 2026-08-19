from isaacsim import SimulationApp

import os

HEADLESS = os.environ.get("ISAAC_HEADLESS", "0") == "1"
MAX_STEPS = int(os.environ.get("ISAAC_MAX_STEPS", "0"))
GRIPPER_CLOSE_START_STEP = int(os.environ.get("GRIPPER_CLOSE_START_STEP", "600"))
GRIPPER_CLOSE_DURATION_STEPS = int(os.environ.get("GRIPPER_CLOSE_DURATION_STEPS", "240"))

simulation_app = SimulationApp({"renderer": "RaytracedLighting", "headless": HEADLESS})

import numpy as np
import omni.graph.core as og
import usdrt.Sdf
from isaacsim.core.api import SimulationContext
from isaacsim.core.api.materials.physics_material import PhysicsMaterial
from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
from isaacsim.core.utils import extensions, prims, rotations, viewports
from pxr import Gf, Usd, UsdGeom, UsdPhysics


RM65_STAGE_PATH = "/RM65"
RM65_ARTICULATION_PATH = "/RM65/root_joint/root_joint"
RM65_USD_PATH = "/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd"

LINK6_CANDIDATE_PATHS = [
    "/RM65/root_joint/link_6",
    "/RM65/root_joint/root_joint/link_6",
    "/RM65/root_joint/Link6",
    "/RM65/root_joint/root_joint/Link6",
]

TABLE_HEIGHT = 0.0
CUBE_SIZE = 0.045
CUBE_PATH = "/World/target_cube"

LEFT_FINGER_PATH = "/World/Link6FollowGripper/left_finger"
RIGHT_FINGER_PATH = "/World/Link6FollowGripper/right_finger"
PALM_PATH = "/World/Link6FollowGripper/palm"


def make_kinematic(rigid_object):
    rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(rigid_object.prim)
    rigid_body_api.CreateKinematicEnabledAttr().Set(True)


def find_first_existing_prim(stage, candidate_paths):
    for path in candidate_paths:
        prim = stage.GetPrimAtPath(path)
        if prim.IsValid():
            return path, prim
    raise RuntimeError(
        "Could not find RM65 link_6 prim. Tried: "
        + ", ".join(candidate_paths)
    )


def prim_world_pose(stage, prim_path):
    prim = stage.GetPrimAtPath(prim_path)
    xformable = UsdGeom.Xformable(prim)
    world_matrix = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    translation = np.array(world_matrix.ExtractTranslation(), dtype=np.float64)

    rotation = Gf.Transform(world_matrix).GetRotation().GetQuat()
    imaginary = rotation.GetImaginary()
    orientation_wxyz = np.array(
        [rotation.GetReal(), imaginary[0], imaginary[1], imaginary[2]],
        dtype=np.float64,
    )

    return translation, orientation_wxyz


def local_point_to_world(stage, parent_path, local_point):
    parent_prim = stage.GetPrimAtPath(parent_path)
    parent_matrix = UsdGeom.Xformable(parent_prim).ComputeLocalToWorldTransform(
        Usd.TimeCode.Default()
    )
    world_point = parent_matrix.Transform(Gf.Vec3d(*local_point))
    return np.array(world_point, dtype=np.float64)


class Link6FollowGripper:
    """Functional gripper that follows the RM65 link_6 frame.

    V2 keeps the gripper deliberately simple:
      - kinematic cuboid palm/fingers;
      - pose recomputed from link_6 every frame;
      - opening can be controlled by a simple close schedule.

    This makes it possible to run MoveIt2 arm motion and see the simplified
    gripper stay attached to the simulated end-effector.
    """

    def __init__(self, simulation_context, link6_path):
        self.stage = simulation_context.stage
        self.link6_path = link6_path

        self.opening = 0.055
        self.closed_opening = 0.020
        self.max_opening = 0.075
        self.tip_offset_x = 0.085
        self.vertical_offset_z = 0.000

        self.grip_material = PhysicsMaterial(
            prim_path="/World/PhysicsMaterials/link6_follow_grip",
            static_friction=4.0,
            dynamic_friction=3.0,
            restitution=0.0,
        )

        self.palm = DynamicCuboid(
            prim_path=PALM_PATH,
            name="link6_follow_palm",
            position=np.array([0.0, 0.0, 0.0]),
            scale=np.array([0.055, 0.080, 0.025]),
            color=np.array([0.05, 0.05, 0.05]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        self.left_finger = DynamicCuboid(
            prim_path=LEFT_FINGER_PATH,
            name="link6_follow_left_finger",
            position=np.array([0.0, 0.0, 0.0]),
            scale=np.array([0.085, 0.014, 0.045]),
            color=np.array([0.02, 0.02, 0.02]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        self.right_finger = DynamicCuboid(
            prim_path=RIGHT_FINGER_PATH,
            name="link6_follow_right_finger",
            position=np.array([0.0, 0.0, 0.0]),
            scale=np.array([0.085, 0.014, 0.045]),
            color=np.array([0.02, 0.02, 0.02]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        make_kinematic(self.palm)
        make_kinematic(self.left_finger)
        make_kinematic(self.right_finger)

    def set_opening(self, opening):
        self.opening = float(np.clip(opening, self.closed_opening, self.max_opening))

    def set_close_fraction(self, alpha):
        alpha = float(np.clip(alpha, 0.0, 1.0))
        self.set_opening(self.max_opening + (self.closed_opening - self.max_opening) * alpha)

    def update_pose_from_link6(self):
        _, link6_orientation = prim_world_pose(self.stage, self.link6_path)

        palm_position = local_point_to_world(
            self.stage,
            self.link6_path,
            [0.040, 0.0, self.vertical_offset_z],
        )
        left_position = local_point_to_world(
            self.stage,
            self.link6_path,
            [self.tip_offset_x, self.opening, self.vertical_offset_z],
        )
        right_position = local_point_to_world(
            self.stage,
            self.link6_path,
            [self.tip_offset_x, -self.opening, self.vertical_offset_z],
        )

        self.palm.set_world_pose(position=palm_position, orientation=link6_orientation)
        self.left_finger.set_world_pose(position=left_position, orientation=link6_orientation)
        self.right_finger.set_world_pose(position=right_position, orientation=link6_orientation)


def create_ros2_action_graph():
    og.Controller.edit(
        {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnImpulseEvent", "omni.graph.action.OnImpulseEvent"),
                ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                ("Context", "isaacsim.ros2.bridge.ROS2Context"),
                ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
                ("SubscribeJointState", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
                ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnImpulseEvent.outputs:execOut", "PublishJointState.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "SubscribeJointState.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "PublishClock.inputs:execIn"),
                ("OnImpulseEvent.outputs:execOut", "ArticulationController.inputs:execIn"),
                ("Context.outputs:context", "PublishJointState.inputs:context"),
                ("Context.outputs:context", "SubscribeJointState.inputs:context"),
                ("Context.outputs:context", "PublishClock.inputs:context"),
                ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),
                ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
                ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
                ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("ArticulationController.inputs:robotPath", RM65_ARTICULATION_PATH),
                ("PublishJointState.inputs:topicName", "isaac_joint_states"),
                ("SubscribeJointState.inputs:topicName", "isaac_joint_commands"),
                ("PublishJointState.inputs:targetPrim", [usdrt.Sdf.Path(RM65_ARTICULATION_PATH)]),
            ],
        },
    )


def create_table_and_cube():
    table_material = PhysicsMaterial(
        prim_path="/World/PhysicsMaterials/table_material",
        static_friction=2.0,
        dynamic_friction=2.0,
        restitution=0.0,
    )

    FixedCuboid(
        prim_path="/World/table",
        name="table",
        position=np.array([0.35, 0.0, TABLE_HEIGHT - 0.012]),
        scale=np.array([0.60, 0.50, 0.024]),
        color=np.array([0.45, 0.45, 0.45]),
        physics_material=table_material,
    )

    cube = DynamicCuboid(
        prim_path=CUBE_PATH,
        name="target_cube",
        position=np.array([0.35, 0.0, TABLE_HEIGHT + CUBE_SIZE / 2.0 + 0.002]),
        scale=np.array([CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]),
        color=np.array([0.9, 0.25, 0.15]),
        mass=0.035,
        physics_material=table_material,
    )

    return cube


def gripper_close_fraction_for_step(step_index):
    if step_index < GRIPPER_CLOSE_START_STEP:
        return 0.0
    alpha = (step_index - GRIPPER_CLOSE_START_STEP) / max(1, GRIPPER_CLOSE_DURATION_STEPS)
    return float(np.clip(alpha, 0.0, 1.0))


def main():
    extensions.enable_extension("isaacsim.ros2.bridge")
    simulation_app.update()

    simulation_context = SimulationContext(stage_units_in_meters=1.0)

    viewports.set_camera_view(
        eye=np.array([1.1, 1.1, 0.75]),
        target=np.array([0.25, 0.0, 0.35]),
    )

    prims.create_prim(
        RM65_STAGE_PATH,
        "Xform",
        position=np.array([0.0, 0.0, 0.0]),
        orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 0)),
        usd_path=RM65_USD_PATH,
    )

    simulation_app.update()
    create_ros2_action_graph()
    simulation_app.update()

    link6_path, _ = find_first_existing_prim(
        simulation_context.stage,
        LINK6_CANDIDATE_PATHS,
    )
    cube = create_table_and_cube()
    gripper = Link6FollowGripper(simulation_context, link6_path)

    simulation_context.initialize_physics()
    simulation_context.play()

    print("RM65 Isaac ROS2 bridge with link_6 gripper V2 started.", flush=True)
    print("Publishing: /isaac_joint_states", flush=True)
    print("Subscribing: /isaac_joint_commands", flush=True)
    print(f"FOUND_LINK6 path={link6_path}", flush=True)
    print(
        "Gripper schedule: "
        f"close_start_step={GRIPPER_CLOSE_START_STEP}, "
        f"close_duration_steps={GRIPPER_CLOSE_DURATION_STEPS}",
        flush=True,
    )

    step_index = 0
    max_cube_z = TABLE_HEIGHT + CUBE_SIZE / 2.0 + 0.002

    while simulation_app.is_running():
        close_fraction = gripper_close_fraction_for_step(step_index)
        gripper.set_close_fraction(close_fraction)
        gripper.update_pose_from_link6()

        simulation_context.step(render=not HEADLESS)
        og.Controller.set(
            og.Controller.attribute("/ActionGraph/OnImpulseEvent.state:enableImpulse"),
            True,
        )

        cube_position, _ = cube.get_world_pose()
        cube_position = np.asarray(cube_position)
        max_cube_z = max(max_cube_z, float(cube_position[2]))

        if step_index % 120 == 0:
            link6_position, _ = prim_world_pose(simulation_context.stage, link6_path)
            print(
                f"step={step_index:05d} "
                f"link6=[{link6_position[0]:+.3f},{link6_position[1]:+.3f},{link6_position[2]:+.3f}] "
                f"opening={gripper.opening:.4f} "
                f"cube_z={cube_position[2]:.4f} "
                f"max_cube_z={max_cube_z:.4f}",
                flush=True,
            )

        step_index += 1
        if MAX_STEPS > 0 and step_index >= MAX_STEPS:
            break

    print(
        f"FINAL bridge_with_link6_gripper_v2 steps={step_index} max_cube_z={max_cube_z:.4f}",
        flush=True,
    )

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    main()
