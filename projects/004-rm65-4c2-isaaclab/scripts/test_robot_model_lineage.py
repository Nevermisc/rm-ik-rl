import xml.etree.ElementTree as ET
import numpy as np
from audit_robot_model_lineage import differences,triangle_stats


def test_ignore_only_prefix_path_spelling_and_number_format():
    a=ET.fromstring('<joint name="x"><parent link="base_link"/><origin xyz="0 0 0"/><mesh filename="package://x/part.STL"/></joint>')
    b=ET.fromstring('<joint name="tool_x"><parent link="tool_base_link"/><origin xyz="0.0 0 0"/><mesh filename="file:///tmp/part.STL"/></joint>')
    assert differences(a,b,'tool_')==[]
    b.find('origin').set('xyz','0 0 .001')
    assert differences(a,b,'tool_')[0]['field']=='/origin[0]/@xyz'


def test_added_collision_not_hidden():
    a=ET.fromstring('<link name="x"><collision/></link>')
    b=ET.fromstring('<link name="tool_x"><collision/><collision name="pad"/></link>')
    assert any('collision[1]' in d['field'] for d in differences(a,b,'tool_'))


def test_tetrahedron_volume_centroid_and_closed_surface():
    a,b,c,d=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],dtype=float)
    result=triangle_stats(np.array([[a,c,b],[a,b,d],[a,d,c],[b,c,d]]).reshape(-1,3))
    assert np.isclose(result['signed_volume_m3'],1/6)
    assert np.allclose(result['uniform_density_surface_centroid_m'],[.25,.25,.25])
    assert result['non_two_manifold_edge_count']==0
    assert result['inconsistent_edge_winding_count']==0
