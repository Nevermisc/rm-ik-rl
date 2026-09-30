"""Keep standalone Isaac CLI integration tests out of CPU pytest discovery.

These remain available as explicit IsaacLab entry points with USD/URDF options;
importing them is not a unit test and would parse pytest's argv/start a simulator.
"""
collect_ignore = [
    'test_combined_ik.py',
    'test_gripper_aperture.py',
    'test_gripper_close_stability.py',
]
