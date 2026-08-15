"""Load the generated RM65-B USD and verify its six-joint articulation."""

from pathlib import Path

from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": True})

import omni.timeline
import omni.usd
from isaacsim.core.prims import Articulation
from isaacsim.core.utils.stage import add_reference_to_stage


project_dir = Path(__file__).resolve().parent
usd_path = project_dir / "assets" / "RM65-B" / "RM65-B.usd"
prim_path = "/World/RM65_B"
expected_joint_names = [f"joint_{index}" for index in range(1, 7)]


def main() -> int:
    if not usd_path.is_file():
        print("[RESULT] FAIL: Run import_rm65.py before this verification.")
        return 1

    omni.usd.get_context().new_stage()
    add_reference_to_stage(usd_path=str(usd_path), prim_path=prim_path)

    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    for _ in range(5):
        simulation_app.update()

    robot = Articulation(prim_path)
    robot.initialize()

    if not robot.is_physics_handle_valid():
        print(f"[RESULT] FAIL: {prim_path} is not a valid articulation.")
        timeline.stop()
        return 1

    dof_names = list(robot.dof_names)
    dof_limits = robot.get_dof_limits()[0]
    joint_positions = robot.get_joint_positions()[0]

    print(f"[RM65] Articulation path: {prim_path}")
    print(f"[RM65] DOF count: {robot.num_dof}")
    print(f"[RM65] DOF names: {dof_names}")
    print(f"[RM65] Initial joint positions (rad): {joint_positions.tolist()}")
    print(f"[RM65] Joint limits (rad): {dof_limits.tolist()}")

    names_ok = dof_names == expected_joint_names
    count_ok = robot.num_dof == 6
    finite_limits = bool((dof_limits[:, 0] < dof_limits[:, 1]).all())

    timeline.stop()
    if names_ok and count_ok and finite_limits:
        print("[RESULT] PASS: RM65-B is a valid six-joint Isaac Sim articulation.")
        return 0

    print(f"[RM65] Checks: names={names_ok}, count={count_ok}, limits={finite_limits}")
    print("[RESULT] FAIL: The imported RM65-B articulation did not match expectations.")
    return 1


try:
    exit_code = main()
finally:
    simulation_app.close()

raise SystemExit(exit_code)
