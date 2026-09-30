import xml.etree.ElementTree as E
import pytest
from restore_native_follower_limits import follower_limits


def source():
    root=E.Element('robot')
    for i in range(5):
        j=E.SubElement(root,'joint',name=f'f{i}',type='revolute')
        E.SubElement(j,'mimic',joint='tool_gripper_joint')
        E.SubElement(j,'limit',lower='0',upper='1')
    return root


def test_source_limits(): assert len(follower_limits(source()))==5


@pytest.mark.parametrize('bad',['count','reference','finite','coverage'])
def test_reject_bad_source(bad):
    root=source()
    if bad=='count': root.remove(root[0])
    elif bad=='reference': root[0].find('mimic').set('joint','unknown')
    elif bad=='finite': root[0].find('limit').set('upper','nan')
    else: root[0].find('limit').set('upper','.8')
    with pytest.raises(ValueError): follower_limits(root)
