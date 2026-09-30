import numpy as np
import pytest
from audit_native_aperture import inner_face_patch,NativeFK
import xml.etree.ElementTree as ET


def test_inner_surface_area_and_centroid():
    triangles=np.array([[[0,.02,0],[.01,.02,0],[.01,.02,.01]],[[0,.02,0],[.01,.02,.01],[0,.02,.01]]])
    face=inner_face_patch(triangles,1)
    assert face['area_m2']==pytest.approx(.0001)
    assert face['centroid_link6_m']==pytest.approx([.005,.02,.005])


@pytest.mark.parametrize('points',[[],np.zeros((2,3,3)),np.full((2,3,3),np.nan)])
def test_rejects_missing_or_degenerate_face(points):
    with pytest.raises(ValueError):
        inner_face_patch(points,1)


def test_fk_master_and_axis_direction():
    root=ET.fromstring('<robot><joint name="tool_gripper_joint" type="revolute"><parent link="link_6"/><child link="tool_r_1"/><axis xyz="0 0 -1"/></joint></robot>')
    result=NativeFK(root).frame('tool_r_1',.5)
    assert result[0,1]==pytest.approx(np.sin(.5))
    with pytest.raises(ValueError,match='limits'):
        NativeFK(root).frame('tool_r_1',.9)


def test_fk_cycle_rejected():
    root=ET.fromstring('<robot><joint name="bad" type="fixed"><parent link="loop"/><child link="loop"/></joint></robot>')
    with pytest.raises(ValueError,match='terminate'):
        NativeFK(root).frame('loop',0.)
