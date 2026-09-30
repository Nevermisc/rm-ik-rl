import numpy as np
import pytest
from scipy.spatial import ConvexHull
from audit_native_collision_fidelity import triangle_intersections,convex_sat


@pytest.mark.parametrize('other,count',[
    ([[.1,.1,0],[.4,.1,0],[.1,.4,0]],1),
    ([[2,2,0],[3,2,0],[2,3,0]],0),
    ([[.1,.1,-1],[.1,.1,1],[.4,.1,0]],1),
    ([[0,0,.01],[1,0,.01],[0,1,.01]],0)])
def test_triangle_sat(other,count):
    a=np.array([[[0,0,0],[1,0,0],[0,1,0]]])
    assert triangle_intersections(a,np.array([other]))['surface_intersecting_triangle_pairs']==count


def cube():
    vertices=np.array([[x,y,z] for x in (0,1) for y in (0,1) for z in (0,1)],float)
    hull=ConvexHull(vertices)
    return dict(vertices=vertices.tolist(),indices=hull.simplices.ravel().tolist(),polygons=[dict(index_base=i*3,num_vertices=3,plane=e.tolist()) for i,e in enumerate(hull.equations)])


@pytest.mark.parametrize('offset,expected',[(2,1),(.5,-.5),(1,0)])
def test_convex_gap(offset,expected):
    transform=np.eye(4); transform[0,3]=offset
    assert convex_sat(cube(),cube(),tb=transform)==pytest.approx(expected)
