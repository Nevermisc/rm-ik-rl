import numpy as np
import pytest
from audit_household_trajectory import analyze, rotated_half_extents


def fixture():
    phases = ['SOURCE_SETTLE','LIFT_HOLD','TRANSFER','OPEN','RELEASE_SETTLE','FINAL_SETTLE']
    poses = np.array([[0,0,.75,1,0,0,0],[0,0,.79,1,0,0,0],
                     [.2,0,.79,1,0,0,0],[.2,0,.66,1,0,0,0],
                     [.2,0,.66,1,0,0,0],[.2,0,.66,1,0,0,0]])
    actions = np.zeros((6,7))
    report = dict(status='pass', target_platform_position_m=[.2,0,.63], target_platform_size_m=[.2,.2,.04],
                  target_support_mode='wide_platform', final_gripper_joint_position_rad=[0]*6,
                  physics_contract={k:{'validation':{'status':'pass'}} for k in ('initial','final')})
    return poses, actions, phases, report, [.10,.02,.02]


def test_candidate_is_not_training_permission():
    result = analyze(*fixture())
    assert result['candidate_checks_passed']
    assert not result['training_ready']
    assert not result['formal_acceptance_passed']


def test_drop_before_target_is_rejected_even_if_endpoint_passes():
    args = fixture()
    args[0][2,2] = .66
    assert not analyze(*args)['candidate_checks_passed']


def test_preshape_is_not_full_release():
    args = fixture()
    args[1][3,6] = .7
    assert not analyze(*args)['candidate_checks_passed']


def test_edge_overhang_is_rejected():
    args = fixture()
    args[0][-1,0] = .28
    assert not analyze(*args)['candidate_checks_passed']


def test_invalid_quaternion():
    with pytest.raises(ValueError): rotated_half_extents([1,1,1], [0,0,0,0])


def test_rotation_is_object_aware():
    np.testing.assert_allclose(rotated_half_extents([.1,.02,.02],[2**-.5,0,0,2**-.5]), [.01,.05,.01])


@pytest.mark.parametrize('joints', [[0,0,float('nan'),0,0,0], [0]*5])
def test_invalid_final_joint_feedback(joints):
    args = fixture()
    args[3]['final_gripper_joint_position_rad'] = joints
    with pytest.raises(ValueError): analyze(*args)


def test_negative_large_joint_position_is_not_open():
    args = fixture()
    args[3]['final_gripper_joint_position_rad'][3] = -.8
    assert not analyze(*args)['candidate_checks_passed']


def test_reordered_phases_are_rejected():
    args = fixture()
    args[2][1], args[2][2] = args[2][2], args[2][1]
    assert not analyze(*args)['checks']['required_phases_in_order']


def test_invalid_normalized_command_is_not_release():
    args = fixture()
    args[1][3,6] = -.1
    with pytest.raises(ValueError): analyze(*args)
