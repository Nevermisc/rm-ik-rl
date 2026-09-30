import numpy as np
import pytest
from audit_native_linkage_closure import pivot_fit, cylinder_profiles
from household_grasp_calibration import rotation


def frames():
    a = np.tile(np.eye(4), (9, 1, 1))
    for frame, q in zip(a, np.linspace(0, 1, 9)):
        frame[:3, :3] = rotation([0, 0, 1], q)
    return a, np.tile(np.eye(4), (9, 1, 1))


def test_known_hinge_has_coincident_axis():
    a, b = frames()
    result = pivot_fit(a, b, [[-.1]*3, [.1]*3], [[-.1]*3, [.1]*3])
    assert result['plausible_kinematic_hinge']
    assert not result['collision_filter_authorized']


def test_pivot_outside_parts_not_admitted():
    a, b = frames()
    result = pivot_fit(a, b, [[1]*3, [2]*3], [[1]*3, [2]*3])
    assert not result['plausible_kinematic_hinge']


def test_rigid_pair_is_not_independent_hinge():
    a, _ = frames()
    assert not pivot_fit(a, a, [[-.1]*3, [.1]*3], [[-.1]*3, [.1]*3])['plausible_kinematic_hinge']


def test_motion_breaking_closure_is_detected():
    a, b = frames()
    b[:, 2, 3] = np.linspace(0, .02, len(b))
    assert pivot_fit(a, b, [[-.1]*3, [.1]*3], [[-.1]*3, [.1]*3])['max_pivot_coincidence_error_m'] > .001


def test_invalid_frames_rejected():
    with pytest.raises(ValueError):
        pivot_fit([], [], [[0]*3, [1]*3], [[0]*3, [1]*3])


@pytest.mark.parametrize('inside', [False, True])
def test_triangulated_cylinder_radius_and_hole_normal(inside):
    triangles = []
    for theta in np.linspace(0, 2*np.pi, 33)[:-1]:
        end = theta + 2*np.pi/32
        p = np.array([[.003*np.cos(theta), .003*np.sin(theta), 0],
                      [.003*np.cos(end), .003*np.sin(end), 0],
                      [.003*np.cos(end), .003*np.sin(end), .01],
                      [.003*np.cos(theta), .003*np.sin(theta), .01]])
        triangles.extend([p[[0,1,2]], p[[0,2,3]]])
    triangles = np.array(triangles)
    if inside:
        triangles = triangles[:, ::-1]
    profile = cylinder_profiles(triangles, [0,0,0], [0,0,1])[0]
    assert abs(profile['radius_m']-.003) < 1e-8
    assert profile['angular_coverage_deg'] > 340
    assert profile['interpretation'] == ('hole_candidate' if inside else 'pin_candidate')
