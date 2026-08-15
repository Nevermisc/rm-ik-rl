# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES.
# SPDX-License-Identifier: Apache-2.0

"""Automatically verify Franka traditional IK without opening a GUI."""

from isaacsim import SimulationApp


print("[START] Creating Isaac Sim in headless mode", flush=True)
simulation_app = SimulationApp({"headless": True})
print("[OK] SimulationApp created", flush=True)

import carb
from isaacsim.core.api import World
from isaacsim.robot.manipulators.examples.franka import KinematicsSolver
from isaacsim.robot.manipulators.examples.franka.tasks import FollowTarget


print("[START] Creating world and Franka follow-target task", flush=True)
world = World(stage_units_in_meters=1.0)
task = FollowTarget(name="follow_target_task")
world.add_task(task)
world.reset()
print("[OK] World and Franka assets loaded", flush=True)

task_params = task.get_params()
robot_name = task_params["robot_name"]["value"]
target_name = task_params["target_name"]["value"]
robot = world.scene.get_object(robot_name)
ik_solver = KinematicsSolver(robot)
articulation_controller = robot.get_articulation_controller()
print("[OK] Traditional IK solver created", flush=True)

max_steps = 240
attempt_count = 0
success_count = 0

for step in range(max_steps):
    if not simulation_app.is_running():
        break

    world.step(render=False)
    if not world.is_playing():
        continue

    observations = world.get_observations()
    actions, success = ik_solver.compute_inverse_kinematics(
        target_position=observations[target_name]["position"],
        target_orientation=observations[target_name]["orientation"],
    )
    attempt_count += 1

    if success:
        success_count += 1
        articulation_controller.apply_action(actions)
    else:
        carb.log_warn("IK did not converge on this frame.")

    if (step + 1) % 60 == 0:
        print(
            f"[PROGRESS] frame={step + 1}, IK successes={success_count}/{attempt_count}",
            flush=True,
        )

result = "PASS" if attempt_count > 0 and success_count > 0 else "FAIL"
print(
    f"[RESULT] {result}: traditional IK succeeded "
    f"{success_count}/{attempt_count} times.",
    flush=True,
)

simulation_app.close()
