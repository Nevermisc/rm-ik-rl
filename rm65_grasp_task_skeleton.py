from isaacsim import SimulationApp

import os

HEADLESS = os.environ.get("ISAAC_HEADLESS", "0") == "1"
MAX_STEPS = int(os.environ.get("ISAAC_MAX_STEPS", "900"))

simulation_app = SimulationApp({"renderer": "RaytracedLighting", "headless": HEADLESS})

import numpy as np
from isaacsim.core.api import SimulationContext
from isaacsim.core.api.materials.physics_material import PhysicsMaterial
from isaacsim.core.api.objects import DynamicCuboid, FixedCuboid
from isaacsim.core.utils import prims, rotations, viewports
from pxr import Gf, UsdPhysics


RM65_STAGE_PATH = "/RM65"
RM65_USD_PATH = "/home/iot22/robot-learning/rm-ik-rl/assets/RM65-B/RM65-B.usd"

TABLE_HEIGHT = 0.0
CUBE_SIZE = 0.045
CUBE_INITIAL_Z = TABLE_HEIGHT + CUBE_SIZE / 2.0 + 0.002

GRASP_CENTER_X = 0.35
GRASP_CENTER_Y = 0.00

LEFT_FINGER_PATH = "/World/FunctionalGripper/left_finger"
RIGHT_FINGER_PATH = "/World/FunctionalGripper/right_finger"
CUBE_PATH = "/World/target_cube"


class SimpleGraspTask:
    """A minimal grasp-task skeleton for later reinforcement learning.

    This is not a final RM65 arm-control environment yet.  It is the next
    functional layer after the contact test:

      scene   : RM65 visual model + table + cube + controllable collision fingers
      action  : gripper opening and vertical lift target
      obs     : cube height, finger opening, relative finger/cube geometry
      reward  : lift success + closing/lifting progress
      success : cube center rises above a threshold
    """

    def __init__(self, simulation_context):
        self.sim = simulation_context
        self.stage = simulation_context.stage

        self.grip_material = PhysicsMaterial(
            prim_path="/World/PhysicsMaterials/high_friction_grip",
            static_friction=4.0,
            dynamic_friction=3.0,
            restitution=0.0,
        )

        self.cube_material = PhysicsMaterial(
            prim_path="/World/PhysicsMaterials/cube_material",
            static_friction=2.0,
            dynamic_friction=2.0,
            restitution=0.0,
        )

        self.table = FixedCuboid(
            prim_path="/World/table",
            name="table",
            position=np.array([GRASP_CENTER_X, GRASP_CENTER_Y, TABLE_HEIGHT - 0.012]),
            scale=np.array([0.60, 0.50, 0.024]),
            color=np.array([0.45, 0.45, 0.45]),
            physics_material=self.grip_material,
        )

        self.cube = DynamicCuboid(
            prim_path=CUBE_PATH,
            name="target_cube",
            position=np.array([GRASP_CENTER_X, GRASP_CENTER_Y, CUBE_INITIAL_Z]),
            scale=np.array([CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]),
            color=np.array([0.9, 0.25, 0.15]),
            mass=0.035,
            physics_material=self.cube_material,
        )

        self.left_finger = DynamicCuboid(
            prim_path=LEFT_FINGER_PATH,
            name="left_finger",
            position=np.array([GRASP_CENTER_X, GRASP_CENTER_Y + 0.085, TABLE_HEIGHT + 0.060]),
            scale=np.array([0.035, 0.018, 0.115]),
            color=np.array([0.02, 0.02, 0.02]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        self.right_finger = DynamicCuboid(
            prim_path=RIGHT_FINGER_PATH,
            name="right_finger",
            position=np.array([GRASP_CENTER_X, GRASP_CENTER_Y - 0.085, TABLE_HEIGHT + 0.060]),
            scale=np.array([0.035, 0.018, 0.115]),
            color=np.array([0.02, 0.02, 0.02]),
            mass=1.0,
            physics_material=self.grip_material,
        )

        self._make_kinematic(self.left_finger)
        self._make_kinematic(self.right_finger)

        self.opening = 0.085
        self.finger_z = TABLE_HEIGHT + 0.060
        self.max_cube_z = CUBE_INITIAL_Z

    def _make_kinematic(self, rigid_object):
        rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(rigid_object.prim)
        rigid_body_api.CreateKinematicEnabledAttr().Set(True)

    def reset(self):
        """Reset cube and gripper to the start of one grasp episode."""
        self.opening = 0.085
        self.finger_z = TABLE_HEIGHT + 0.060
        self.max_cube_z = CUBE_INITIAL_Z

        self.cube.set_world_pose(position=np.array([GRASP_CENTER_X, GRASP_CENTER_Y, CUBE_INITIAL_Z]))
        self.cube.set_linear_velocity(np.zeros(3))
        self.cube.set_angular_velocity(np.zeros(3))
        self._apply_gripper_pose()

        return self.get_observation()

    def step(self, action):
        """Apply one action and return obs, reward, done, info.

        action[0]: target opening change, negative means close
        action[1]: target vertical change, positive means lift
        """
        action = np.clip(np.asarray(action, dtype=np.float64), -1.0, 1.0)

        self.opening = float(np.clip(self.opening + action[0] * 0.006, 0.022, 0.090))
        self.finger_z = float(np.clip(self.finger_z + action[1] * 0.006, TABLE_HEIGHT + 0.050, TABLE_HEIGHT + 0.200))

        self._apply_gripper_pose()
        self.sim.step(render=not HEADLESS)

        obs = self.get_observation()
        reward = self.compute_reward(obs)
        done = bool(obs["success"])
        info = {
            "max_cube_z": self.max_cube_z,
            "success": obs["success"],
        }

        return obs, reward, done, info

    def scripted_action(self, step_index):
        """A deterministic policy used as a smoke test before real RL."""
        if step_index < 20:
            return np.array([0.0, 0.0])
        if step_index < 90:
            return np.array([-1.0, 0.0])
        if step_index < 300:
            return np.array([0.0, 1.0])
        return np.array([0.0, 0.0])

    def _apply_gripper_pose(self):
        left_y = GRASP_CENTER_Y + self.opening
        right_y = GRASP_CENTER_Y - self.opening

        self.left_finger.set_world_pose(
            position=np.array([GRASP_CENTER_X, left_y, self.finger_z])
        )
        self.right_finger.set_world_pose(
            position=np.array([GRASP_CENTER_X, right_y, self.finger_z])
        )

    def get_observation(self):
        cube_pos, _ = self.cube.get_world_pose()
        left_pos, _ = self.left_finger.get_world_pose()
        right_pos, _ = self.right_finger.get_world_pose()

        cube_pos = np.asarray(cube_pos)
        left_pos = np.asarray(left_pos)
        right_pos = np.asarray(right_pos)

        self.max_cube_z = max(self.max_cube_z, float(cube_pos[2]))
        success = bool(cube_pos[2] > 0.06)

        return {
            "cube_pos": cube_pos,
            "left_finger_pos": left_pos,
            "right_finger_pos": right_pos,
            "opening": float(abs(left_pos[1] - right_pos[1]) / 2.0),
            "finger_z": float((left_pos[2] + right_pos[2]) / 2.0),
            "cube_z": float(cube_pos[2]),
            "success": success,
        }

    def compute_reward(self, obs):
        closed_score = np.clip((0.090 - obs["opening"]) / (0.090 - 0.022), 0.0, 1.0)
        finger_lift_score = np.clip((obs["finger_z"] - (TABLE_HEIGHT + 0.060)) / 0.140, 0.0, 1.0)

        cube_lift_reward = 35.0 * max(0.0, obs["cube_z"] - CUBE_INITIAL_Z)
        close_reward = 0.25 * closed_score
        coordinated_lift_reward = 0.20 * closed_score * finger_lift_score
        success_bonus = 5.0 if obs["success"] else 0.0

        return float(cube_lift_reward + close_reward + coordinated_lift_reward + success_bonus)


def create_simulation_context_with_rm65():
    simulation_context = SimulationContext(stage_units_in_meters=1.0)

    viewports.set_camera_view(
        eye=np.array([0.75, 0.75, 0.45]),
        target=np.array([0.25, 0.0, 0.12]),
    )

    prims.create_prim(
        RM65_STAGE_PATH,
        "Xform",
        position=np.array([0.0, -0.28, 0.0]),
        orientation=rotations.gf_rotation_to_np_array(Gf.Rotation(Gf.Vec3d(0, 0, 1), 0)),
        usd_path=RM65_USD_PATH,
    )

    return simulation_context


def run_scripted_demo():
    simulation_context = create_simulation_context_with_rm65()
    task = SimpleGraspTask(simulation_context)

    simulation_context.initialize_physics()
    simulation_context.play()

    print("RM65 grasp task skeleton started.", flush=True)
    print("This is the RL-ready task skeleton: observation/action/reward/success are explicit.", flush=True)

    obs = task.reset()
    print(f"initial_obs cube_z={obs['cube_z']:.4f} opening={obs['opening']:.4f}", flush=True)

    episode_reward = 0.0
    info = {"max_cube_z": task.max_cube_z, "success": False}
    for step_index in range(MAX_STEPS):
        action = task.scripted_action(step_index)
        obs, reward, done, info = task.step(action)
        episode_reward += reward

        if step_index % 60 == 0:
            print(
                f"step={step_index:04d} "
                f"cube_z={obs['cube_z']:.4f} "
                f"opening={obs['opening']:.4f} "
                f"reward={reward:.4f} "
                f"success={obs['success']}",
                flush=True,
            )

    print(
        f"FINAL episode_reward={episode_reward:.4f} "
        f"max_cube_z={info['max_cube_z']:.4f} "
        f"success={info['success']}",
        flush=True,
    )

    simulation_context.stop()
    simulation_app.close()


if __name__ == "__main__":
    run_scripted_demo()
