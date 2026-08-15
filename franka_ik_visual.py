# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES.
# SPDX-License-Identifier: Apache-2.0

"""Visible traditional-IK demo for Isaac Sim.

The target cube follows a smooth 3D curve. At every simulation frame, the Lula
kinematics solver calculates Franka joint targets so that its end effector
follows the cube.
"""

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": False})

import math

import numpy as np
from isaacsim.core.api import World
from isaacsim.robot.manipulators.examples.franka import KinematicsSolver
from isaacsim.robot.manipulators.examples.franka.tasks import FollowTarget


world = World(stage_units_in_meters=1.0)
task = FollowTarget(name="follow_target_task")
world.add_task(task)
world.reset()

task_params = task.get_params()
robot_name = task_params["robot_name"]["value"]
target_name = task_params["target_name"]["value"]

robot = world.scene.get_object(robot_name)
target = world.scene.get_object(target_name)
ik_solver = KinematicsSolver(robot)
articulation_controller = robot.get_articulation_controller()

frame = 0
success_count = 0
attempt_count = 0
reset_needed = False

print("[DEMO] Visible traditional IK demo started.", flush=True)
print("[DEMO] The cube moves automatically; Franka should follow it.", flush=True)

while simulation_app.is_running():
    world.step(render=True)

    if world.is_stopped() and not reset_needed:
        reset_needed = True

    if not world.is_playing():
        continue

    if reset_needed:
        world.reset()
        reset_needed = False
        frame = 0

    t = frame / 120.0
    target_position = np.array(
        [
            0.50 + 0.10 * math.cos(t),
            0.10 * math.sin(t),
            0.50 + 0.06 * math.sin(2.0 * t),
        ]
    )
    target.set_world_pose(position=target_position)

    observations = world.get_observations()
    actions, success = ik_solver.compute_inverse_kinematics(
        target_position=observations[target_name]["position"],
        target_orientation=observations[target_name]["orientation"],
    )

    attempt_count += 1
    if success:
        success_count += 1
        articulation_controller.apply_action(actions)

    if frame % 120 == 0:
        print(
            f"[DEMO] frame={frame}, IK successes={success_count}/{attempt_count}",
            flush=True,
        )

    frame += 1

simulation_app.close()
