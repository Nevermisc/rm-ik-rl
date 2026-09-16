#!/usr/bin/env python3
"""Run a scripted RM65+4C2 table pick-and-place baseline in Isaac Lab."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--usd", type=Path, required=True)
parser.add_argument("--urdf", type=Path, required=True)
parser.add_argument("--description", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--transfer-joint-1-rad", type=float, default=0.8)
parser.add_argument(
    "--robot-base-z-m",
    type=float,
    default=0.0,
    help="World height of the robot mounting plane; Lula targets remain in the robot base frame.",
)
parser.add_argument("--arm-effort-limit-sim", type=float, default=300.0)
parser.add_argument("--arm-stiffness", type=float, default=1000.0)
parser.add_argument("--arm-damping", type=float, default=100.0)
parser.add_argument("--gripper-effort-limit-sim", type=float, default=20.0)
parser.add_argument("--gripper-stiffness", type=float, default=120.0)
parser.add_argument("--gripper-damping", type=float, default=12.0)
parser.add_argument("--gripper-close-target-rad", type=float, default=0.65)
parser.add_argument("--pregrasp-distance-m", type=float, default=0.10)
parser.add_argument("--grasp-world-offset-x-m", type=float, default=0.0)
parser.add_argument("--grasp-world-offset-z-m", type=float, default=0.0)
parser.add_argument(
    "--grasp-orientation-mode",
    choices=("reference", "top_down"),
    default="reference",
)
parser.add_argument("--top-down-yaw-rad", type=float, default=0.0)
parser.add_argument(
    "--top-down-tilt-rad",
    type=float,
    default=0.0,
    help="Tilt the link-to-block direction away from vertical while keeping the closing axis horizontal.",
)
parser.add_argument(
    "--top-down-ik-multistart",
    type=int,
    default=1,
    help="Number of deterministic joint-space seeds used to solve the top-down pose.",
)
parser.add_argument(
    "--top-down-blend",
    type=float,
    default=1.0,
    help="Interpolate from the calibrated side grasp (0) to the requested above-table pose (1).",
)
parser.add_argument(
    "--lift-mode",
    choices=("joint_reference", "cartesian_vertical"),
    default="joint_reference",
    help="Use the historical fixed joint target or solve a local vertical lift from the current grasp pose.",
)
parser.add_argument("--cartesian-lift-height-m", type=float, default=0.04)
parser.add_argument("--release-clearance-m", type=float, default=0.08)
parser.add_argument("--release-separation-assist-m", type=float, default=0.05)
parser.add_argument("--place-descent", action="store_true")
parser.add_argument("--place-descent-distance-m", type=float, default=0.10)
parser.add_argument(
    "--place-waypoint-steps",
    type=int,
    default=60,
    help="Simulation steps used for each approximately 1 cm place-descent segment.",
)
parser.add_argument(
    "--target-support-mode",
    choices=("wide_platform", "rotated_strip"),
    default="wide_platform",
)
parser.add_argument(
    "--target-collision-enable-stage",
    choices=("after_transfer", "after_place_descent"),
    default="after_transfer",
)
parser.add_argument("--diagnose-approach-only", action="store_true")
parser.add_argument("--diagnose-kinematics-only", action="store_true")
parser.add_argument("--collision-bypass-during-approach", action="store_true")
parser.add_argument("--initialize-at-grasp", action="store_true")
parser.add_argument("--disable-arm-gravity-during-approach", action="store_true")
parser.add_argument(
    "--disable-arm-gravity-through-transport",
    action="store_true",
    help="Keep arm-link gravity disabled after approach to isolate object grasp/transport physics.",
)
parser.add_argument("--natural-source-gravity", action="store_true")
parser.add_argument(
    "--enable-moving-gripper-gravity",
    action="store_true",
    help="Keep gravity enabled on all six moving 4C2 finger links.",
)
parser.add_argument(
    "--unassisted-release",
    action="store_true",
    help="After opening the gripper, let gravity place the block without pose or velocity injection.",
)
parser.add_argument(
    "--record-episode-dir",
    type=Path,
    help="Write a synchronized scripted-expert episode to this directory.",
)
parser.add_argument(
    "--record-stride-steps",
    type=int,
    default=12,
    help="Record one policy frame every N physics steps (12 gives 20 Hz at 240 Hz physics).",
)
parser.add_argument(
    "--episode-prompt",
    default="pick up the block and place it on the target",
    help="Language instruction stored with the expert episode.",
)
parser.add_argument(
    "--record-images",
    action="store_true",
    help="Record synchronized external and wrist RGB; requires --record-episode-dir and --enable_cameras.",
)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import numpy as np  # noqa: E402
import torch  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaacsim.core.utils.extensions import enable_extension  # noqa: E402

enable_extension("isaacsim.robot_motion.motion_generation")

from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg  # noqa: E402
from isaaclab.sensors import ContactSensor, ContactSensorCfg  # noqa: E402
from isaaclab.sensors.camera import Camera, CameraCfg  # noqa: E402
from openpi_extension.expert_episode import (  # noqa: E402
    EpisodeRecorder,
    normalize_gripper,
    validate_episode,
)
from grasp_geometry import compute_top_down_link_pose  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from isaaclab.utils import math as math_utils  # noqa: E402
from isaacsim.core.utils.rotations import rot_matrix_to_quat  # noqa: E402
from isaacsim.core.utils.stage import get_current_stage  # noqa: E402
from isaacsim.robot_motion.motion_generation.lula.kinematics import LulaKinematicsSolver  # noqa: E402
from pxr import PhysxSchema, UsdPhysics  # noqa: E402


ARM_JOINTS = [f"joint_{index}" for index in range(1, 7)]
ARM_BODY_PATHS = {f"/World/Robot/link_{index}" for index in range(1, 7)}
MOVING_GRIPPER_BODY_PATHS = {
    "/World/Robot/tool_r_1",
    "/World/Robot/tool_l_1",
    "/World/Robot/tool_r_2",
    "/World/Robot/tool_l_2",
    "/World/Robot/tool_r_3",
    "/World/Robot/tool_l_3",
}
BLOCK_SIZE = (0.060, 0.040, 0.025)
BLOCK_MASS_KG = 0.030
SOURCE_BLOCK_POSITION = np.array([-0.22128649, -0.00000383, 0.75670463], dtype=np.float64)
SOURCE_BLOCK_QUATERNION_WXYZ = (-0.20872162, -0.00000211, 0.97797507, 0.00002437)
TARGET_PLATFORM_SIZE = (0.200, 0.200, 0.040)
TARGET_PLATFORM_TOP_Z = 0.650
SOURCE_PLATFORM_SIZE = (0.120, 0.018, 0.020)
TARGET_STRIP_SIZE = (0.070, 0.018, 0.020)
SOURCE_PLATFORM_TOP_Z = 0.7330
RELEASE_DOWNWARD_SPEED_M_S = 0.10
RELEASE_SEPARATION_ASSIST_M = 0.05
TIP_LOCAL_POINTS = {
    "tool_r_2": (0.04368, -0.00645, 0.01250),
    "tool_l_2": (0.04368, 0.00645, 0.01257),
}
PAD_LOCAL_CENTERS = {
    "tool_r_2": (0.028775714, -0.011597111, -0.073257379),
    "tool_l_2": (0.027286683, 0.013343694, -0.072958842),
}
CONTACT_SENSORS: dict[str, ContactSensor] = {}
GRIPPER_MASTER_JOINT = "tool_gripper_joint"


def rotate_about_z(position: np.ndarray, angle: float) -> np.ndarray:
    cosine, sine = np.cos(angle), np.sin(angle)
    return np.array(
        [cosine * position[0] - sine * position[1], sine * position[0] + cosine * position[1], position[2]],
        dtype=np.float64,
    )


def quaternion_multiply_wxyz(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lw, lx, ly, lz = left
    rw, rx, ry, rz = right
    return np.array(
        [
            lw * rw - lx * rx - ly * ry - lz * rz,
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
        ],
        dtype=np.float64,
    )


def quaternion_to_matrix_wxyz(quaternion: np.ndarray) -> np.ndarray:
    w, x, y, z = quaternion
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def tip_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
    body_id = list(robot.data.body_names).index(body_name)
    local = torch.tensor(TIP_LOCAL_POINTS[body_name], device=robot.device).unsqueeze(0)
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
    )[0]


def body_world_position(robot: Articulation, body_name: str) -> torch.Tensor:
    body_id = list(robot.data.body_names).index(body_name)
    return robot.data.body_pos_w[0, body_id]


def local_point_world_position(
    robot: Articulation, body_name: str, local_position: tuple[float, float, float]
) -> torch.Tensor:
    body_id = list(robot.data.body_names).index(body_name)
    local = torch.tensor(local_position, device=robot.device).unsqueeze(0)
    return robot.data.body_pos_w[0, body_id] + math_utils.quat_apply(
        robot.data.body_quat_w[0, body_id].unsqueeze(0), local
    )[0]


class ExpertEpisodeCapture:
    """Sample observations and the action targets applied on the next physics step."""

    def __init__(
        self,
        recorder: EpisodeRecorder,
        arm_ids: list[int],
        gripper_master_id: int,
        stride_steps: int,
        physics_dt: float,
        sim: SimulationContext,
        external_camera: Camera | None = None,
        wrist_camera: Camera | None = None,
        wrist_tool_body_id: int | None = None,
    ) -> None:
        self.recorder = recorder
        self.arm_ids = arm_ids
        self.gripper_master_id = gripper_master_id
        self.stride_steps = stride_steps
        self.physics_dt = physics_dt
        self.sim = sim
        self.external_camera = external_camera
        self.wrist_camera = wrist_camera
        self.wrist_tool_body_id = wrist_tool_body_id
        self.wrist_local_offset: torch.Tensor | None = None
        self.wrist_local_forward: torch.Tensor | None = None
        self.sim_step = 0

    @staticmethod
    def _rgb(camera: Camera) -> np.ndarray:
        image = camera.data.output["rgb"][0, ..., :3].detach().cpu().numpy()
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        return image

    def _render_images(self, robot: Articulation, cube: RigidObject) -> tuple[np.ndarray, np.ndarray]:
        if self.external_camera is None or self.wrist_camera is None:
            raise RuntimeError("both cameras are required for image recording")
        if self.wrist_tool_body_id is None:
            raise RuntimeError("wrist tool body id is required for image recording")
        tool_position = robot.data.body_pos_w[0, self.wrist_tool_body_id]
        tool_quaternion = robot.data.body_quat_w[0, self.wrist_tool_body_id]
        if self.wrist_local_offset is None:
            world_offset = torch.tensor([0.0, 0.15, 0.10], device=robot.device)
            eye = tool_position + world_offset
            world_forward = torch.nn.functional.normalize(cube.data.root_pos_w[0] - eye, dim=0)
            inverse_tool_quaternion = math_utils.quat_conjugate(tool_quaternion.unsqueeze(0))[0]
            self.wrist_local_offset = math_utils.quat_apply(
                inverse_tool_quaternion.unsqueeze(0), world_offset.unsqueeze(0)
            )[0]
            self.wrist_local_forward = math_utils.quat_apply(
                inverse_tool_quaternion.unsqueeze(0), world_forward.unsqueeze(0)
            )[0]
        assert self.wrist_local_forward is not None
        eye = tool_position + math_utils.quat_apply(
            tool_quaternion.unsqueeze(0), self.wrist_local_offset.unsqueeze(0)
        )[0]
        forward = math_utils.quat_apply(
            tool_quaternion.unsqueeze(0), self.wrist_local_forward.unsqueeze(0)
        )[0]
        self.wrist_camera.set_world_poses_from_view(
            eye.unsqueeze(0), (eye + forward).unsqueeze(0)
        )
        self.sim.render()
        self.external_camera.update(self.physics_dt)
        self.wrist_camera.update(self.physics_dt)
        return self._rgb(self.external_camera), self._rgb(self.wrist_camera)

    def before_step(
        self,
        robot: Articulation,
        cube: RigidObject,
        target_state: torch.Tensor,
        phase: str,
    ) -> None:
        # The simulator data buffers are stale immediately after the initial
        # direct state write, so the first valid sample is taken after one
        # complete stride of physics updates.
        if self.sim_step > 0 and self.sim_step % self.stride_steps == 0:
            observed_arm = robot.data.joint_pos[0, self.arm_ids].detach().cpu().numpy()
            observed_gripper = normalize_gripper(
                float(robot.data.joint_pos[0, self.gripper_master_id].item())
            )
            target_arm = target_state[0, self.arm_ids].detach().cpu().numpy()
            target_gripper = normalize_gripper(
                float(target_state[0, self.gripper_master_id].item())
            )
            action = np.concatenate([target_arm, [target_gripper]])
            cube_pose = torch.cat(
                [cube.data.root_pos_w[0], cube.data.root_quat_w[0]], dim=0
            ).detach().cpu().numpy()
            external_rgb = None
            wrist_rgb = None
            if self.external_camera is not None:
                external_rgb, wrist_rgb = self._render_images(robot, cube)
            self.recorder.add_frame(
                timestamp_s=self.sim_step * self.physics_dt,
                sim_step=self.sim_step,
                phase=phase,
                joint_position_rad=observed_arm,
                gripper_position=observed_gripper,
                action=action,
                cube_pose_wxyz=cube_pose,
                external_rgb=external_rgb,
                wrist_rgb=wrist_rgb,
            )
        self.sim_step += 1


def smooth_move(
    sim: SimulationContext,
    robot: Articulation,
    cube: RigidObject,
    state: torch.Tensor,
    joint_ids: list[int],
    start: np.ndarray,
    target: np.ndarray,
    steps: int,
    phase: str,
    capture: ExpertEpisodeCapture | None = None,
) -> None:
    print(f"PICK_PLACE_STAGE={phase}_START", flush=True)
    for step in range(steps):
        progress = (step + 1) / steps
        smooth = 3.0 * progress**2 - 2.0 * progress**3
        command = start + smooth * (target - start)
        state[:, joint_ids] = torch.as_tensor(command, device=sim.device, dtype=state.dtype)
        robot.set_joint_position_target(state)
        if capture is not None:
            capture.before_step(robot, cube, state, phase)
        robot.write_data_to_sim()
        cube.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        cube.update(sim.get_physics_dt())
        for contact_sensor in CONTACT_SENSORS.values():
            contact_sensor.update(sim.get_physics_dt())
    print(f"PICK_PLACE_STAGE={phase}_DONE", flush=True)


def hold(
    sim: SimulationContext,
    robot: Articulation,
    cube: RigidObject,
    state: torch.Tensor,
    steps: int,
    phase: str,
    capture: ExpertEpisodeCapture | None = None,
) -> None:
    for _ in range(steps):
        robot.set_joint_position_target(state)
        if capture is not None:
            capture.before_step(robot, cube, state, phase)
        robot.write_data_to_sim()
        cube.write_data_to_sim()
        sim.step(render=False)
        robot.update(sim.get_physics_dt())
        cube.update(sim.get_physics_dt())
        for contact_sensor in CONTACT_SENSORS.values():
            contact_sensor.update(sim.get_physics_dt())


def contact_force_statistics(contact_sensor: ContactSensor, recent_steps: int = 60) -> dict[str, float]:
    """Return peak, current, and recent sustained cube-contact force magnitudes."""

    current = contact_sensor.data.force_matrix_w
    history = contact_sensor.data.force_matrix_w_history
    if current is None or history is None:
        return {"peak_n": 0.0, "current_n": 0.0, "recent_mean_n": 0.0}
    current_n = float(torch.linalg.vector_norm(current, dim=-1).max())
    history_norm = torch.linalg.vector_norm(history, dim=-1)
    peak_n = float(history_norm.max())
    recent = history_norm[0, : min(recent_steps, history_norm.shape[1])].reshape(
        min(recent_steps, history_norm.shape[1]), -1
    )
    recent_mean_n = float(recent.max(dim=1).values.mean())
    return {"peak_n": peak_n, "current_n": current_n, "recent_mean_n": recent_mean_n}


def spawn_platform(
    path: str,
    position: np.ndarray,
    size: tuple[float, float, float],
    color: tuple[float, float, float],
    orientation: tuple[float, float, float, float] | None = None,
) -> None:
    cfg = sim_utils.CuboidCfg(
        size=size,
        collision_props=sim_utils.CollisionPropertiesCfg(),
        visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=color),
        physics_material=sim_utils.RigidBodyMaterialCfg(
            static_friction=1.0,
            dynamic_friction=0.8,
            restitution=0.0,
            friction_combine_mode="max",
        ),
    )
    kwargs = {"translation": tuple(position)}
    if orientation is not None:
        kwargs["orientation"] = orientation
    cfg.func(path, cfg, **kwargs)


def main() -> int:
    usd = args.usd.expanduser().resolve()
    urdf = args.urdf.expanduser().resolve()
    description = args.description.expanduser().resolve()
    output = args.output.expanduser().resolve()
    missing = [str(path) for path in (usd, urdf, description) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing required files: {missing}")
    if abs(args.transfer_joint_1_rad) < 0.5 or abs(args.transfer_joint_1_rad) > 1.2:
        raise ValueError("--transfer-joint-1-rad must have magnitude between 0.5 and 1.2")
    if not 0.0 <= args.robot_base_z_m <= 0.8:
        raise ValueError("--robot-base-z-m must be between 0 and 0.8")
    if min(args.arm_effort_limit_sim, args.arm_stiffness, args.arm_damping) <= 0.0:
        raise ValueError("arm actuator effort, stiffness, and damping must be positive")
    if min(args.gripper_effort_limit_sim, args.gripper_stiffness, args.gripper_damping) <= 0.0:
        raise ValueError("gripper actuator effort, stiffness, and damping must be positive")
    if not 0.1 <= args.gripper_close_target_rad <= 1.0:
        raise ValueError("--gripper-close-target-rad must be between 0.1 and 1.0")
    if not 0.01 <= args.pregrasp_distance_m <= 0.10:
        raise ValueError("--pregrasp-distance-m must be between 0.01 and 0.10")
    if abs(args.grasp_world_offset_x_m) > 0.08:
        raise ValueError("--grasp-world-offset-x-m must be between -0.08 and 0.08")
    if abs(args.grasp_world_offset_z_m) > 0.08:
        raise ValueError("--grasp-world-offset-z-m must be between -0.08 and 0.08")
    if abs(args.top_down_yaw_rad) > np.pi:
        raise ValueError("--top-down-yaw-rad must be between -pi and pi")
    if not 0.0 <= args.top_down_tilt_rad <= np.deg2rad(70.0):
        raise ValueError("--top-down-tilt-rad must be between 0 and 70 degrees")
    if not 1 <= args.top_down_ik_multistart <= 512:
        raise ValueError("--top-down-ik-multistart must be between 1 and 512")
    if not 0.0 <= args.top_down_blend <= 1.0:
        raise ValueError("--top-down-blend must be between 0 and 1")
    if not 0.02 <= args.cartesian_lift_height_m <= 0.15:
        raise ValueError("--cartesian-lift-height-m must be between 0.02 and 0.15")
    if not 0.03 <= args.release_clearance_m <= 0.20:
        raise ValueError("--release-clearance-m must be between 0.03 and 0.20")
    if not 0.0 <= args.release_separation_assist_m <= 0.20:
        raise ValueError("--release-separation-assist-m must be between 0.0 and 0.20")
    if not 0.03 <= args.place_descent_distance_m <= 0.13:
        raise ValueError("--place-descent-distance-m must be between 0.03 and 0.13")
    if not 30 <= args.place_waypoint_steps <= 240:
        raise ValueError("--place-waypoint-steps must be between 30 and 240")
    if not 1 <= args.record_stride_steps <= 240:
        raise ValueError("--record-stride-steps must be between 1 and 240")
    if not args.episode_prompt.strip():
        raise ValueError("--episode-prompt must not be empty")
    if args.record_episode_dir is not None and (
        args.diagnose_approach_only or args.diagnose_kinematics_only
    ):
        raise ValueError("episode recording is available only for a complete pick-and-place run")
    if args.record_images and args.record_episode_dir is None:
        raise ValueError("--record-images requires --record-episode-dir")
    if args.record_images and not getattr(args, "enable_cameras", False):
        raise ValueError("--record-images requires the AppLauncher flag --enable_cameras")

    grasp_arm = np.array([0.0, -0.55, 1.05, 0.0, 0.65, 0.0], dtype=np.float64)
    lift_arm = np.array([0.0, -0.73, 0.87, 0.0, 0.65, 0.0], dtype=np.float64)
    source_block_position = SOURCE_BLOCK_POSITION.copy()
    source_block_quaternion = np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
    if args.natural_source_gravity:
        source_block_position[2] = SOURCE_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
        source_block_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    robot_base_position = np.array([0.0, 0.0, args.robot_base_z_m], dtype=np.float64)
    source_block_position_base = source_block_position - robot_base_position
    lula = LulaKinematicsSolver(robot_description_path=str(description), urdf_path=str(urdf))
    grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
    if args.grasp_world_offset_x_m != 0.0 or args.grasp_world_offset_z_m != 0.0:
        offset_target_position = grasp_link_position + np.array(
            [args.grasp_world_offset_x_m, 0.0, args.grasp_world_offset_z_m], dtype=np.float64
        )
        offset_grasp_arm, success = lula.compute_inverse_kinematics(
            "link_6",
            offset_target_position,
            target_orientation=None,
            warm_start=grasp_arm,
            position_tolerance=1e-4,
        )
        if not success:
            raise RuntimeError("Lula failed to solve the requested grasp world offset")
        grasp_arm = np.asarray(offset_grasp_arm, dtype=np.float64)
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
    reference_block_from_link_local = grasp_link_rotation.T @ (source_block_position - grasp_link_position)
    top_down_ik_seed_index = None
    if args.grasp_orientation_mode == "top_down":
        calibrated_reference_link_position = (
            source_block_position_base
            - grasp_link_rotation @ reference_block_from_link_local
        )
        top_down_link_position, top_down_rotation, reference_block_from_link_local = (
            compute_top_down_link_pose(
                calibrated_reference_link_position,
                grasp_link_rotation,
                source_block_position_base,
                args.top_down_yaw_rad,
                args.top_down_tilt_rad,
                args.top_down_blend,
            )
        )
        joint_lower = np.array([-3.106, -2.2689, -2.356, -3.106, -2.234, -6.28])
        joint_upper = np.array([3.106, 2.2689, 2.356, 3.106, 2.234, 6.28])
        ik_seeds = [grasp_arm]
        if args.top_down_ik_multistart > 1:
            rng = np.random.default_rng(20260916)
            random_seeds = rng.uniform(
                joint_lower,
                joint_upper,
                size=(args.top_down_ik_multistart - 1, len(ARM_JOINTS)),
            )
            ik_seeds.extend(random_seeds)
        top_down_solution = None
        success = False
        for seed_index, ik_seed in enumerate(ik_seeds):
            candidate_solution, candidate_success = lula.compute_inverse_kinematics(
                "link_6",
                top_down_link_position,
                rot_matrix_to_quat(top_down_rotation),
                warm_start=np.asarray(ik_seed, dtype=np.float64),
                position_tolerance=1e-4,
                orientation_tolerance=1e-3,
            )
            if candidate_success:
                top_down_solution = candidate_solution
                top_down_ik_seed_index = seed_index
                success = True
                break
        if not success:
            print(
                "TOP_DOWN_IK_TARGET="
                f"position={top_down_link_position.tolist()} "
                f"yaw={args.top_down_yaw_rad:.6f} tilt={args.top_down_tilt_rad:.6f} "
                f"blend={args.top_down_blend:.6f} seeds={args.top_down_ik_multistart}",
                flush=True,
            )
            raise RuntimeError("Lula failed to solve the top-down grasp pose")
        grasp_arm = np.asarray(top_down_solution, dtype=np.float64)
        grasp_link_position, grasp_link_rotation = lula.compute_forward_kinematics("link_6", grasp_arm)
    if args.lift_mode == "cartesian_vertical":
        vertical_lift_target = grasp_link_position + np.array(
            [0.0, 0.0, args.cartesian_lift_height_m], dtype=np.float64
        )
        lift_arm_solution, success = lula.compute_inverse_kinematics(
            "link_6",
            vertical_lift_target,
            rot_matrix_to_quat(grasp_link_rotation),
            warm_start=grasp_arm,
            position_tolerance=1e-4,
            orientation_tolerance=1e-3,
        )
        if not success:
            raise RuntimeError("Lula failed to solve the local Cartesian vertical lift")
        lift_arm = np.asarray(lift_arm_solution, dtype=np.float64)
    lift_link_position, lift_link_rotation = lula.compute_forward_kinematics("link_6", lift_arm)
    expected_lift_translation = lift_link_position - grasp_link_position
    expected_source_lift_block_position = source_block_position + expected_lift_translation
    target_lift_arm = lift_arm.copy()
    target_lift_arm[0] = args.transfer_joint_1_rad
    transferred_link_position, transferred_link_rotation = lula.compute_forward_kinematics(
        "link_6", target_lift_arm
    )
    release_clear_arm = None
    if args.unassisted_release and not args.place_descent:
        release_clear_target = transferred_link_position + np.array(
            [0.0, 0.0, args.release_clearance_m], dtype=np.float64
        )
        release_clear_solution, success = lula.compute_inverse_kinematics(
            "link_6",
            release_clear_target,
            target_orientation=None,
            warm_start=target_lift_arm,
            position_tolerance=1e-4,
        )
        if not success:
            raise RuntimeError("Lula failed to solve the vertical release-clearance motion")
        release_clear_arm = np.asarray(release_clear_solution, dtype=np.float64)

    transfer_quaternion = np.array(
        [np.cos(args.transfer_joint_1_rad / 2.0), 0.0, 0.0, np.sin(args.transfer_joint_1_rad / 2.0)],
        dtype=np.float64,
    )
    target_release_position = rotate_about_z(expected_source_lift_block_position, args.transfer_joint_1_rad)
    target_block_position = target_release_position.copy()
    target_block_position[2] = TARGET_PLATFORM_TOP_Z + BLOCK_SIZE[2] / 2.0
    target_block_quaternion = quaternion_multiply_wxyz(transfer_quaternion, source_block_quaternion)
    target_platform_size = (
        TARGET_STRIP_SIZE if args.target_support_mode == "rotated_strip" else TARGET_PLATFORM_SIZE
    )
    target_platform_orientation = (
        tuple(transfer_quaternion) if args.target_support_mode == "rotated_strip" else None
    )
    target_platform_position = np.array(
        [
            target_block_position[0],
            target_block_position[1],
            TARGET_PLATFORM_TOP_Z - target_platform_size[2] / 2.0,
        ],
        dtype=np.float64,
    )
    place_waypoints = []
    if args.place_descent:
        place_waypoint_count = max(1, int(round(args.place_descent_distance_m / 0.01)))
        place_distances = np.linspace(0.01, args.place_descent_distance_m, place_waypoint_count)
        place_warm_start = lift_arm.copy()
        for distance in place_distances:
            place_link_target = lift_link_position - np.array(
                [0.0, 0.0, distance], dtype=np.float64
            )
            place_solution, success = lula.compute_inverse_kinematics(
                "link_6",
                place_link_target,
                rot_matrix_to_quat(lift_link_rotation),
                warm_start=place_warm_start,
                position_tolerance=1e-4,
                orientation_tolerance=1e-3,
            )
            if not success:
                raise RuntimeError(f"Lula failed to solve place waypoint at {distance:.3f} m")
            place_warm_start = np.asarray(place_solution, dtype=np.float64)
            rotated_place_solution = place_warm_start.copy()
            rotated_place_solution[0] += args.transfer_joint_1_rad - lift_arm[0]
            place_waypoints.append(rotated_place_solution)

    place_max_command_step_rad = None
    if place_waypoints:
        place_joint_sequence = np.vstack([target_lift_arm, *place_waypoints])
        place_max_command_step_rad = float(
            np.max(np.abs(np.diff(place_joint_sequence, axis=0)))
        )
    if args.diagnose_kinematics_only:
        diagnostic = {
            "status": "diagnostic",
            "simulation_only": True,
            "robot_base_position_m": robot_base_position.tolist(),
            "transfer_joint_1_rad": args.transfer_joint_1_rad,
            "grasp_orientation_mode": args.grasp_orientation_mode,
            "top_down_ik_seed_index": top_down_ik_seed_index,
            "grasp_arm_joint_position_rad": grasp_arm.tolist(),
            "lift_arm_joint_position_rad": lift_arm.tolist(),
            "target_lift_arm_joint_position_rad": target_lift_arm.tolist(),
            "place_waypoint_count": len(place_waypoints),
            "place_max_command_step_rad": place_max_command_step_rad,
            "place_ik_uses_base_rotation_symmetry": True,
            "place_waypoint_joint_position_rad": [item.tolist() for item in place_waypoints],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(diagnostic, indent=2), flush=True)
        return 0

    sim = SimulationContext(
        sim_utils.SimulationCfg(
            dt=1.0 / 240.0,
            device=args.device,
            physics_material=sim_utils.RigidBodyMaterialCfg(
                static_friction=1.5,
                dynamic_friction=1.2,
                restitution=0.0,
                friction_combine_mode="max",
            ),
        )
    )
    light_cfg = sim_utils.DomeLightCfg(intensity=2500.0, color=(0.8, 0.8, 0.8))
    light_cfg.func("/World/Light", light_cfg)
    if not args.diagnose_approach_only:
        spawn_platform(
            "/World/TargetPlatform",
            target_platform_position,
            target_platform_size,
            (0.12, 0.45, 0.20),
            target_platform_orientation,
        )
    if args.natural_source_gravity:
        source_platform_position = np.array(
            [
                source_block_position[0],
                source_block_position[1],
                SOURCE_PLATFORM_TOP_Z - SOURCE_PLATFORM_SIZE[2] / 2.0,
            ],
            dtype=np.float64,
        )
        spawn_platform(
            "/World/SourcePlatform", source_platform_position, SOURCE_PLATFORM_SIZE, (0.35, 0.35, 0.38)
        )
    target_platform_collision_apis = []
    for prim in get_current_stage().Traverse():
        if str(prim.GetPath()).startswith("/World/TargetPlatform") and prim.HasAPI(UsdPhysics.CollisionAPI):
            collision_api = UsdPhysics.CollisionAPI(prim)
            collision_api.CreateCollisionEnabledAttr().Set(False)
            target_platform_collision_apis.append(collision_api)

    robot = Articulation(
        ArticulationCfg(
            prim_path="/World/Robot",
            spawn=sim_utils.UsdFileCfg(
                usd_path=str(usd),
                activate_contact_sensors=True,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False),
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                    enabled_self_collisions=False,
                    solver_position_iteration_count=64,
                    solver_velocity_iteration_count=4,
                ),
            ),
            init_state=ArticulationCfg.InitialStateCfg(
                pos=tuple(robot_base_position),
                joint_pos={"joint_.*": 0.0, "tool_.*": 0.0},
            ),
            actuators={
                "arm": ImplicitActuatorCfg(
                    joint_names_expr=["joint_[1-6]"],
                    effort_limit_sim=args.arm_effort_limit_sim,
                    velocity_limit_sim=1.0,
                    stiffness=args.arm_stiffness,
                    damping=args.arm_damping,
                ),
                "gripper": ImplicitActuatorCfg(
                    joint_names_expr=["tool_.*"],
                    effort_limit_sim=args.gripper_effort_limit_sim,
                    velocity_limit_sim=1.0,
                    stiffness=args.gripper_stiffness,
                    damping=args.gripper_damping,
                ),
            },
        )
    )
    cube = RigidObject(
        RigidObjectCfg(
            prim_path="/World/Cube",
            spawn=sim_utils.CuboidCfg(
                size=BLOCK_SIZE,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=not args.natural_source_gravity,
                    solver_position_iteration_count=32,
                    solver_velocity_iteration_count=4,
                    max_depenetration_velocity=1.0,
                ),
                mass_props=sim_utils.MassPropertiesCfg(mass=BLOCK_MASS_KG),
                collision_props=sim_utils.CollisionPropertiesCfg(),
                visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.10, 0.08)),
                physics_material=sim_utils.RigidBodyMaterialCfg(
                    static_friction=1.5,
                    dynamic_friction=1.2,
                    restitution=0.0,
                    friction_combine_mode="max",
                ),
            ),
            init_state=RigidObjectCfg.InitialStateCfg(
                pos=tuple(source_block_position),
                rot=tuple(source_block_quaternion),
            ),
        )
    )
    external_camera = None
    wrist_camera = None
    if args.record_images:
        external_camera = Camera(
            CameraCfg(
                prim_path="/World/ExternalCamera",
                update_period=0.0,
                height=480,
                width=640,
                data_types=["rgb"],
                spawn=sim_utils.PinholeCameraCfg(
                    focal_length=24.0,
                    focus_distance=2.0,
                    horizontal_aperture=20.955,
                    clipping_range=(0.01, 10.0),
                ),
            )
        )
        wrist_camera = Camera(
            CameraCfg(
                prim_path="/World/WristCamera",
                update_period=0.0,
                height=480,
                width=640,
                data_types=["rgb"],
                spawn=sim_utils.PinholeCameraCfg(
                    focal_length=18.0,
                    focus_distance=1.0,
                    horizontal_aperture=20.955,
                    clipping_range=(0.01, 10.0),
                ),
            )
        )
    PhysxSchema.PhysxContactReportAPI.Apply(get_current_stage().GetPrimAtPath("/World/Cube"))
    CONTACT_SENSORS.update(
        {
            body_path.rsplit("/", 1)[-1]: ContactSensor(
                ContactSensorCfg(
                    prim_path=body_path,
                    update_period=0.0,
                    history_length=400,
                    filter_prim_paths_expr=["/World/Cube"],
                )
            )
            for body_path in sorted(MOVING_GRIPPER_BODY_PATHS)
        }
    )

    isolated_paths = []
    approach_arm_gravity_apis = []
    for prim in get_current_stage().Traverse():
        path = str(prim.GetPath())
        if (
            (args.disable_arm_gravity_during_approach or args.disable_arm_gravity_through_transport)
            and path in ARM_BODY_PATHS
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
        ):
            rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
            rigid_body_api.CreateDisableGravityAttr().Set(True)
            approach_arm_gravity_apis.append(rigid_body_api)
        if (
            not args.enable_moving_gripper_gravity
            and path in MOVING_GRIPPER_BODY_PATHS
            and prim.HasAPI(UsdPhysics.RigidBodyAPI)
        ):
            PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateDisableGravityAttr().Set(True)
            isolated_paths.append(path)
    cube_prim = get_current_stage().GetPrimAtPath("/World/Cube")
    cube_rigid_body_api = PhysxSchema.PhysxRigidBodyAPI.Apply(cube_prim)
    cube_rigid_body_api.CreateDisableGravityAttr().Set(not args.natural_source_gravity)
    cube_collision_apis = []
    for prim in get_current_stage().Traverse():
        if str(prim.GetPath()).startswith("/World/Cube") and prim.HasAPI(UsdPhysics.CollisionAPI):
            collision_api = UsdPhysics.CollisionAPI(prim)
            cube_collision_apis.append(collision_api)
            if args.collision_bypass_during_approach:
                collision_api.CreateCollisionEnabledAttr().Set(False)
    if not cube_collision_apis:
        raise RuntimeError("no CollisionAPI prim found below /World/Cube")

    sim.reset()
    robot.reset()
    cube.reset()
    if external_camera is not None:
        scene_center = 0.5 * (source_block_position + target_block_position)
        external_eye = torch.as_tensor(
            scene_center + np.array([0.70, 0.70, 0.45]),
            device=sim.device,
            dtype=torch.float32,
        ).unsqueeze(0)
        external_target = torch.as_tensor(
            scene_center,
            device=sim.device,
            dtype=torch.float32,
        ).unsqueeze(0)
        external_camera.set_world_poses_from_view(external_eye, external_target)
    joint_names = list(robot.data.joint_names)
    arm_ids = [joint_names.index(name) for name in ARM_JOINTS]
    gripper_ids = [index for index, name in enumerate(joint_names) if name.startswith("tool_")]
    if GRIPPER_MASTER_JOINT not in joint_names:
        raise RuntimeError(f"missing gripper master joint {GRIPPER_MASTER_JOINT}")
    episode_recorder = None
    episode_capture = None
    if args.record_episode_dir is not None:
        episode_recorder = EpisodeRecorder(
            output_dir=args.record_episode_dir.expanduser().resolve(),
            prompt=args.episode_prompt,
            control_hz=1.0 / (sim.get_physics_dt() * args.record_stride_steps),
            metadata={
                "simulation_only": True,
                "expert": "scripted_rm65_pick_place",
                "images_recorded": args.record_images,
                "robot_base_position_m": robot_base_position.tolist(),
                "source_block_position_m": source_block_position.tolist(),
                "target_block_position_m": target_block_position.tolist(),
                "transfer_joint_1_rad": args.transfer_joint_1_rad,
                "record_stride_steps": args.record_stride_steps,
            },
        )
        episode_capture = ExpertEpisodeCapture(
            recorder=episode_recorder,
            arm_ids=arm_ids,
            gripper_master_id=joint_names.index(GRIPPER_MASTER_JOINT),
            stride_steps=args.record_stride_steps,
            physics_dt=sim.get_physics_dt(),
            sim=sim,
            external_camera=external_camera,
            wrist_camera=wrist_camera,
            wrist_tool_body_id=(
                list(robot.data.body_names).index("tool_base_link")
                if args.record_images
                else None
            ),
        )

    grasp_link_quaternion = rot_matrix_to_quat(grasp_link_rotation)
    outward_direction = (
        np.array([0.0, 0.0, -1.0], dtype=np.float64)
        if args.grasp_orientation_mode == "top_down"
        else quaternion_to_matrix_wxyz(
            np.asarray(SOURCE_BLOCK_QUATERNION_WXYZ, dtype=np.float64)
        )[:, 0]
    )
    waypoint_count = max(1, int(round(args.pregrasp_distance_m / 0.01)))
    retreat_distances = np.linspace(0.01, args.pregrasp_distance_m, waypoint_count)
    retreat_waypoints = []
    warm_start = grasp_arm.copy()
    for distance in retreat_distances:
        waypoint_position = grasp_link_position - distance * outward_direction
        waypoint_q, success = lula.compute_inverse_kinematics(
            "link_6",
            waypoint_position,
            grasp_link_quaternion,
            warm_start=warm_start,
            position_tolerance=1e-4,
            orientation_tolerance=1e-3,
        )
        if not success:
            raise RuntimeError(f"Lula failed to solve Cartesian retreat waypoint at {distance:.3f} m")
        warm_start = np.asarray(waypoint_q, dtype=np.float64)
        retreat_waypoints.append(warm_start.copy())
    pregrasp_arm = grasp_arm.copy() if args.initialize_at_grasp else retreat_waypoints[-1]

    state = robot.data.default_joint_pos.clone()
    state[:, arm_ids] = torch.as_tensor(pregrasp_arm, device=sim.device, dtype=state.dtype)
    state[:, gripper_ids] = 0.0
    robot.write_joint_state_to_sim(state, torch.zeros_like(state))
    cube_pose = cube.data.default_root_state[:, :7].clone()
    cube_pose[:, :3] = torch.as_tensor(source_block_position, device=sim.device, dtype=cube_pose.dtype)
    cube_pose[:, 3:7] = torch.as_tensor(
        source_block_quaternion, device=sim.device, dtype=cube_pose.dtype
    )
    cube.write_root_pose_to_sim(cube_pose)
    cube.write_root_velocity_to_sim(torch.zeros_like(cube.data.root_vel_w))
    hold(
        sim,
        robot,
        cube,
        state,
        60 if args.initialize_at_grasp else 240,
        "SOURCE_SETTLE",
        episode_capture,
    )
    settled_source_position = cube.data.root_pos_w[0].clone()
    settled_source_quaternion = cube.data.root_quat_w[0].clone()
    print("PICK_PLACE_STAGE=SOURCE_SETTLED", flush=True)

    approach_waypoints = [] if args.initialize_at_grasp else list(reversed(retreat_waypoints[:-1])) + [grasp_arm]
    previous_waypoint = pregrasp_arm
    for index, waypoint in enumerate(approach_waypoints, start=1):
        smooth_move(
            sim,
            robot,
            cube,
            state,
            arm_ids,
            previous_waypoint,
            waypoint,
            120,
            f"APPROACH_{index}",
            episode_capture,
        )
        previous_waypoint = waypoint
    if args.collision_bypass_during_approach:
        hold(sim, robot, cube, state, 240, "PRE_COLLISION_RESTORE_HOLD", episode_capture)
        pre_restore_arm_error = float(
            np.max(np.abs(robot.data.joint_pos[0, arm_ids].detach().cpu().numpy() - grasp_arm))
        )
        print(f"PICK_PLACE_PRE_RESTORE_ARM_ERROR_RAD={pre_restore_arm_error:.9f}", flush=True)
    if args.collision_bypass_during_approach:
        for collision_api in cube_collision_apis:
            collision_api.CreateCollisionEnabledAttr().Set(True)
        print("PICK_PLACE_STAGE=CUBE_COLLISION_RESTORED", flush=True)
    if not args.initialize_at_grasp:
        hold(sim, robot, cube, state, 240, "GRASP_HOLD", episode_capture)
    actual_approach_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
    open_l2_midpoint = 0.5 * (
        tip_world_position(robot, "tool_l_2") + tip_world_position(robot, "tool_r_2")
    )
    open_midpoint_to_block = float(
        torch.linalg.vector_norm(open_l2_midpoint - cube.data.root_pos_w[0])
    )
    open_midpoint_world = open_l2_midpoint.detach().cpu().numpy()
    open_midpoint_minus_block = open_midpoint_world - cube.data.root_pos_w[0].detach().cpu().numpy()
    open_pad_center_world_by_body = {
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
    }
    open_pad_center_minus_block_by_body = {
        body_name: (
            np.asarray(world_position, dtype=np.float64)
            - cube.data.root_pos_w[0].detach().cpu().numpy()
        ).tolist()
        for body_name, world_position in open_pad_center_world_by_body.items()
    }
    print(
        "PICK_PLACE_APPROACH="
        + json.dumps(
            {
                "max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
                "l2_midpoint_to_block_center_m": open_midpoint_to_block,
                "l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
            }
        ),
        flush=True,
    )
    close_start = np.zeros(len(gripper_ids), dtype=np.float64)
    close_target = np.full(len(gripper_ids), args.gripper_close_target_rad, dtype=np.float64)
    smooth_move(
        sim,
        robot,
        cube,
        state,
        gripper_ids,
        close_start,
        close_target,
        180,
        "CLOSE",
        episode_capture,
    )
    hold(sim, robot, cube, state, 120, "CLOSE_HOLD", episode_capture)
    closed_position = cube.data.root_pos_w[0].clone()
    closed_link_6_position = body_world_position(robot, "link_6").clone()
    closed_pad_center_world_by_body = {
        body_name: local_point_world_position(robot, body_name, local_position).detach().cpu().tolist()
        for body_name, local_position in PAD_LOCAL_CENTERS.items()
    }
    closed_pad_center_minus_block_by_body = {
        body_name: (np.asarray(world_position, dtype=np.float64) - closed_position.detach().cpu().numpy()).tolist()
        for body_name, world_position in closed_pad_center_world_by_body.items()
    }
    closed_l2_gap = float(
        torch.linalg.vector_norm(
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
        )
    )
    closed_gripper_joint_position = robot.data.joint_pos[0, gripper_ids].clone()
    close_contact_force_statistics_by_body = {}
    for body_name, contact_sensor in CONTACT_SENSORS.items():
        close_contact_force_statistics_by_body[body_name] = contact_force_statistics(contact_sensor)
    close_contact_force_by_body_n = {
        body_name: statistics["peak_n"]
        for body_name, statistics in close_contact_force_statistics_by_body.items()
    }
    close_current_contact_force_by_body_n = {
        body_name: statistics["current_n"]
        for body_name, statistics in close_contact_force_statistics_by_body.items()
    }
    close_recent_mean_contact_force_by_body_n = {
        body_name: statistics["recent_mean_n"]
        for body_name, statistics in close_contact_force_statistics_by_body.items()
    }
    close_current_contact_force_vector_by_body_n = {}
    for body_name, contact_sensor in CONTACT_SENSORS.items():
        current = contact_sensor.data.force_matrix_w
        close_current_contact_force_vector_by_body_n[body_name] = (
            [0.0, 0.0, 0.0]
            if current is None
            else current.reshape(-1, 3).sum(dim=0).detach().cpu().tolist()
        )
    close_left_finger_contact_force_n = max(
        close_contact_force_by_body_n[name] for name in ("tool_l_1", "tool_l_2", "tool_l_3")
    )
    close_right_finger_contact_force_n = max(
        close_contact_force_by_body_n[name] for name in ("tool_r_1", "tool_r_2", "tool_r_3")
    )
    print(
        "PICK_PLACE_CLOSE_CONTACT="
        + json.dumps(
            {
                "left_finger_force_n": close_left_finger_contact_force_n,
                "right_finger_force_n": close_right_finger_contact_force_n,
                "current_force_by_body_n": close_current_contact_force_by_body_n,
                "recent_mean_force_by_body_n": close_recent_mean_contact_force_by_body_n,
                "current_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
            }
        ),
        flush=True,
    )

    if args.diagnose_approach_only:
        diagnostic = {
            "status": "diagnostic",
            "simulation_only": True,
            "collision_bypass_during_approach": args.collision_bypass_during_approach,
            "initialized_at_grasp": args.initialize_at_grasp,
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
            "natural_source_gravity": args.natural_source_gravity,
            "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
            "arm_actuator": {
                "effort_limit_sim": args.arm_effort_limit_sim,
                "stiffness": args.arm_stiffness,
                "damping": args.arm_damping,
            },
            "gripper_actuator": {
                "effort_limit_sim": args.gripper_effort_limit_sim,
                "stiffness": args.gripper_stiffness,
                "damping": args.gripper_damping,
                "close_target_rad": args.gripper_close_target_rad,
            },
            "pregrasp_distance_m": args.pregrasp_distance_m,
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
            "robot_base_position_m": robot_base_position.tolist(),
            "grasp_orientation_mode": args.grasp_orientation_mode,
            "top_down_yaw_rad": args.top_down_yaw_rad,
            "top_down_tilt_rad": args.top_down_tilt_rad,
            "top_down_ik_multistart": args.top_down_ik_multistart,
            "top_down_ik_seed_index": top_down_ik_seed_index,
            "top_down_blend": args.top_down_blend,
            "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
            "lift_mode": args.lift_mode,
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
            "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
            "closed_position_m": closed_position.detach().cpu().tolist(),
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
            "approach_actual_arm_joint_position_rad": actual_approach_arm.tolist(),
            "approach_target_arm_joint_position_rad": grasp_arm.tolist(),
            "cartesian_retreat_distances_m": retreat_distances.tolist(),
            "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
            "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
            "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
            "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
            "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
            "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
            "closed_l2_tip_gap_m": closed_l2_gap,
            "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(diagnostic, indent=2), flush=True)
        return 0

    if not args.disable_arm_gravity_through_transport:
        for rigid_body_api in approach_arm_gravity_apis:
            rigid_body_api.CreateDisableGravityAttr().Set(False)
    if approach_arm_gravity_apis and not args.disable_arm_gravity_through_transport:
        print("PICK_PLACE_STAGE=ARM_GRAVITY_RESTORED", flush=True)
    cube_rigid_body_api.CreateDisableGravityAttr().Set(False)
    smooth_move(
        sim, robot, cube, state, arm_ids, grasp_arm, lift_arm, 240, "LIFT", episode_capture
    )
    hold(sim, robot, cube, state, 120, "LIFT_HOLD", episode_capture)
    lifted_position = cube.data.root_pos_w[0].clone()
    lifted_link_6_position = body_world_position(robot, "link_6").clone()
    actual_lift_link_translation = lifted_link_6_position - closed_link_6_position
    actual_lift_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
    lift_height_after_attempt = float((lifted_position[2] - closed_position[2]).item())
    if lift_height_after_attempt <= 0.02:
        failed_lift_report = {
            "status": "fail",
            "failure_stage": "lift",
            "simulation_only": True,
            "pi05_used": False,
            "real_robot_command_sent": False,
            "natural_source_gravity": args.natural_source_gravity,
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
            "pregrasp_distance_m": args.pregrasp_distance_m,
            "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
            "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
            "lift_mode": args.lift_mode,
            "cartesian_lift_height_m": args.cartesian_lift_height_m,
            "gripper_actuator": {
                "effort_limit_sim": args.gripper_effort_limit_sim,
                "stiffness": args.gripper_stiffness,
                "damping": args.gripper_damping,
                "close_target_rad": args.gripper_close_target_rad,
            },
            "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
            "settled_source_position_m": settled_source_position.detach().cpu().tolist(),
            "closed_position_m": closed_position.detach().cpu().tolist(),
            "lifted_position_m": lifted_position.detach().cpu().tolist(),
            "block_lift_height_m": lift_height_after_attempt,
            "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
            "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
            "close_contact_force_by_body_n": close_contact_force_by_body_n,
            "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
            "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
            "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
            "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
            "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
            "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
            "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
            "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
            "lift_target_arm_joint_position_rad": lift_arm.tolist(),
            "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
            "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
            "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
            "reason": "The block did not clear the source support after the commanded lift.",
        }
        if episode_recorder is not None:
            episode_recorder.metadata["task_success"] = False
            episode_recorder.metadata["failure_stage"] = "lift"
            episode_manifest = episode_recorder.save()
            episode_validation = validate_episode(
                episode_recorder.output_dir, require_images=args.record_images
            )
            failed_lift_report["expert_episode"] = {
                "directory": str(episode_recorder.output_dir),
                "frame_count": episode_manifest["frame_count"],
                "validation": episode_validation,
                "training_ready": False,
            }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(failed_lift_report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(failed_lift_report, indent=2), flush=True)
        print("RM65_PICK_PLACE_BASELINE=FAIL_AT_LIFT", flush=True)
        return 1

    smooth_move(
        sim,
        robot,
        cube,
        state,
        arm_ids,
        lift_arm,
        target_lift_arm,
        360,
        "TRANSFER",
        episode_capture,
    )
    if args.target_collision_enable_stage == "after_transfer":
        for collision_api in target_platform_collision_apis:
            collision_api.CreateCollisionEnabledAttr().Set(True)
        if target_platform_collision_apis:
            print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED", flush=True)
            hold(sim, robot, cube, state, 120, "TARGET_COLLISION_HOLD", episode_capture)
    pre_place_position = cube.data.root_pos_w[0].clone()
    pre_place_link_6_position = body_world_position(robot, "link_6").clone()
    place_actual_arm = None
    place_actual_link_6_position = None
    place_commanded_link_6_position = None
    release_start_arm = target_lift_arm
    if args.place_descent:
        previous_place_waypoint = target_lift_arm
        for index, waypoint in enumerate(place_waypoints, start=1):
            smooth_move(
                sim,
                robot,
                cube,
                state,
                arm_ids,
                previous_place_waypoint,
                waypoint,
                args.place_waypoint_steps,
                f"PLACE_DESCENT_{index}",
                episode_capture,
            )
            previous_place_waypoint = waypoint
        hold(sim, robot, cube, state, 120, "PLACE_HOLD", episode_capture)
        release_start_arm = place_waypoints[-1]
        place_actual_arm = robot.data.joint_pos[0, arm_ids].detach().cpu().numpy()
        place_actual_link_6_position = body_world_position(robot, "link_6").clone()
        place_commanded_link_6_position, _ = lula.compute_forward_kinematics(
            "link_6", place_waypoints[-1]
        )
        place_commanded_link_6_position += robot_base_position
        if args.target_collision_enable_stage == "after_place_descent":
            for collision_api in target_platform_collision_apis:
                collision_api.CreateCollisionEnabledAttr().Set(True)
            if target_platform_collision_apis:
                print("PICK_PLACE_STAGE=TARGET_PLATFORM_COLLISION_ENABLED_AFTER_PLACE", flush=True)
                hold(
                    sim,
                    robot,
                    cube,
                    state,
                    120,
                    "TARGET_COLLISION_AFTER_PLACE_HOLD",
                    episode_capture,
                )
    pre_release_position = cube.data.root_pos_w[0].clone()

    smooth_move(
        sim,
        robot,
        cube,
        state,
        gripper_ids,
        close_target,
        close_start,
        180,
        "OPEN",
        episode_capture,
    )
    if args.unassisted_release:
        print("PICK_PLACE_STAGE=UNASSISTED_RELEASE", flush=True)
        hold(sim, robot, cube, state, 240, "RELEASE_SETTLE", episode_capture)
        released_position = cube.data.root_pos_w[0].clone()
        if args.place_descent:
            retreat_place_waypoints = list(reversed(place_waypoints[:-1])) + [target_lift_arm]
            previous_place_waypoint = release_start_arm
            for index, waypoint in enumerate(retreat_place_waypoints, start=1):
                smooth_move(
                    sim,
                    robot,
                    cube,
                    state,
                    arm_ids,
                    previous_place_waypoint,
                    waypoint,
                    60,
                    f"RETREAT_{index}",
                    episode_capture,
                )
                previous_place_waypoint = waypoint
        else:
            assert release_clear_arm is not None
            smooth_move(
                sim,
                robot,
                cube,
                state,
                arm_ids,
                release_start_arm,
                release_clear_arm,
                240,
                "RETREAT",
                episode_capture,
            )
        hold(sim, robot, cube, state, 480, "FINAL_SETTLE", episode_capture)
        final_position = cube.data.root_pos_w[0].clone()
    else:
        target_clear_arm = target_lift_arm.copy()
        target_clear_arm[1] -= 0.10
        target_clear_arm[2] -= 0.10
        release_pose = cube.data.root_state_w[:, :7].clone()
        release_pose[:, 2] -= args.release_separation_assist_m
        cube.write_root_pose_to_sim(release_pose)
        release_velocity = torch.zeros_like(cube.data.root_vel_w)
        release_velocity[:, 2] = -RELEASE_DOWNWARD_SPEED_M_S
        cube.write_root_velocity_to_sim(release_velocity)
        print("PICK_PLACE_STAGE=RELEASE_ASSIST_APPLIED", flush=True)
        hold(sim, robot, cube, state, 480, "ASSISTED_RELEASE_SETTLE", episode_capture)
        released_position = cube.data.root_pos_w[0].clone()
        smooth_move(
            sim,
            robot,
            cube,
            state,
            arm_ids,
            target_lift_arm,
            target_clear_arm,
            240,
            "RETREAT",
            episode_capture,
        )
        hold(sim, robot, cube, state, 120, "FINAL_SETTLE", episode_capture)
        final_position = cube.data.root_pos_w[0].clone()

    settled_source_np = settled_source_position.detach().cpu().numpy()
    closed_np = closed_position.detach().cpu().numpy()
    lifted_np = lifted_position.detach().cpu().numpy()
    pre_release_np = pre_release_position.detach().cpu().numpy()
    released_np = released_position.detach().cpu().numpy()
    final_np = final_position.detach().cpu().numpy()
    source_to_target_distance = float(np.linalg.norm(target_block_position[:2] - source_block_position[:2]))
    lift_height = float(lifted_np[2] - closed_np[2])
    final_target_xy_error = float(np.linalg.norm(final_np[:2] - target_block_position[:2]))
    final_target_position_error = float(np.linalg.norm(final_np - target_block_position))
    release_drift = float(np.linalg.norm(final_np - released_np))
    final_l2_tip_gap = float(
        torch.linalg.vector_norm(
            tip_world_position(robot, "tool_l_2") - tip_world_position(robot, "tool_r_2")
        )
    )
    all_states_finite = bool(
        torch.isfinite(robot.data.joint_pos).all().item()
        and torch.isfinite(cube.data.root_state_w).all().item()
    )
    passed = (
        all_states_finite
        and source_to_target_distance > 0.12
        and lift_height > 0.02
        and final_target_xy_error < 0.05
        and final_target_position_error < 0.05
        and release_drift < 0.02
        and float(robot.data.joint_pos[0, gripper_ids].max()) < 0.12
        and final_l2_tip_gap > 0.06
    )
    unassisted_full_task_complete = bool(
        passed
        and args.unassisted_release
        and args.place_descent
        and args.natural_source_gravity
        and args.enable_moving_gripper_gravity
        and not args.collision_bypass_during_approach
        and not args.initialize_at_grasp
        and not args.disable_arm_gravity_during_approach
        and not args.disable_arm_gravity_through_transport
    )
    expert_episode_report = None
    if episode_recorder is not None:
        episode_recorder.metadata["task_success"] = passed
        episode_recorder.metadata[
            "unassisted_full_task_complete"
        ] = unassisted_full_task_complete
        episode_manifest = episode_recorder.save()
        episode_validation = validate_episode(
            episode_recorder.output_dir, require_images=args.record_images
        )
        if episode_validation["status"] != "pass":
            raise RuntimeError(f"recorded episode failed validation: {episode_validation}")
        expert_episode_report = {
            "directory": str(episode_recorder.output_dir),
            "format": episode_manifest["format"],
            "frame_count": episode_manifest["frame_count"],
            "control_hz": episode_manifest["control_hz"],
            "validation": episode_validation,
            "training_ready": bool(passed and args.record_images),
            "training_blocker": (
                None
                if args.record_images
                else "external and wrist RGB streams were not recorded"
            ),
        }
    report = {
        "status": "pass" if passed else "fail",
        "simulation_only": True,
        "pi05_used": False,
        "expert": (
            "scripted initialized-grasp and joint-space transport baseline; pi0.5 is not used"
            if args.initialize_at_grasp
            else "scripted Cartesian-approach and joint-space transport baseline; pi0.5 is not used"
        ),
        "task": (
            (
                "approach, close, lift, transfer, Cartesian place descent, unassisted release, and retreat"
                if args.place_descent
                else "approach, close, lift, transfer, unassisted release, and vertical clearance"
            )
            if args.unassisted_release
            else "approach, close, lift, transfer, assisted release onto a platform, and retreat"
        ),
        "real_robot_command_sent": False,
        "expert_episode": expert_episode_report,
        "unassisted_full_task_complete": unassisted_full_task_complete,
        "transfer_joint_1_rad": args.transfer_joint_1_rad,
        "collision_bypass_during_approach": args.collision_bypass_during_approach,
        "initialized_at_grasp": args.initialize_at_grasp,
        "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
        "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
        "natural_source_gravity": args.natural_source_gravity,
        "arm_actuator": {
            "effort_limit_sim": args.arm_effort_limit_sim,
            "stiffness": args.arm_stiffness,
            "damping": args.arm_damping,
        },
        "gripper_actuator": {
            "effort_limit_sim": args.gripper_effort_limit_sim,
            "stiffness": args.gripper_stiffness,
            "damping": args.gripper_damping,
            "close_target_rad": args.gripper_close_target_rad,
        },
        "pregrasp_distance_m": args.pregrasp_distance_m,
        "grasp_world_offset_x_m": args.grasp_world_offset_x_m,
        "grasp_world_offset_z_m": args.grasp_world_offset_z_m,
        "robot_base_position_m": robot_base_position.tolist(),
        "grasp_orientation_mode": args.grasp_orientation_mode,
        "top_down_yaw_rad": args.top_down_yaw_rad,
        "top_down_tilt_rad": args.top_down_tilt_rad,
        "top_down_ik_multistart": args.top_down_ik_multistart,
        "top_down_ik_seed_index": top_down_ik_seed_index,
        "top_down_blend": args.top_down_blend,
        "reference_block_from_link_local_m": reference_block_from_link_local.tolist(),
        "lift_mode": args.lift_mode,
        "cartesian_lift_height_m": args.cartesian_lift_height_m,
        "development_assistance": {
            "initialized_at_grasp": args.initialize_at_grasp,
            "arm_gravity_disabled_during_approach": args.disable_arm_gravity_during_approach,
            "arm_gravity_disabled_through_transport": args.disable_arm_gravity_through_transport,
            "source_block_gravity_disabled_until_close": not args.natural_source_gravity,
            "target_platform_collision_enable_stage": args.target_collision_enable_stage,
            "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
            "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
        },
        "block_mass_kg": BLOCK_MASS_KG,
        "block_size_m": list(BLOCK_SIZE),
        "moving_gripper_gravity_disabled": not args.enable_moving_gripper_gravity,
        "gravity_disabled_body_paths": isolated_paths,
        "source_block_position_m": source_block_position.tolist(),
        "target_block_position_m": target_block_position.tolist(),
        "expected_lift_translation_from_fk_m": expected_lift_translation.tolist(),
        "expected_source_lift_block_position_m": expected_source_lift_block_position.tolist(),
        "expected_release_position_before_drop_m": target_release_position.tolist(),
        "source_block_quaternion_wxyz": source_block_quaternion.tolist(),
        "target_block_quaternion_wxyz": target_block_quaternion.tolist(),
        "source_block_temporarily_gravity_disabled": not args.natural_source_gravity,
        "source_platform_size_m": list(SOURCE_PLATFORM_SIZE) if args.natural_source_gravity else None,
        "gravity_enabled_after_gripper_close": True,
        "target_platform_position_m": target_platform_position.tolist(),
        "target_platform_size_m": list(target_platform_size),
        "target_support_mode": args.target_support_mode,
        "target_platform_quaternion_wxyz": (
            list(target_platform_orientation) if target_platform_orientation is not None else None
        ),
        "target_platform_collision_enabled_after_transfer": (
            args.target_collision_enable_stage == "after_transfer"
        ),
        "target_collision_enable_stage": args.target_collision_enable_stage,
        "release_unassisted": args.unassisted_release,
        "place_descent": args.place_descent,
        "place_descent_distance_m": args.place_descent_distance_m if args.place_descent else None,
        "place_waypoint_steps": args.place_waypoint_steps if args.place_descent else None,
        "place_max_command_step_rad": place_max_command_step_rad,
        "place_ik_uses_base_rotation_symmetry": True,
        "pre_place_block_position_m": pre_place_position.detach().cpu().tolist(),
        "pre_place_link_6_position_m": pre_place_link_6_position.detach().cpu().tolist(),
        "place_actual_block_translation_m": (
            (pre_release_position - pre_place_position).detach().cpu().tolist()
            if args.place_descent
            else None
        ),
        "place_actual_link_6_position_m": (
            place_actual_link_6_position.detach().cpu().tolist()
            if place_actual_link_6_position is not None
            else None
        ),
        "place_commanded_link_6_position_m": (
            place_commanded_link_6_position.tolist()
            if place_commanded_link_6_position is not None
            else None
        ),
        "place_actual_link_translation_m": (
            (place_actual_link_6_position - pre_place_link_6_position).detach().cpu().tolist()
            if place_actual_link_6_position is not None
            else None
        ),
        "place_max_arm_joint_error_rad": (
            float(np.max(np.abs(place_actual_arm - place_waypoints[-1])))
            if place_actual_arm is not None
            else None
        ),
        "release_clearance_m": (
            args.release_clearance_m if args.unassisted_release and not args.place_descent else None
        ),
        "release_downward_speed_assist_m_s": 0.0 if args.unassisted_release else RELEASE_DOWNWARD_SPEED_M_S,
        "release_separation_assist_m": 0.0 if args.unassisted_release else args.release_separation_assist_m,
        "cartesian_retreat_distances_m": retreat_distances.tolist(),
        "cartesian_pregrasp_joint_position_rad": pregrasp_arm.tolist(),
        "settled_source_position_m": settled_source_np.tolist(),
        "settled_source_quaternion_wxyz": settled_source_quaternion.detach().cpu().tolist(),
        "closed_position_m": closed_np.tolist(),
        "lifted_position_m": lifted_np.tolist(),
        "pre_release_position_m": pre_release_np.tolist(),
        "released_position_m": released_np.tolist(),
        "final_position_m": final_np.tolist(),
        "source_to_target_xy_distance_m": source_to_target_distance,
        "block_lift_height_m": lift_height,
        "approach_max_arm_joint_error_rad": float(np.max(np.abs(actual_approach_arm - grasp_arm))),
        "approach_l2_midpoint_to_block_center_m": open_midpoint_to_block,
        "approach_l2_midpoint_world_m": open_midpoint_world.tolist(),
        "approach_l2_midpoint_minus_block_center_m": open_midpoint_minus_block.tolist(),
        "approach_pad_center_world_by_body_m": open_pad_center_world_by_body,
        "approach_pad_center_minus_block_by_body_m": open_pad_center_minus_block_by_body,
        "closed_pad_center_world_by_body_m": closed_pad_center_world_by_body,
        "closed_pad_center_minus_block_by_body_m": closed_pad_center_minus_block_by_body,
        "closed_l2_tip_gap_m": closed_l2_gap,
        "closed_gripper_joint_position_rad": closed_gripper_joint_position.detach().cpu().tolist(),
        "close_left_finger_contact_force_n": close_left_finger_contact_force_n,
        "close_right_finger_contact_force_n": close_right_finger_contact_force_n,
        "close_contact_force_by_body_n": close_contact_force_by_body_n,
        "close_current_contact_force_by_body_n": close_current_contact_force_by_body_n,
        "close_recent_mean_contact_force_by_body_n": close_recent_mean_contact_force_by_body_n,
        "close_current_contact_force_vector_by_body_n": close_current_contact_force_vector_by_body_n,
        "closed_link_6_position_m": closed_link_6_position.detach().cpu().tolist(),
        "lifted_link_6_position_m": lifted_link_6_position.detach().cpu().tolist(),
        "actual_lift_link_translation_m": actual_lift_link_translation.detach().cpu().tolist(),
        "lift_max_arm_joint_error_rad": float(np.max(np.abs(actual_lift_arm - lift_arm))),
        "lift_actual_arm_joint_position_rad": actual_lift_arm.tolist(),
        "lift_target_arm_joint_position_rad": lift_arm.tolist(),
        "final_target_xy_error_m": final_target_xy_error,
        "final_target_position_error_m": final_target_position_error,
        "post_release_drift_m": release_drift,
        "final_l2_tip_gap_m": final_l2_tip_gap,
        "final_gripper_joint_position_rad": robot.data.joint_pos[0, gripper_ids].detach().cpu().tolist(),
        "all_states_finite": all_states_finite,
        "criteria": {
            "source_to_target_xy_distance_m_gt": 0.12,
            "block_lift_height_m_gt": 0.02,
            "final_target_xy_error_m_lt": 0.05,
            "final_target_position_error_m_lt": 0.05,
            "post_release_drift_m_lt": 0.02,
            "final_gripper_joint_position_rad_lt": 0.12,
            "final_l2_tip_gap_m_gt": 0.06,
        },
        "limitation": "The collision pads and scripted waypoints still require physical calibration.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"RM65_PICK_PLACE_BASELINE={'PASS' if passed else 'FAIL'}", flush=True)
    return 0 if passed else 1


try:
    exit_code = main()
except BaseException:
    print("PICK_PLACE_STAGE=PYTHON_EXCEPTION", flush=True)
    traceback.print_exc()
    raise
finally:
    simulation_app.close(skip_cleanup=True)

raise SystemExit(exit_code)
