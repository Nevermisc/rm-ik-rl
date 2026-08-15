"""Visible RM65-B traditional IK demo for Isaac Sim 5.1.0 final.

The target cube follows a small Cartesian curve. Every frame, Lula solves the
full target pose and the result is sent to the RM65 articulation controller.
Close the Isaac Sim window to stop the program.
"""

from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": False})

import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import VisualCuboid
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils import viewports
from isaacsim.core.utils.rotations import rot_matrix_to_quat
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.robot_motion.motion_generation import (
    ArticulationKinematicsSolver,
    LulaKinematicsSolver,
)


project_dir = Path(__file__).resolve().parent
usd_path = project_dir / "assets" / "RM65-B" / "RM65-B.usd"
urdf_path = project_dir / "assets" / "RM65-B" / "urdf" / "RM65-B.urdf"
description_path = project_dir / "rm65_robot_description.yaml"
prim_path = "/World/RM65_B"
end_effector_frame = "link_6"


def main() -> None:
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()
    add_reference_to_stage(usd_path=str(usd_path), prim_path=prim_path)
    robot = world.scene.add(SingleArticulation(prim_path=prim_path, name="rm65"))

    lula_solver = LulaKinematicsSolver(
        robot_description_path=str(description_path),
        urdf_path=str(urdf_path),
    )
    articulation_ik = ArticulationKinematicsSolver(
        robot_articulation=robot,
        kinematics_solver=lula_solver,
        end_effector_frame_name=end_effector_frame,
    )

    center_q = np.array([0.2, -0.8, 1.15, 0.2, 0.65, -0.2])
    center_position, center_rotation = lula_solver.compute_forward_kinematics(
        end_effector_frame, center_q
    )
    target_orientation = rot_matrix_to_quat(center_rotation)
    target = world.scene.add(
        VisualCuboid(
            prim_path="/World/IK_Target",
            name="ik_target",
            position=center_position,
            orientation=target_orientation,
            scale=np.array([0.035, 0.035, 0.035]),
            color=np.array([1.0, 0.15, 0.05]),
        )
    )

    viewports.set_camera_view(
        eye=np.array([1.15, 1.15, 0.9]),
        target=np.array([0.0, 0.0, 0.4]),
    )
    world.reset()
    robot.set_joint_positions(np.array([0.0, -0.5, 1.0, 0.0, 0.5, 0.0]))
    controller = robot.get_articulation_controller()

    frame = 0
    success_count = 0
    while simulation_app.is_running():
        time_value = frame / 120.0
        target_position = center_position + np.array(
            [
                0.045 * np.sin(time_value),
                0.045 * np.cos(time_value),
                0.020 * np.sin(2.0 * time_value),
            ]
        )
        target.set_world_pose(position=target_position, orientation=target_orientation)

        action, success = articulation_ik.compute_inverse_kinematics(
            target_position=target_position,
            target_orientation=target_orientation,
        )
        if success:
            controller.apply_action(action)
            success_count += 1

        world.step(render=True)
        frame += 1
        if frame % 120 == 0:
            print(f"[RM65] IK success: {success_count}/{frame} frames")


try:
    main()
finally:
    simulation_app.close()
