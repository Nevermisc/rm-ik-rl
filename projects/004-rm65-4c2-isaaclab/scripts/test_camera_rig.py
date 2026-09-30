import ast
import copy
import json
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpi_extension.camera_rig import camera_rotation, load_camera_rig

CONFIG = Path(__file__).resolve().parents[1] / 'config/household_camera_rig_v1.json'


def test_camera_axes_are_rigid_right_handed_and_look_forward():
    record = load_camera_rig(CONFIG)
    wrist = record['config']['wrist']
    rotation = camera_rotation(wrist['forward_local'], wrist['up_local'])
    np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-12)
    assert np.linalg.det(rotation) == pytest.approx(1.)
    expected = np.array(wrist['forward_local'])
    expected /= np.linalg.norm(expected)
    np.testing.assert_allclose(rotation @ [0, 0, -1], expected)
    assert record['uses_object_pose_for_camera_initialization'] is False
    assert len(record['config_sha256']) == 64


def test_v2_configuration_is_distinct_and_fixed():
    v1 = load_camera_rig(CONFIG)
    v2 = load_camera_rig(CONFIG.with_name('household_camera_rig_v2.json'))
    assert v1['config_sha256'] != v2['config_sha256']
    assert v2['config']['rig_id'] == 'household_fixed_v2'
    assert not v2['uses_object_pose_for_camera_initialization']


@pytest.mark.parametrize('forward,up', [([0,0,0],[0,0,1]), ([0,0,1],[0,0,1]),
                                        ([0,0,1],[0,0,0]), ([1,float('nan'),0],[0,0,1])])
def test_invalid_axes(forward, up):
    with pytest.raises(ValueError): camera_rotation(forward, up)


@pytest.mark.parametrize('section,key,value', [('wrist','parent_link','Cube'),
    ('wrist','offset_local_m',[1,0,0]), ('optics','width',True),
    ('optics','clipping_range_m',[1,0]), ('optics','wrist_focal_length_mm',float('nan'))])
def test_invalid_rig(tmp_path, section, key, value):
    rig = copy.deepcopy(json.loads(CONFIG.read_text()))
    rig[section][key] = value
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(rig))
    with pytest.raises(ValueError): load_camera_rig(path)


def test_fixed_pose_method_never_accepts_or_reads_object_state():
    tree = ast.parse((Path(__file__).parent / 'run_pick_place_baseline.py').read_text())
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_set_fixed_wrist_pose')
    assert [a.arg for a in method.args.args] == ['self', 'tool_position', 'tool_quaternion']
    text = ast.unparse(method)
    assert 'cube' not in text and 'source_block' not in text and 'target_block' not in text
    assert 'set_world_poses(' in text and "convention='opengl'" in text
