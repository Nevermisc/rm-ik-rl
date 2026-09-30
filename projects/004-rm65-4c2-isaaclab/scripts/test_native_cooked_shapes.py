from types import SimpleNamespace as S
import pytest
from audit_native_cooked_shapes import convex_record


def tetra():
    return S(vertices=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],indices=[0,1,2,0,1,3,0,2,3,1,2,3],
             polygons=[S(plane=[0,0,1,0],num_vertices=3,index_base=i) for i in (0,3,6,9)])


def test_convex_serialization():
    assert convex_record(tetra())['bounds_m']==[[0,0,0],[1,1,1]]


@pytest.mark.parametrize('bad',['vertex','index','slice','plane'])
def test_reject_corrupt_convex(bad):
    value=tetra()
    if bad=='vertex': value.vertices[0][0]=float('nan')
    elif bad=='index': value.indices[0]=4
    elif bad=='slice': value.polygons[0].index_base=12
    else: value.polygons[0].plane=[1,2]
    with pytest.raises(ValueError): convex_record(value)
