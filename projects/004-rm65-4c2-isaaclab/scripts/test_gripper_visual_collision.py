import struct
import numpy as np
import pytest
from audit_gripper_visual_collision import aabb_separation, bounds, stl_vertices, transformed


def test_gap_is_positive_only_for_disjoint_bounds():
    a = np.array([[0,0,0],[1,1,1]])
    assert aabb_separation(a, a) == 0
    assert aabb_separation(a, a + [0,0,2]) == 1
    assert aabb_separation(a, a + [2,2,0]) == pytest.approx(2**.5)


def test_binary_stl(tmp_path):
    path = tmp_path / 'mesh.stl'
    path.write_bytes(bytes(80) + struct.pack('<I',1) + struct.pack('<12fH',0,0,1, 0,0,0, 1,0,0, 0,1,0, 0))
    np.testing.assert_allclose(stl_vertices(path), [[0,0,0],[1,0,0],[0,1,0]])


def test_ascii_stl_and_transform(tmp_path):
    path = tmp_path / 'mesh.stl'
    path.write_text('solid test\n vertex 0 0 0\n vertex 1 0 0\n vertex 0 1 0\nendsolid\n')
    frame = np.eye(4)
    frame[:3,3] = [2,3,4]
    np.testing.assert_allclose(bounds(transformed(stl_vertices(path), frame)), [[2,3,4],[3,4,4]])


def test_corrupt_stl_fails(tmp_path):
    path = tmp_path / 'invalid.stl'
    path.write_bytes(bytes(100))
    with pytest.raises(ValueError): stl_vertices(path)
