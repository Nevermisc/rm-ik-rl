import copy
import xml.etree.ElementTree as ET
import pytest
from build_native_gripper_candidate import audit_native_source, build


@pytest.fixture
def native(tmp_path):
    mesh = tmp_path/'source.STL'
    mesh.write_bytes(b'synthetic signature fixture, not simulation geometry')
    robot = ET.Element('robot', name='test')
    names = ['base_link','r_1','r_2','r_3','l_1','l_2','l_3','r_2_base','l_2_base']
    for name in names:
        link = ET.SubElement(robot,'link',name='tool_'+name)
        for kind in ('visual','collision'):
            obj = ET.SubElement(link,kind)
            ET.SubElement(ET.SubElement(obj,'geometry'),'mesh',filename=mesh.as_uri())
        inertia = ET.SubElement(link,'inertial')
        ET.SubElement(inertia,'mass',value='.01')
        ET.SubElement(inertia,'inertia',ixx='.00001',iyy='.00001',izz='.00001',ixy='0',ixz='0',iyz='0')
    for name in ('gripper','r_3','l_1','l_3','r_2','l_2'):
        joint = ET.SubElement(robot,'joint',name='tool_'+name+'_joint',type='revolute')
        ET.SubElement(joint,'limit',lower='0',upper='.865' if name=='gripper' else '1')
        if name != 'gripper':
            ET.SubElement(joint,'mimic',joint='tool_gripper_joint',multiplier='1',offset='0')
    return robot


def test_native_source_contract(native):
    report = audit_native_source(native)
    assert len(report['links']) == 9
    assert len(report['followers']) == 5
    assert report['source_total_gripper_mass_kg'] == pytest.approx(.09)


def test_rejects_extra_pad(native):
    link = native.find('link')
    link.append(copy.deepcopy(link.find('collision')))
    with pytest.raises(ValueError,match='extra pads'):
        audit_native_source(native)


def test_rejects_displaced_collision(native):
    ET.SubElement(native.find('link/collision'),'origin',xyz='0 0 .065')
    with pytest.raises(ValueError,match='coincide'):
        audit_native_source(native)


@pytest.mark.parametrize('value',['.1 .1 .1','nan 1 1','1 1'])
def test_rejects_scaling(native,value):
    native.find('link/collision/geometry/mesh').set('scale',value)
    with pytest.raises(ValueError,match='unit scale'):
        audit_native_source(native)


@pytest.mark.parametrize('value',['0','nan','-1'])
def test_rejects_invalid_mass(native,value):
    native.find('link/inertial/mass').set('value',value)
    with pytest.raises(ValueError,match='mass/inertia'):
        audit_native_source(native)


def test_rejects_nonphysical_inertia(native):
    native.find('link/inertial/inertia').set('ixx','1')
    with pytest.raises(ValueError,match='mass/inertia'):
        audit_native_source(native)


def test_rejects_lost_mimic(native):
    joint = native.findall('joint')[1]
    joint.remove(joint.find('mimic'))
    with pytest.raises(ValueError,match='mimic'):
        audit_native_source(native)


def test_rejects_mimic_change(native):
    native.find('joint/mimic').set('multiplier','-1')
    with pytest.raises(ValueError,match='mimic'):
        audit_native_source(native)


def test_preserves_existing_candidate(tmp_path):
    with pytest.raises(ValueError,match='fresh'):
        build(None,None,None,None,tmp_path)
