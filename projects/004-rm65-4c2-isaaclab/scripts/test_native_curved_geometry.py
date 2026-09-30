import itertools
import numpy as np
import pytest
from native_curved_geometry import closest_source_surface,solid_winding_number,hull_from_vertices,closest_normal_ray_interval


def cube(center=(0.,0.,0.),half=1.):
    return hull_from_vertices(np.array(list(itertools.product((-half,half),repeat=3)))+center)


def test_surface_distance_finite_face_and_edge():
    triangle=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
    assert closest_source_surface([.2,.2,.4],triangle)['distance_m']==pytest.approx(.4)
    result=closest_source_surface([1.,1.,0.],triangle)
    assert result['distance_m']==pytest.approx(2**-.5)
    assert result['nearest_point']==pytest.approx([.5,.5,0.])


def test_closed_solid_winding_and_rigid_invariance():
    t=cube()['triangles']
    assert abs(solid_winding_number([0,0,0],t))==pytest.approx(1.)
    assert solid_winding_number([2,0,0],t)==pytest.approx(0.,abs=1e-12)
    R=np.array([[0.,-1,0],[1.,0,0],[0,0,1]])
    shift=np.array([3.,2.,1.]);moved=t@R.T+shift
    assert abs(solid_winding_number(shift,moved))==pytest.approx(1.)
    assert closest_source_surface(shift,moved)['distance_m']==pytest.approx(1.)


def test_vertex_hull_ray_protrusion_recession_and_miss():
    h=cube(half=1.)
    assert closest_normal_ray_interval([1.2,0,0],[1,0,0],[h])['outward_boundary_offset_m']==pytest.approx(-.2)
    assert closest_normal_ray_interval([.8,0,0],[1,0,0],[h])['outward_boundary_offset_m']==pytest.approx(.2)
    assert not closest_normal_ray_interval([0,2,0],[1,0,0],[h])['hit']


def test_ray_union_merges_overlapping_hulls_and_selects_nearest_component():
    a=cube();b=cube(center=(1.,0.,0.));far=cube(center=(10.,0.,0.))
    ray=closest_normal_ray_interval([.5,0,0],[1,0,0],[a,b,far])
    assert ray['source_point_in_hull_union']
    assert ray['outward_boundary_offset_m']==pytest.approx(1.5)
    assert len(ray['intervals'])==2
