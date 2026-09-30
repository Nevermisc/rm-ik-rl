import numpy as np
import pytest

from audit_native_collision_fidelity import convex_sat
from audit_native_external_cooked_geometry import box_hull, common_interior_witness, normal_ray_envelope


def test_disjoint_hulls_have_separating_axis_and_no_common_witness():
    hull=box_hull([.01,.01,.01]); transform=np.eye(4); transform[0,3]=.025
    assert convex_sat(hull,hull,transform,np.eye(4)) == pytest.approx(.005)
    assert not common_interior_witness(hull,transform,[.01,.01,.01])['feasible']


def test_known_cuboid_overlap_has_finite_common_interior_ball():
    hull=box_hull([.01,.01,.01]); transform=np.eye(4); transform[0,3]=.015
    assert convex_sat(hull,hull,transform,np.eye(4)) == pytest.approx(-.005)
    witness=common_interior_witness(hull,transform,[.01,.01,.01])
    assert witness['strict_common_interior']
    assert witness['radius_m'] == pytest.approx(.0025)


def test_tangency_is_not_strict_solid_overlap():
    hull=box_hull([.01,.01,.01]); transform=np.eye(4); transform[0,3]=.02
    witness=common_interior_witness(hull,transform,[.01,.01,.01])
    assert witness['feasible']
    assert not witness['strict_common_interior']
    assert witness['radius_m'] == pytest.approx(0.)


def test_normal_ray_distinguishes_recession_extension_and_absent_coverage():
    hull=box_hull([.01,.008,.01])
    points=np.array([[0.,.01,0.],[0.,.006,0.],[.02,.01,0.]])
    result=normal_ray_envelope(points,np.array([0.,1.,0.]),[hull])
    assert result[:2] == pytest.approx([-.002,.002])
    assert np.isnan(result[2])
