import numpy as np
import pytest

from native_contact_geometry import points_to_triangles_distances, point_to_triangles_distance


def test_finite_face_edge_vertex_and_disconnected_faces():
    triangles=np.array([[[0,0,0],[1,0,0],[0,1,0]], [[3,0,0],[4,0,0],[3,1,0]]],dtype=float)
    points=np.array([[.2,.3,.7],[.5,-.3,.4],[-.3,-.4,0],[3.2,.3,.2],[2,0,0]])
    assert np.allclose(points_to_triangles_distances(points,triangles),[.7,.5,.5,.2,1.],atol=1e-14)


def test_rigid_transform_and_scalar_reference_agree():
    rng=np.random.default_rng(420051)
    triangles=rng.normal(size=(11,3,3))
    points=rng.normal(size=(251,3))
    expected=np.array([point_to_triangles_distance(point,triangles) for point in points])
    q,_=np.linalg.qr(rng.normal(size=(3,3))); shift=np.array([100,-20,40])
    actual=points_to_triangles_distances(points@q+shift,triangles@q+shift)
    assert np.allclose(actual,expected,rtol=1e-11,atol=1e-13)


def test_empty_contacts_and_rejected_invalid_geometry():
    tri=np.array([[[0.,0,0],[1,0,0],[0,1,0]]])
    assert points_to_triangles_distances(np.empty((0,3)),tri).shape==(0,)
    with pytest.raises(ValueError): points_to_triangles_distances([[np.nan,0,0]],tri)
    with pytest.raises(ValueError): points_to_triangles_distances([1,2,3],tri)
    with pytest.raises(ValueError): points_to_triangles_distances([[0,0,0]],np.zeros((1,3,3)))
