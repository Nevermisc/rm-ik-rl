import numpy as np
import pytest

from household_grasp_calibration import PadGeometry, origin_transform, rotation


@pytest.fixture
def geometry(tmp_path):
    links = []
    for side, sign in (("r", -1), ("l", 1)):
        name = f"tool_{side}_2"
        links.append(f'''<link name="{name}"><collision name="contact_pad_box">
          <origin xyz="0.03 0 0"/><geometry><box size=".04 .014 .018"/></geometry>
          </collision></link><joint name="{name}_joint" type="revolute">
          <parent link="link_6"/><child link="{name}"/><origin xyz="0 {sign*.06} .12"/>
          <axis xyz="0 0 {-sign}"/><limit lower="0" upper="1"/></joint>''')
    path = tmp_path / 'fixture.urdf'
    path.write_text('<robot><link name="link_6"/>' + ''.join(links) + '</robot>')
    return PadGeometry(path)


def test_rotation():
    np.testing.assert_allclose(rotation([0, 0, 1], np.pi/2) @ [1, 0, 0], [0, 1, 0], atol=1e-12)


def test_zero_axis_rejected():
    with pytest.raises(ValueError):
        rotation([0, 0, 0], 0)


def test_empty_origin_identity():
    np.testing.assert_array_equal(origin_transform(None), np.eye(4))


def test_pad_geometry_at_open(geometry):
    center, closing, gap = geometry.pads(0)
    np.testing.assert_allclose(center, [.03, 0, .12])
    np.testing.assert_allclose(closing, [0, 1, 0])
    assert gap == pytest.approx(.106)


def test_width_fit(geometry):
    center, closing, evidence = geometry.fit_box(.065)
    assert abs(evidence['modeled_gap_m'] - .065) < .0003
    assert not evidence['collision_free_path_validated']
    assert len(evidence['urdf_sha256']) == 64


def test_impossible_width(geometry):
    with pytest.raises(ValueError, match='outside'):
        geometry.fit_box(.2)


def test_joint_limit(geometry):
    with pytest.raises(ValueError, match='limits'):
        geometry.pads(1.2)


def test_missing_chain(geometry):
    with pytest.raises(ValueError, match='chain'):
        geometry.transform('unknown', 0)


@pytest.mark.parametrize('width', [0, -1, float('nan')])
def test_invalid_width(geometry, width):
    with pytest.raises(ValueError):
        geometry.fit_box(width)
