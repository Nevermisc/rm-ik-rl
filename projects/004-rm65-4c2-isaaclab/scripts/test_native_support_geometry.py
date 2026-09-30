import numpy as np
import pytest
from native_support_geometry import horizontal_section, gravity_projection_margin


def test_finite_triangle_section_and_no_intersection():
    triangles=np.array([[[0,0,-1],[2,0,1],[0,2,1]]],float)
    np.testing.assert_allclose(horizontal_section(triangles,0),[[0,1],[1,0]])
    assert horizontal_section(triangles,2).shape==(0,2)
    np.testing.assert_allclose(horizontal_section(triangles,-1),[[0,0]])


def test_signed_square_margin_inside_outside_corner():
    points=np.array([[0,0],[2,0],[2,2],[0,2]],float)
    assert gravity_projection_margin([1,1],points)['signed_margin_m']==pytest.approx(1.)
    assert gravity_projection_margin([3,3],points)['signed_margin_m']==pytest.approx(-2**.5)


def test_rank_deficient_support_is_not_area_support():
    result=gravity_projection_margin([.5,1],[[0,0],[1,0],[.2,0]])
    assert result['rank']==1 and result['signed_margin_m']==pytest.approx(-1.)
    assert not result['inside']
    assert gravity_projection_margin([2,0],[[1,0]])['signed_margin_m']==pytest.approx(-1.)


def test_coplanar_triangle_and_invalid_input():
    points=horizontal_section(np.array([[[0,0,0],[1,0,0],[0,1,0]]]),0)
    assert gravity_projection_margin([.2,.2],points)['signed_margin_m']==pytest.approx(.2)
    with pytest.raises(ValueError): horizontal_section(np.full((1,3,3),np.nan),0)
