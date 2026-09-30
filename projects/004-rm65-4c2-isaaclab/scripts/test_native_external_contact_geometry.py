import numpy as np
import pytest

from audit_native_external_contact_geometry import reconstruct_body_frame, triangle_box_evidence


def test_planar_noncollinear_pose_reconstructs_actual_rigid_transform():
    local = np.array([[0., 0., 0.], [.02, 0., 0.], [0., .03, 0.], [.02, .03, 0.]])
    rotation = np.array([[0., 0., -1.], [0., -1., 0.], [-1., 0., 0.]])
    translation = np.array([-.25, .65, .81])
    contacts = [dict(point_link_m=a.tolist(), point_world_m=b.tolist())
                for a, b in zip(local, local @ rotation.T + translation)]
    fit = reconstruct_body_frame(contacts)
    assert fit['valid']
    assert fit['centered_local_rank'] == 2
    assert np.allclose(fit['rotation_local_to_world'], rotation)
    assert fit['position_world_m'] == pytest.approx(translation)
    assert fit['max_residual_m'] < 1e-12


def test_collinear_correspondences_are_not_pose_evidence():
    contacts = [dict(point_link_m=[i, 0., 0.], point_world_m=[i+1, 2., 3.]) for i in range(4)]
    fit = reconstruct_body_frame(contacts)
    assert not fit['valid']
    assert fit['centered_local_rank'] == 1


def test_large_triangle_intersects_box_even_with_every_vertex_outside():
    triangles = np.array([[[-3., -3., 0.], [3., -3., 0.], [0., 3., 0.]]])
    evidence = triangle_box_evidence(triangles, [1., 1., 1.])
    assert evidence['strict_source_face_inside_object']
    assert evidence['source_face_area_in_closed_box_m2'] == pytest.approx(4.)
    assert evidence['max_interior_witness_margin_m'] == pytest.approx(1.)


def test_coplanar_touch_is_not_strict_interior():
    triangles = np.array([[[-3., -3., 1.], [3., -3., 1.], [0., 3., 1.]]])
    evidence = triangle_box_evidence(triangles, [1., 1., 1.])
    assert evidence['source_face_area_in_closed_box_m2'] == pytest.approx(4.)
    assert not evidence['strict_source_face_inside_object']


def test_finite_triangle_outside_box_does_not_count_infinite_plane():
    triangles = np.array([[[2., 2., 0.], [3., 2., 0.], [2., 3., 0.]]])
    evidence = triangle_box_evidence(triangles, [1., 1., 1.])
    assert evidence['intersecting_triangle_count'] == 0
    assert not evidence['strict_source_face_inside_object']
