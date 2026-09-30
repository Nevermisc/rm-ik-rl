import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from audit_gripper_visual_collision import transformed
from audit_native_aperture import NativeFK, audit
from native_contact_geometry import (load_inner_triangles, point_to_triangles_distance,
                                     scene_geometry, _quaternion_wxyz)


TRIANGLE = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]])


@pytest.mark.parametrize('point,expected', [
    ([.2, .3, 0.], 0.), ([.2, .3, .4], .4), ([.2, .3, -.4], .4),
    ([.7, .7, 0.], .4 / np.sqrt(2)), ([-.3, .2, 0.], .3),
    ([-.3, -.4, 0.], .5), ([2., 0., 0.], 1.),
    ([.7, .7, .3], np.sqrt(.08 + .09)), ([.5, .5, 0.], 0.)])
def test_triangle_distance_face_edge_and_vertex(point, expected):
    assert point_to_triangles_distance(point, TRIANGLE) == pytest.approx(expected, abs=1e-13)


def test_distance_selects_closest_finite_triangle_and_is_rigid_invariant():
    triangles = np.concatenate([TRIANGLE + [0., 0., 2.], TRIANGLE])
    point = np.array([.2, .3, .1])
    rotation = np.array([[0., 0., -1.], [0., -1., 0.], [-1., 0., 0.]])
    offset = np.array([.7, -.2, .5])
    assert point_to_triangles_distance(point, triangles) == pytest.approx(.1)
    assert point_to_triangles_distance(point @ rotation.T + offset,
                                      triangles @ rotation.T + offset) == pytest.approx(.1)


@pytest.mark.parametrize('bad', [[], np.zeros((3, 3)), np.zeros((1, 3, 3)),
    np.array([[[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]]]),
    np.full((1, 3, 3), np.nan), np.full((1, 3, 3), np.inf)])
def test_rejects_invalid_or_degenerate_triangles(bad):
    with pytest.raises(ValueError):
        point_to_triangles_distance([0., 0., 0.], bad)


@pytest.mark.parametrize('bad', [[0., 0.], [np.nan, 0., 0.], [np.inf, 0., 0.]])
def test_rejects_invalid_point(bad):
    with pytest.raises(ValueError):
        point_to_triangles_distance(bad, TRIANGLE)


def test_loader_returns_source_link_local_faces(tmp_path):
    # Different local offsets make accidental flange-coordinate output visible.
    text = ['<robot><link name="link_6"/>']
    for name, offset, plane in [('tool_l_3', -.04, .01), ('tool_r_3', .04, -.01)]:
        mesh = tmp_path / (name + '.stl')
        mesh.write_text('solid test\nfacet normal 0 1 0\nouter loop\n' +
            '\n'.join(f'vertex {x} {plane} {z}' for x, z in [(0., 0.), (.02, 0.), (0., .03)]) +
            '\nendloop\nendfacet\nendsolid test\n')
        text.append(f'<link name="{name}"><visual><geometry><mesh filename="{mesh.name}"/>'
                    f'</geometry></visual></link><joint name="{name}_fixed" type="fixed">'
                    f'<parent link="link_6"/><child link="{name}"/><origin xyz=".1 {offset} .2"/>'
                    '</joint>')
    path = tmp_path / 'native.urdf'
    path.write_text(''.join(text) + '</robot>')
    local = load_inner_triangles(path)
    assert local['tool_l_3'][0, 0] == pytest.approx([0., .01, 0.])
    assert local['tool_r_3'][0, 0] == pytest.approx([0., -.01, 0.])
    assert point_to_triangles_distance([.005, .011, .005], local['tool_l_3']) == pytest.approx(.001)


@pytest.mark.parametrize('rotation', [np.eye(3), np.diag([1., -1., -1.]),
    np.diag([-1., 1., -1.]), np.diag([-1., -1., 1.]),
    np.array([[0., 0., -1.], [0., -1., 0.], [-1., 0., 0.]])])
def test_quaternion_handles_180_degree_horizontal_pose(rotation):
    w, x, y, z = _quaternion_wxyz(rotation)
    reconstructed = np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    assert np.allclose(reconstructed, rotation, atol=1e-14)


def test_actual_final_source_geometry_when_available():
    path = Path(os.environ.get('RM65_NATIVE_URDF',
        str(Path(__file__).resolve().parents[1] / 'generated/native_surface_source_limits_001/native.urdf')))
    if not path.exists():
        pytest.skip('actual source asset is retained on the laboratory host')
    local = load_inner_triangles(path)
    fk = NativeFK(ET.parse(path).getroot())
    reference = audit(path)
    assert reference['urdf_sha256'] == 'c362f677ee792a5475c293617b6241ca17566b4dbaf87237d459afe2d307ff74'
    for name, triangles in local.items():
        assert triangles.shape == (20, 3, 3)
        area = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0],
                                      triangles[:, 2] - triangles[:, 0]), axis=1).sum() / 2
        assert area == pytest.approx(reference['samples'][0]['faces'][name]['area_m2'])
        flange = transformed(triangles.reshape(-1, 3), fk.frame(name, 0.)).reshape(-1, 3, 3)
        assert point_to_triangles_distance(flange[0].mean(axis=0), flange) < 1e-12
    scene = scene_geometry(path)
    assert scene['object_center_world'] == pytest.approx([-.284002483, -.000000529, .806497914], abs=1e-8)
    assert np.asarray(scene['palm_rotation'])[:, 2] == pytest.approx([-1., 0., 0.], abs=1e-5)
    assert [s['gap_m'] for s in scene['face_samples']] == pytest.approx(
        [.06999986897486896, .045223665074470704, .016360229704343057, .0033533784963197914])
    with pytest.raises(ValueError, match='limits'):
        scene_geometry(path, arm_joints=[0., 0., 0., 0., 3., 0.])
