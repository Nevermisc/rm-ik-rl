import math
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.object_placement import yaw_placement


def test_identity():
    result = yaw_placement([.02,.12,.02], 0)
    assert result['world_aabb_size_m'] == [.02,.12,.02]
    assert result['orientation_wxyz'] == [1,0,0,0]


def test_marker_rotation_is_not_scaling():
    result = yaw_placement([.019,.121,.0195], math.pi/2)
    assert result['world_aabb_size_m'] == pytest.approx([.121,.019,.0195])
    assert result['asset_scale'] == [1,1,1]
    assert sum(v*v for v in result['orientation_wxyz']) == pytest.approx(1.)
    assert not result['grasp_feasibility_validated']


@pytest.mark.parametrize('size,yaw', [([0,1,1],0), ([1,2],0), ([1,2,3],float('nan')), ([1,2,3],4)])
def test_invalid(size,yaw):
    with pytest.raises(ValueError): yaw_placement(size,yaw)
