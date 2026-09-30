import copy
import xml.etree.ElementTree as ET
import numpy as np
import pytest
from audit_imported_joint_frames import pose, compare_joint, expected_joints


def fixture(axis='0 0 1', quaternion='(1, 0, 0, 0)'):
    source = ET.fromstring(f'<joint name="j" type="revolute"><parent link="p"/><child link="c"/><origin xyz="0.1 0 0"/><axis xyz="{axis}"/><limit lower="0" upper="1"/></joint>')
    attrs = {'physics:localPos0':'(0.1, 0, 0)', 'physics:localPos1':'(0, 0, 0)',
             'physics:localRot0':quaternion, 'physics:localRot1':quaternion,
             'physics:lowerLimit':'0', 'physics:upperLimit':str(np.rad2deg(1)), 'physics:axis':'Z'}
    return source, dict(type='PhysicsRevoluteJoint', attributes=attrs,
        relationships={'physics:body0':['/r/p'], 'physics:body1':['/r/c']})


@pytest.mark.parametrize('axis,quat', [('0 0 1','(1, 0, 0, 0)'), ('0 0 -1','(0, 0, 1, 0)')])
def test_axis_can_be_encoded_by_two_local_quaternions(axis, quat):
    source, usd = fixture(axis, quat)
    assert compare_joint(source, usd, 1)['status'] == 'pass'


@pytest.mark.parametrize('kind', ['direction', 'parent', 'limit'])
def test_real_mismatch_rejected(kind):
    source, usd = fixture()
    if kind == 'direction':
        source.find('axis').set('xyz', '0 0 -1')
    elif kind == 'parent':
        usd['relationships']['physics:body0'] = ['/r/wrong']
    else:
        usd['attributes']['physics:upperLimit'] = '1'
    assert compare_joint(source, usd, 1)['status'] == 'fail'


def test_zero_quaternion_rejected():
    with pytest.raises(ValueError):
        pose('(0, 0, 0)', '(0, 0, 0, 0)')


def test_arm_only_excludes_mount_by_link_identity():
    joint, _ = fixture()
    mount = ET.fromstring('<joint name="rm65_to_4c2"><parent link="c"/><child link="tool_base_link"/></joint>')
    source = {'j': joint, 'rm65_to_4c2': mount}
    assert set(expected_joints(source, True)) == {'j'}
    assert set(expected_joints(source, False)) == set(source)
