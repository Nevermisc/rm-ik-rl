from isaacsim import SimulationApp

import os

HEADLESS = os.environ.get("ISAAC_HEADLESS", "0") == "1"
MAX_STEPS = int(os.environ.get("ISAAC_MAX_STEPS", "0"))
CONTROL_MODE = os.environ.get("ISAAC_GRIPPER_CONTROL_MODE", "policy")
POLICY_MODEL_PATH = os.environ.get(
    "ISAAC_PPO_MODEL_PATH",
    "/home/iot22/robot-learning/rm-ik-rl/rm65_grasp_ppo_policy.pt",
)
POLICY_START_STEP = int(os.environ.get("ISAAC_POLICY_START_STEP", "600"))
POLICY_EPISODE_STEPS = int(os.environ.get("ISAAC_POLICY_EPISODE_STEPS", "360"))

simulation_app = SimulationApp({"renderer": "RaytracedLighting", "headless": HEADLESS})

import numpy as np
import omni.graph.core as og
import torch
import torch.nn as nn
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
CUBE_INITIAL_Z = TABLE_HEIGHT + CUBE_SIZE / 2.0 + 0.002
CUBE_PATH = "/World/target_cube"

LEFT_FINGER_PATH = "/World/Link6PolicyGripper/left_finger"
RIGHT_FINGER_PATH = "/World/Link6PolicyGripper/right_finger"
PALM_PATH = "/World/Link6PolicyGripper/palm"


class ActorCritic(nn.Module):
    """Small actor-critic model matching rm65_grasp_ppo_train.py checkpoints."""

    def __init__(self, obs_dim, action_dim):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
        )
        self.actor_mean = nn.Linear(64, action_dim)
        self.critic = nn.Linear(64, 1)
        self.log_std = nn.Parameter(torch.full((action_dim,), -0.4))

    def forward(self, obs):
        features = self.shared(obs)
        mean = torch.tanh(self.actor_mean(features))
        value = self.critic(features).squeeze(-1)
        std = torch.exp(self.log_std).expand_as(mean)
        return mean, std, value

    def deterministic_action(self, obs):
        mean, _, value = self.forward(obs)
        return torch.clamp(mean, -1.0, 1.0), value


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


class Link6PolicyGripper:
    """Functional gripper attached to RM65 link_6 and controlled by policy action.

    action[0] controls opening:
      negative -> close
      positive -> open

    action[1] controls local vertical offset:
      positive -> lift along the gripper local z direction
      negative -> lower along the gripper local z direction
    """

    def __init__(self, simulation_context, link6_path):
        self.stage = simulation_context.stage
        self.link6_path = link6_path

        self.opening = 0.075
        self.closed_opening = 0.020
        self.max_opening = 0.085
        self.tip_offset_x = 0.085
        self.vertical_offset_z = 0.000
        self.min_vertical_offset_z = -0.030
        self.max_vertical_offset_z = 0.160

        self.grip_material = PhysicsMaterial(
            prim_path="/World/PhysicsMaterials/link6_policy_grip",
            static_friction=4.0,
            dynamic_friction=3.0,
            restitution=0.0,
        )

        self.palm = DynamicCuboid(
            prim_path=PALM_PATH,
            name="link6_policy_palm",
            position=np.array([0.0, 0.0, 0.0]),
            scale=np.array([0.055, 0.080, 0.025]),
            color=np.array([0.05, 0.05, 0.05]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        self.left_finger = DynamicCuboid(
            prim_path=LEFT_FINGER_PATH,
            name="link6_policy_left_finger",
            position=np.array([0.0, 0.0, 0.0]),
            scale=np.array([0.085, 0.014, 0.045]),
            color=np.array([0.02, 0.02, 0.02]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        self.right_finger = DynamicCuboid(
            prim_path=RIGHT_FINGER_PATH,
            name="link6_policy_right_finger",
            position=np.array([0.0, 0.0, 0.0]),
            scale=np.array([0.085, 0.014, 0.045]),
            color=np.array([0.02, 0.02, 0.02]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        make_kinematic(self.palm)
        make_kinematic(self.left_finger)
        make_kinematic(self.right_finger)

    def apply_action(self, action):
        action = np.clip(np.asarray(action, dtype=np.float64), -1.0, 1.0)
        self.opening = float(
            np.clip(
                self.opening + action[0] * 0.006,
                self.closed_opening,
                self.max_opening,
            )
        )
        self.vertical_offset_z = float(
            np.clip(
                self.vertical_offset_z + action[1] * 0.006,
                self.min_vertical_offset_z,
                self.max_vertical_offset_z,
            )
        )

    def scripted_action(self, policy_step_index):
        if policy_step_index < 20:
            return np.array([0.0, 0.0])
        if policy_step_index < 90:
            return np.array([-1.0, 0.0])
        if policy_step_index < 300:
            return np.array([0.0, 1.0])
        return np.array([0.0, 0.0])

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

    def get_finger_positions(self):
        left_position, _ = self.left_finger.get_world_pose()
        right_position, _ = self.right_finger.get_world_pose()
        return np.asarray(left_position), np.asarray(right_position)


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
        prim_path="/World/PhysicsMaterials/policy_table_material",
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
        position=np.array([0.35, 0.0, CUBE_INITIAL_Z]),
        scale=np.array([CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]),
        color=np.array([0.9, 0.25, 0.15]),
        mass=0.035,
        physics_material=table_material,
    )

    return cube


def load_policy_model(model_path):
    checkpoint = torch.load(model_path, map_location="cpu")
    model = ActorCritic(checkpoint["obs_dim"], checkpoint["action_dim"])
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model


def get_observation(cube, gripper):
    cube_position, _ = cube.get_world_pose()
    left_position, right_position = gripper.get_finger_positions()

    cube_position = np.asarray(cube_position)
    finger_center = 0.5 * (left_position + right_position)
    cube_relative_to_finger = cube_position - finger_center

    return {
        "cube_pos": cube_position,
        "left_finger_pos": left_position,
        "right_finger_pos": right_position,
        "opening": float(gripper.opening),
        "finger_z": float(finger_center[2]),
        "cube_z": float(cube_position[2]),
        "cube_relative_to_finger": cube_relative_to_finger,
        "success": bool(cube_position[2] > 0.06),
    }


def obs_to_vector(obs, policy_step_index):
    rel = obs["cube_relative_to_finger"]
    return np.array(
        [
            obs["cube_z"],
            obs["cube_z"] - CUBE_INITIAL_Z,
            obs["opening"],
            obs["finger_z"],
            rel[0],
            rel[1],
            rel[2],
            policy_step_index / max(1, POLICY_EPISODE_STEPS),
        ],
        dtype=np.float32,
    )


def policy_action(model, obs, policy_step_index):
    obs_vec = obs_to_vector(obs, policy_step_index)
    obs_tensor = torch.as_tensor(obs_vec, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        action_tensor, _ = model.deterministic_action(obs_tensor)
    return action_tensor.squeeze(0).cpu().numpy()


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
    gripper = Link6PolicyGripper(simulation_context, link6_path)

    model = None
    if CONTROL_MODE == "policy":
        model = load_policy_model(POLICY_MODEL_PATH)

    simulation_context.initialize_physics()
    simulation_context.play()

    print("RM65 Isaac ROS2 bridge with policy gripper V3 started.", flush=True)
    print("Publishing: /isaac_joint_states", flush=True)
    print("Subscribing: /isaac_joint_commands", flush=True)
    print(f"FOUND_LINK6 path={link6_path}", flush=True)
    print(f"control_mode={CONTROL_MODE}", flush=True)
    print(f"policy_start_step={POLICY_START_STEP}", flush=True)
    if model is not None:
        print(f"policy_model={POLICY_MODEL_PATH}", flush=True)

    step_index = 0
    policy_step_index = 0
    max_cube_z = CUBE_INITIAL_Z
    last_action = np.array([0.0, 0.0], dtype=np.float32)

    while simulation_app.is_running():
        gripper.update_pose_from_link6()
        obs = get_observation(cube, gripper)

        if step_index >= POLICY_START_STEP:
            if CONTROL_MODE == "policy":
                last_action = policy_action(model, obs, policy_step_index)
            elif CONTROL_MODE == "scripted":
                last_action = gripper.scripted_action(policy_step_index)
            elif CONTROL_MODE == "hold":
                last_action = np.array([0.0, 0.0], dtype=np.float32)
            else:
                raise ValueError(
                    "ISAAC_GRIPPER_CONTROL_MODE must be one of: policy, scripted, hold"
                )

            gripper.apply_action(last_action)
            policy_step_index += 1

        gripper.update_pose_from_link6()

        simulation_context.step(render=not HEADLESS)
        og.Controller.set(
            og.Controller.attribute("/ActionGraph/OnImpulseEvent.state:enableImpulse"),
            True,
        )

        obs = get_observation(cube, gripper)
        max_cube_z = max(max_cube_z, obs["cube_z"])

        if step_index % 120 == 0 or obs["success"]:
            link6_position, _ = prim_world_pose(simulation_context.stage, link6_path)
            print(
                f"step={step_index:05d} "
                f"policy_step={policy_step_index:04d} "
                f"link6=[{link6_position[0]:+.3f},{link6_position[1]:+.3f},{link6_position[2]:+.3f}] "
                f"action=[{last_action[0]:+.3f},{last_action[1]:+.3f}] "
                f"opening={gripper.opening:.4f} "
                f"local_z={gripper.vertical_offset_z:.4f} "
                f"cube_z={obs['cube_z']:.4f} "
                f"max_cube_z={max_cube_z:.4f} "
                f"success={obs['success']}",
                flush=True,
            )

        step_index += 1
        if MAX_STEPS > 0 and step_index >= MAX_STEPS:
            break
        if obs["success"]:
            break

    print(
        f"FINAL bridge_with_policy_gripper_v3 "
        f"steps={step_index} "
        f"policy_steps={policy_step_index} "
        f"max_cube_z={max_cube_z:.4f} "
        f"success={obs['success']}",
        flush=True,
    )

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    main()
