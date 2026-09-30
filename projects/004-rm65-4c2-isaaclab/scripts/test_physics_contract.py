from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.physics_contract import validate_strict_options, validate_runtime_snapshot


def options():
    return SimpleNamespace(natural_source_gravity=True, enable_moving_gripper_gravity=True,
        unassisted_release=True, disable_arm_gravity_during_approach=False,
        disable_arm_gravity_through_transport=False, collision_bypass_during_approach=False,
        initialize_at_grasp=False, target_collision_enable_stage='initial')


def test_strict_options_pass():
    validate_strict_options(options())


@pytest.mark.parametrize('field,value', [('natural_source_gravity', False),
    ('enable_moving_gripper_gravity', False), ('unassisted_release', False),
    ('disable_arm_gravity_during_approach', True), ('disable_arm_gravity_through_transport', True),
    ('collision_bypass_during_approach', True), ('initialize_at_grasp', True),
    ('target_collision_enable_stage', 'after_transfer')])
def test_reject_assistance(field, value):
    args = options()
    setattr(args, field, value)
    with pytest.raises(ValueError):
        validate_strict_options(args)


def snapshot():
    return dict(gravity_m_s2=[0, 0, -9.81], rigid_bodies={'body': dict(gravity_disabled=False,
        rigid_body_enabled=True, kinematic_enabled=False)}, object_colliders={'mesh': True},
        object_runtime_masses_kg=[.066], stage_meters_per_unit=1., stage_up_axis='Z')


def test_runtime_pass_and_missing_body():
    assert validate_runtime_snapshot(snapshot(), {'body'}, .066)['status'] == 'pass'
    assert validate_runtime_snapshot(snapshot(), {'missing'}, .066)['status'] == 'fail'


@pytest.mark.parametrize('key,value', [('gravity_m_s2', [0,0,0]), ('gravity_m_s2', [0,0,float('nan')]),
    ('object_runtime_masses_kg', [.01]), ('object_runtime_masses_kg', []),
    ('stage_up_axis', 'Y'), ('stage_meters_per_unit', .01), ('object_colliders', {}),
    ('object_colliders', {'mesh': False})])
def test_runtime_reject(key, value):
    data = snapshot()
    data[key] = value
    assert validate_runtime_snapshot(data, {'body'}, .066)['status'] == 'fail'


@pytest.mark.parametrize('key,value', [('gravity_disabled', True), ('gravity_disabled', None),
    ('kinematic_enabled', True), ('rigid_body_enabled', False)])
def test_reject_body(key, value):
    data = deepcopy(snapshot())
    data['rigid_bodies']['body'][key] = value
    assert validate_runtime_snapshot(data, {'body'}, .066)['status'] == 'fail'
