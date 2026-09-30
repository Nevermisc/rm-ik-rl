import numpy as np
import pytest
from native_household_geometry import object_vertical_bounds, support_withdraw_offset


def test_actual_vertices_not_symmetric_half_height():
    points=np.array([[1.,0.,0.],[-2.,0.,0.],[0.,0.,0.]])
    # +90 degree about Y takes asymmetric local X extents to Z.
    lo,hi=object_vertical_bounds([0,0,4],[2**-.5,0,2**-.5,0],points)
    assert lo==pytest.approx(3.)
    assert hi==pytest.approx(6.)


def test_three_segment_fixture_clears_catch_before_deeper_drop():
    initial_bottom=.7060550547201251
    catch_top=.6464979136121074
    for f in np.linspace(0,1,1001):
        offset=support_withdraw_offset(f)
        if offset[0] <= .12+.015:
            assert initial_bottom+offset[2] > catch_top+.019
    assert support_withdraw_offset(1)==pytest.approx([.15,0,-.1])
    assert support_withdraw_offset(1/3)==pytest.approx([0,0,-.04])
    assert support_withdraw_offset(2/3)==pytest.approx([.15,0,-.04])


@pytest.mark.parametrize('f',[-.1,1.1,float('nan'),float('inf')])
def test_invalid_fixture_fraction(f):
    with pytest.raises(ValueError):support_withdraw_offset(f)
